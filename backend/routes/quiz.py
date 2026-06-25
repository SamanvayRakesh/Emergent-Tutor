"""Quiz generation + submission + gamification stats."""
import uuid
import json
import random
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from core import db, openai_client, get_current_user
from plan_gates import check_limit, increment_usage
from credits import deduct_credits
from models import QuizGenerateRequest, QuizSubmitRequest
from adaptive_engine import record_quiz_result, update_topic_performance

router = APIRouter()


@router.post("/quiz/generate")
async def generate_quiz(body: QuizGenerateRequest, request: Request):
    user = await get_current_user(request)
    # Grade lock
    if body.class_level != user.get("class_level"):
        raise HTTPException(status_code=403, detail="Quizzes must match your active grade.")
    # Daily quiz limit
    allowed, info = await check_limit(user["user_id"], "quiz")
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail={
                "code": "DAILY_LIMIT_REACHED", "feature": "quiz",
                "message": f"You've used all {info['limit']} quizzes on the Free plan today.",
                "limit_info": info, "upgrade_to": "pro",
            },
        )

    # Credit gate: deduct 5 credits per quiz
    await deduct_credits(user["user_id"], "quiz_generate")

    prompt = f"""Generate exactly {body.num_questions} multiple-choice questions for CBSE Class {body.class_level} {body.subject} on the topic: "{body.topic}".

Difficulty level: {body.difficulty}

Return ONLY a JSON object with this structure:
{{
  "title": "Quiz: {body.topic}",
  "subject": "{body.subject}",
  "class_level": "{body.class_level}",
  "questions": [
    {{
      "question": "...",
      "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
      "correct": "A",
      "explanation": "Brief explanation why the answer is correct"
    }}
  ]
}}

Make questions test conceptual understanding, not just memorization. Include a brief explanation for each answer."""

    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert CBSE question paper setter. Generate clear, educational MCQ questions."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7, max_tokens=2000,
        )
        quiz_data = json.loads(response.choices[0].message.content)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI generation failed: {e}")

    quiz_id = f"quiz_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    quiz_doc = {
        "quiz_id": quiz_id, "user_id": user["user_id"],
        "class_level": body.class_level, "subject": body.subject,
        "topic": body.topic, "difficulty": body.difficulty,
        "questions": quiz_data.get("questions", []),
        "title": quiz_data.get("title", f"Quiz: {body.topic}"),
        "completed": False, "score": None, "created_at": now,
    }
    await db.quizzes.insert_one(quiz_doc)
    await increment_usage(user["user_id"], "quizzes", 1)
    quiz_doc.pop("_id", None)
    return quiz_doc


@router.get("/quiz/history")
async def get_quiz_history(request: Request):
    user = await get_current_user(request)
    return await db.quizzes.find({"user_id": user["user_id"]}, {"_id": 0}).sort("created_at", -1).limit(20).to_list(20)


@router.get("/quiz/topic-mastery")
async def get_topic_mastery(topic: str, request: Request):
    """Return adaptive difficulty recommendation for a topic based on quiz history."""
    user = await get_current_user(request)
    profile = await db.student_profiles.find_one({"user_id": user["user_id"]}, {"_id": 0, "topics": 1})
    if not profile:
        return {"topic": topic, "mastery": 0.5, "recommended_difficulty": "medium", "attempts": 0}
    data = profile.get("topics", {}).get(topic, {})
    mastery = data.get("mastery", 0.5)
    attempts = data.get("attempts", 0)
    if mastery < 0.4:
        difficulty = "easy"
    elif mastery < 0.7:
        difficulty = "medium"
    else:
        difficulty = "hard"
    return {
        "topic": topic,
        "mastery": round(mastery, 2),
        "mastery_pct": int(mastery * 100),
        "recommended_difficulty": difficulty,
        "attempts": attempts,
    }


