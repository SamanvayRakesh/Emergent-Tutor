"""Mock Exam: generate, history, submit, follow-up quiz on weak topics."""
import uuid
import json
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from core import db, openai_client, get_current_user
from plan_gates import check_limit, increment_usage, has_feature
from models import MockExamRequest, QuizSubmitRequest

router = APIRouter()


@router.post("/mock-exam/generate")
async def generate_mock_exam(body: MockExamRequest, request: Request):
    user = await get_current_user(request)
    # Grade lock
    if body.class_level != user.get("class_level"):
        raise HTTPException(status_code=403, detail="Mock exams must match your active grade. Change grade in Profile.")
    # Plan gate: weekly mock exam limit
    allowed, info = await check_limit(user["user_id"], "mock_exam")
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail={
                "code": "WEEKLY_LIMIT_REACHED", "feature": "mock_exam",
                "message": f"You've used your {info['limit']} mock exam(s) this week on the Free plan.",
                "limit_info": info, "upgrade_to": "pro",
            },
        )
    is_board = body.class_level in ["10", "12"]
    sec_a = max(4, body.num_questions // 2)
    sec_b = max(3, body.num_questions // 4)
    sec_c = body.num_questions - sec_a - sec_b

    prompt = f"""Generate a CBSE Class {body.class_level} {body.subject} mock exam paper with {body.num_questions} questions total.
Structure: Section A ({sec_a} MCQs, 1 mark each), Section B ({sec_b} questions, 2 marks each), Section C ({sec_c} questions, 3 marks each).
{"Focus on board exam patterns with HOTS questions." if is_board else "Cover fundamental concepts suitable for internal assessments."}

Return ONLY valid JSON:
{{
  "title": "Class {body.class_level} {body.subject} Mock Examination",
  "duration_minutes": {body.duration_minutes},
  "sections": [
    {{
      "section": "A", "title": "Multiple Choice Questions", "marks_per_question": 1,
      "questions": [{{"id":"A1","question":"...","options":["A. ...","B. ...","C. ...","D. ..."],"correct":"A","marks":1,"difficulty":"easy","topic":"...","explanation":"..."}}]
    }},
    {{
      "section": "B", "title": "Short Answer (MCQ Format)", "marks_per_question": 2,
      "questions": [{{"id":"B1","question":"...","options":["A. ...","B. ...","C. ...","D. ..."],"correct":"A","marks":2,"difficulty":"medium","topic":"...","explanation":"..."}}]
    }},
    {{
      "section": "C", "title": "Application Based Questions", "marks_per_question": 3,
      "questions": [{{"id":"C1","question":"...","options":["A. ...","B. ...","C. ...","D. ..."],"correct":"A","marks":3,"difficulty":"hard","topic":"...","explanation":"..."}}]
    }}
  ]
}}
Generate EXACTLY {sec_a} questions in Section A, {sec_b} in Section B, {sec_c} in Section C. Cover different chapters."""

    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Expert CBSE question paper setter."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"}, temperature=0.7, max_tokens=4000,
        )
        exam_data = json.loads(response.choices[0].message.content)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Mock exam generation failed: {e}")

    exam_id = f"exam_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    exam_doc = {
        "exam_id": exam_id, "user_id": user["user_id"],
        "class_level": body.class_level, "subject": body.subject,
        "duration_minutes": body.duration_minutes,
        "title": exam_data.get("title", f"Class {body.class_level} {body.subject} Mock Exam"),
        "sections": exam_data.get("sections", []),
        "completed": False, "score": None, "created_at": now,
    }
    await db.mock_exams.insert_one(exam_doc)
    await increment_usage(user["user_id"], "mocks", 1)
    exam_doc.pop("_id", None)
    return exam_doc


@router.get("/mock-exam/history")
async def get_mock_exam_history(request: Request):
    user = await get_current_user(request)
    return await db.mock_exams.find(
        {"user_id": user["user_id"]}, {"_id": 0, "sections": 0}
    ).sort("created_at", -1).limit(10).to_list(10)