@router.post("/quiz/{quiz_id}/submit")
async def submit_quiz(quiz_id: str, body: QuizSubmitRequest, request: Request):
    user = await get_current_user(request)
    quiz = await db.quizzes.find_one({"quiz_id": quiz_id, "user_id": user["user_id"]}, {"_id": 0})
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    questions = quiz.get("questions", [])
    correct_count = 0
    results = []
    for i, q in enumerate(questions):
        ua = body.answers.get(str(i))
        is_correct = ua == q.get("correct")
        if is_correct:
            correct_count += 1
        results.append({
            "question": q["question"], "user_answer": ua,
            "correct_answer": q.get("correct"),
            "is_correct": is_correct, "explanation": q.get("explanation", ""),
        })

    total = len(questions)
    score_pct = int((correct_count / total * 100)) if total > 0 else 0
    xp_earned = correct_count * 20

    await db.quizzes.update_one(
        {"quiz_id": quiz_id},
        {"$set": {"completed": True, "score": score_pct, "correct_count": correct_count,
                  "total_questions": total, "completed_at": datetime.now(timezone.utc).isoformat()}},
    )
    await db.users.update_one({"user_id": user["user_id"]}, {"$inc": {"xp": xp_earned}})

    # Feed quiz result into adaptive engine (per-question tracking)
    await record_quiz_result(user["user_id"], quiz.get("topic", "General"), score_pct, correct_count, total)
    for i, q in enumerate(questions):
        ua = body.answers.get(str(i))
        is_correct = ua == q.get("correct")
        topic_label = q.get("topic") or quiz.get("topic") or quiz.get("chapter") or "General"
        await update_topic_performance(user["user_id"], topic_label, is_correct)

    return {"score": score_pct, "correct_count": correct_count, "total_questions": total,
            "xp_earned": xp_earned, "results": results}


@router.get("/gamification/stats")
async def get_gamification_stats(request: Request):
    user = await get_current_user(request)
    xp = user.get("xp", 0)
    level = max(1, xp // 500 + 1)
    xp_in_level = xp % 500

    session_count = await db.chat_sessions.count_documents({"user_id": user["user_id"]})
    quiz_count = await db.quizzes.count_documents({"user_id": user["user_id"], "completed": True})
    chapters_studied = await db.progress.count_documents({"user_id": user["user_id"]})

    achievements = []
    if session_count >= 1:
        achievements.append({"id": "first_chat", "name": "First Steps", "description": "Started your first AI chat", "icon": "star", "color": "#22d3ee"})
    if session_count >= 10:
        achievements.append({"id": "chat_10", "name": "Curious Mind", "description": "Completed 10 AI chat sessions", "icon": "brain", "color": "#8b5cf6"})
    if quiz_count >= 1:
        achievements.append({"id": "first_quiz", "name": "Quiz Starter", "description": "Completed your first quiz", "icon": "target", "color": "#10b981"})
    if quiz_count >= 5:
        achievements.append({"id": "quiz_5", "name": "Quiz Master", "description": "Completed 5 quizzes", "icon": "trophy", "color": "#f59e0b"})
    if xp >= 100:
        achievements.append({"id": "xp_100", "name": "Rising Star", "description": "Earned 100 XP", "icon": "zap", "color": "#d946ef"})
    if user.get("streak", 0) >= 3:
        achievements.append({"id": "streak_3", "name": "On Fire!", "description": "3-day learning streak", "icon": "flame", "color": "#ef4444"})

    daily_topics = ["Photosynthesis", "Newton's Laws", "Quadratic Equations", "Periodic Table", "French Revolution", "Python Lists"]
    random.seed(datetime.now().date().toordinal())
    daily_topic = random.choice(daily_topics)

    return {
        "xp": xp, "level": level, "xp_in_level": xp_in_level, "xp_to_next": 500 - xp_in_level,
        "streak": user.get("streak", 0), "longest_streak": user.get("longest_streak", 0),
        "achievements": achievements,
        "session_count": session_count, "quiz_count": quiz_count, "chapters_studied": chapters_studied,
        "daily_challenge": {"topic": daily_topic, "subject": "Mixed", "xp_reward": 50},
    }