@router.post("/mock-exam/{exam_id}/submit")
async def submit_mock_exam(exam_id: str, body: QuizSubmitRequest, request: Request):
    user = await get_current_user(request)
    exam = await db.mock_exams.find_one({"exam_id": exam_id, "user_id": user["user_id"]}, {"_id": 0})
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    total_marks = earned_marks = 0
    section_results = []
    weak_topics = []
    for section in exam.get("sections", []):
        s_earned = s_total = 0
        s_correct = s_questions = 0
        for q in section.get("questions", []):
            marks = q.get("marks", 1)
            s_total += marks; total_marks += marks; s_questions += 1
            if body.answers.get(q["id"]) == q.get("correct"):
                s_earned += marks; earned_marks += marks; s_correct += 1
            else:
                if q.get("topic"):
                    weak_topics.append(q["topic"])
        section_results.append({
            "section": section["section"], "title": section.get("title", ""),
            "correct": s_correct, "total": s_questions,
            "marks_earned": s_earned, "marks_total": s_total,
            "percentage": int(s_earned / s_total * 100) if s_total > 0 else 0,
        })

    score_pct = int(earned_marks / total_marks * 100) if total_marks > 0 else 0
    xp_earned = int(score_pct * 1.5)
    weak_unique = list(set(weak_topics))[:5]

    await db.mock_exams.update_one(
        {"exam_id": exam_id},
        {"$set": {"completed": True, "score": score_pct,
                  "earned_marks": earned_marks, "total_marks": total_marks,
                  "section_results": section_results,
                  "weak_topics": weak_unique,
                  "completed_at": datetime.now(timezone.utc).isoformat()}},
    )
    await db.users.update_one({"user_id": user["user_id"]}, {"$inc": {"xp": xp_earned}})

    return {
        "score": score_pct, "earned_marks": earned_marks, "total_marks": total_marks,
        "xp_earned": xp_earned, "section_results": section_results, "weak_topics": weak_unique,
    }


@router.post("/mock-exam/{exam_id}/followup-quiz")
async def mock_exam_followup_quiz(exam_id: str, request: Request):
    """Generate an adaptive 5-question quiz targeting the user's weak topics from this exam.
    Premium feature — requires Pro or Elite plan."""
    user = await get_current_user(request)
    if not await has_feature(user["user_id"], "adaptive_quizzes"):
        raise HTTPException(
            status_code=402,
            detail={
                "code": "PREMIUM_FEATURE", "feature": "adaptive_quizzes",
                "message": "Adaptive weak-topic quizzes are a Pro feature. Upgrade to unlock laser-focused practice on your weak spots.",
                "upgrade_to": "pro",
            },
        )
    exam = await db.mock_exams.find_one({"exam_id": exam_id, "user_id": user["user_id"]}, {"_id": 0})
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    if not exam.get("completed"):
        raise HTTPException(status_code=400, detail="Submit the exam before requesting a follow-up quiz")

    weak_topics = exam.get("weak_topics", []) or []
    if not weak_topics:
        raise HTTPException(status_code=400, detail="No weak topics — you nailed this exam! Try a harder mock instead.")

    topics_str = ", ".join(weak_topics)
    prompt = f"""Generate exactly 5 CBSE Class {exam['class_level']} {exam['subject']} MCQ questions focused EXCLUSIVELY on these weak topics where the student needs more practice: {topics_str}.

Make each question SHARPER and slightly more conceptual than typical board questions — the goal is to lock in mastery of these specific weak areas.

Return ONLY a JSON object:
{{
  "title": "Weak-Area Practice: {exam['subject']}",
  "subject": "{exam['subject']}",
  "class_level": "{exam['class_level']}",
  "topics": {json.dumps(weak_topics)},
  "questions": [
    {{"question":"...","options":["A. ...","B. ...","C. ...","D. ..."],"correct":"A","explanation":"Short, satisfying reason why...","topic":"matched weak topic"}}
  ]
}}
Vary difficulty: 2 medium, 2 hard, 1 application-based."""

    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Expert CBSE adaptive quiz generator. Laser-focused on specific weak topics."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"}, temperature=0.7, max_tokens=2000,
        )
        quiz_data = json.loads(response.choices[0].message.content)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI generation failed: {e}")

    quiz_id = f"quiz_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    quiz_doc = {
        "quiz_id": quiz_id, "user_id": user["user_id"],
        "class_level": exam['class_level'], "subject": exam['subject'],
        "topic": f"Follow-up: {topics_str}",
        "difficulty": "adaptive",
        "questions": quiz_data.get("questions", []),
        "title": quiz_data.get("title", "Weak-Area Practice"),
        "weak_topics": weak_topics,
        "source_exam_id": exam_id,
        "completed": False, "score": None, "created_at": now,
    }
    await db.quizzes.insert_one(quiz_doc)
    quiz_doc.pop("_id", None)
    return quiz_doc
