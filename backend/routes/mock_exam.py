"""Mock Exam: generate, history, submit, follow-up quiz on weak topics."""
import uuid
import json
import asyncio
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, HTTPException, Request

from core import db, openai_client, get_current_user, logger
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from plan_gates import check_limit, increment_usage, has_feature
from credits import deduct_credits
from models import MockExamRequest, QuizSubmitRequest
from school_curriculum import get_school_chapters, has_school_curriculum

router = APIRouter()


EXAM_COST = 30
JOB_LEASE_SECONDS = 150
JOB_DEADLINE_SECONDS = 360
_generation_tasks = set()


def _public_job(job):
    if not job:
        return None
    public = {k: v for k, v in job.items() if k not in {
        "_id", "generation_request", "generation_parts", "lease_token", "lease_until",
        "generation_attempts", "generation_phase",
    }}
    if job.get("generation_status") == "generating":
        public["generation_progress"] = max(job.get("generation_progress", 0), min(90, job.get("sections_completed", 0) * 30))
    return public


def _section_counts(total):
    a = total // 2
    b = total // 4
    return [a, b, total - a - b]


@router.post("/mock-exam/generate", status_code=202)
async def generate_mock_exam(body: MockExamRequest, request: Request):
    user = await get_current_user(request)
    if body.class_level != user.get("class_level"):
        raise HTTPException(status_code=403, detail="Mock exams must match your active grade.")
    if body.num_questions not in (10, 15, 20, 30) or not 10 <= body.duration_minutes <= 180:
        raise HTTPException(status_code=400, detail="Choose 10, 15, 20 or 30 questions and a duration from 10 to 180 minutes.")
    existing = await db.mock_exams.find_one({"user_id": user["user_id"], "generation_status": "generating"}, {"_id": 0})
    if existing:
        return {**_public_job(existing), "status": "generating"}
    allowed, info = await check_limit(user["user_id"], "mock_exam")
    if not allowed:
        raise HTTPException(status_code=429, detail={
            "code": "WEEKLY_LIMIT_REACHED", "feature": "mock_exam",
            "message": "You've reached your mock-exam limit. Upgrade to continue.",
            "limit_info": info, "upgrade_to": "pro",
        })
    if user.get("credits", 0) < EXAM_COST:
        raise HTTPException(status_code=402, detail={
            "code": "INSUFFICIENT_CREDITS", "feature": "mock_exam_generate",
            "message": "Not enough credits for a mock exam (30 credits).", "upgrade_to": "pro",
            "required": EXAM_COST, "current": user.get("credits", 0),
        })
    school = user.get("school", "")
    if has_school_curriculum(school, body.class_level):
        chapters = get_school_chapters(school, body.class_level, body.subject)
        if not chapters:
            raise HTTPException(status_code=400, detail="Choose a subject from your school's syllabus.")
        names = {c["name"] for c in chapters}
        selected = body.chapters or ([body.chapter] if body.chapter else [])
        if len(selected) > 7 or any(c not in names for c in selected):
            raise HTTPException(status_code=400, detail="Choose up to seven chapters from your school's syllabus.")
    now = datetime.now(timezone.utc)
    job = {
        "exam_id": f"exam_{uuid.uuid4().hex[:12]}", "user_id": user["user_id"],
        "school": school, "class_level": body.class_level, "subject": body.subject,
        "duration_minutes": body.duration_minutes,
        "title": f"{body.subject} Mock Exam", "sections": [], "completed": False, "score": None,
        "created_at": now.isoformat(), "started_at": now.isoformat(),
        "deadline_at": (now + timedelta(seconds=JOB_DEADLINE_SECONDS)).isoformat(),
        "generation_status": "generating", "generation_phase": "queued",
        "generation_message": "Your exam is queued.", "sections_completed": 0,
        "generation_progress": 0, "estimated_seconds": 60,
        "generation_request": body.model_dump() if hasattr(body, "model_dump") else body.dict(),
    }
    try:
        await db.mock_exams.insert_one(job)
    except DuplicateKeyError:
        existing = await db.mock_exams.find_one({"user_id": user["user_id"], "generation_status": "generating"})
        if not existing:
            raise
        return {**_public_job(existing), "status": "generating"}
    return {**_public_job(job), "status": "generating"}


@router.get("/mock-exam/jobs/active")
async def active_mock_exam_job(request: Request):
    user = await get_current_user(request)
    job = await db.mock_exams.find_one(
        {"user_id": user["user_id"], "generation_status": {"$in": ["generating", "ready"]}, "completed": False}, {"_id": 0},
        sort=[("created_at", -1)],
    )
    return {"job": _public_job(job)}


@router.get("/mock-exam/jobs/{exam_id}")
async def mock_exam_job(exam_id: str, request: Request):
    user = await get_current_user(request)
    job = await db.mock_exams.find_one({"exam_id": exam_id, "user_id": user["user_id"]}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Mock exam not found")
    return {"job": _public_job(job)}


def _validate_section(raw, letter, count, marks):
    questions = raw.get("questions") if isinstance(raw, dict) else None
    if not isinstance(questions, list) or len(questions) != count:
        raise ValueError("Incorrect number of exam questions")
    clean = []
    for index, q in enumerate(questions, 1):
        if not isinstance(q, dict) or not isinstance(q.get("question"), str) or not q["question"].strip():
            raise ValueError("Missing exam question")
        options = q.get("options")
        correct = str(q.get("correct", "")).strip().upper()
        if len(correct) > 1 and correct[1:2] in (".", ")", ":"):
            correct = correct[0]
        if not isinstance(options, list) or len(options) != 4 or correct not in "ABCD" or len(correct) != 1:
            raise ValueError("Invalid multiple choice answers")
        normalized = []
        for i, option in enumerate(options):
            if not isinstance(option, str) or not option.strip():
                raise ValueError("Empty answer option")
            text = option.strip()
            if len(text) > 2 and text[0].upper() == "ABCD"[i] and text[1] in ".):":
                text = text[2:].strip()
            if not text:
                raise ValueError("Empty answer option")
            normalized.append(f"{'ABCD'[i]}. {text}")
        clean.append({**q, "id": f"{letter}{index}", "options": normalized, "correct": correct, "marks": marks})
    titles = {"A": "Multiple Choice Questions", "B": "Short Answer (MCQ Format)", "C": "Application Based Questions"}
    return {"section": letter, "title": titles[letter], "marks_per_question": marks, "questions": clean}


async def _generate_exam_sections(job, owned):
    body = MockExamRequest(**job["generation_request"])
    user = {"school": job.get("school", "")}
    # Resolve chapters — multi-chapter takes priority over single-chapter legacy field
    selected_chapters: list[str] = body.chapters[:7] if body.chapters else (
        [body.chapter] if body.chapter else []
    )

    # Build school context for BNPS / NIOS students
    school = user.get("school", "")
    school_context = ""
    if school and has_school_curriculum(school, body.class_level):
        all_chapters = get_school_chapters(school, body.class_level, body.subject)
        ch_names = [c["name"] for c in all_chapters]
        scope_str = (
            f"Focus ONLY on these chapter(s): {', '.join(selected_chapters)}."
            if selected_chapters else
            f"Cover all chapters: {', '.join(ch_names)}."
        )
        if school == "nios":
            school_context = (
                f"\nCURRICULUM: NIOS Secondary (National Institute of Open Schooling).\n"
                f"Generate questions STRICTLY from the NIOS Secondary syllabus for {body.subject}. "
                + scope_str
                + "\nDo NOT use CBSE/NCERT content."
            )
        else:
            school_context = (
                f"\nSCHOOL: Brooklyn National Public School (BNPS) — Grade {body.class_level}.\n"
                f"Generate questions STRICTLY from the BNPS syllabus. " + scope_str
                + "\nDo NOT use NCERT default chapters or generic CBSE content."
            )
    elif selected_chapters:
        school_context = f"\nFocus ONLY on these chapter(s): {', '.join(selected_chapters)}. All questions must be from these chapters."

    exam_label = "NIOS Secondary Course" if school == "nios" else f"Grade {body.class_level}"
    chapter_label = f" — {', '.join(selected_chapters[:3])}{'…' if len(selected_chapters) > 3 else ''}" if selected_chapters else ""
    exam_title_default = f"{'NIOS Secondary Course' if school == 'nios' else f'Class {body.class_level}'} {body.subject}{chapter_label} Mock Exam"


    counts = _section_counts(body.num_questions)
    async def build(index):
        letter = "ABC"[index]
        marks = index + 1
        cached = job.get("generation_parts", {}).get(letter)
        if cached:
            return _validate_section(cached, letter, counts[index], marks)
        prompt = f"""Create exactly {counts[index]} {exam_label} {body.subject} MCQs for section {letter}.
{school_context}
Difficulty: {['easy', 'medium', 'hard'][index]}. Each question carries {marks} mark(s).
Return JSON only: {{"questions":[{{"question":"...","options":["A. ...","B. ...","C. ...","D. ..."],"correct":"A","topic":"chapter/topic","explanation":"One short sentence."}}]}}
Keep wording concise, answers unambiguous and all questions distinct."""
        for attempt in range(2):
            try:
                response = await asyncio.wait_for(openai_client.chat.completions.create(
                    model="deepseek/deepseek-v4-flash", messages=[
                        {"role": "system", "content": "Expert question paper setter. Follow only the specified school's curriculum. Return valid JSON."},
                        {"role": "user", "content": prompt},
                    ], response_format={"type": "json_object"}, temperature=0.6,
                    max_tokens=min(4800, counts[index] * 230 + 400),
                    extra_body={"include_reasoning": False},
                ), timeout=45)
                section = _validate_section(json.loads(response.choices[0].message.content), letter, counts[index], marks)
                updated = await db.mock_exams.update_one(owned, {
                    "$set": {f"generation_parts.{letter}": section},
                    "$inc": {"sections_completed": 1},
                })
                if not updated.modified_count:
                    raise RuntimeError("Exam job ownership changed")
                return section
            except (asyncio.TimeoutError, ValueError, IndexError, TypeError):
                if attempt:
                    raise
        raise ValueError("Exam section generation failed")
    tasks = [asyncio.create_task(build(i)) for i in range(3)]
    try:
        sections = await asyncio.gather(*tasks)
        return sections, exam_title_default
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


async def _finish_exam_job(job):
    owned = {"exam_id": job["exam_id"], "generation_status": "generating", "lease_token": job["lease_token"]}
    try:
        if not job.get("sections"):
            if job.get("generation_attempts", 0) > 2 or job["deadline_at"] < datetime.now(timezone.utc).isoformat():
                raise asyncio.TimeoutError()
            sections, title = await asyncio.wait_for(_generate_exam_sections(job, owned), timeout=110)
            saved = await db.mock_exams.update_one(owned, {"$set": {
                "sections": sections, "title": title, "generation_phase": "settling",
                "generation_message": "Saving your exam.", "generation_progress": 95,
            }})
            if not saved.modified_count:
                return
        # The debit and its exam marker are written together in one atomic user update.
        # A recovered job can therefore finish without charging twice.
        debited = await db.users.find_one_and_update(
            {"user_id": job["user_id"], "credits": {"$gte": EXAM_COST},
             "mock_exam_debits": {"$ne": job["exam_id"]}},
            {"$inc": {"credits": -EXAM_COST}, "$addToSet": {"mock_exam_debits": job["exam_id"]}},
            return_document=ReturnDocument.AFTER, projection={"_id": 0, "credits": 1},
        )
        if not debited:
            previously_paid = await db.users.find_one({"user_id": job["user_id"], "mock_exam_debits": job["exam_id"]})
            if not previously_paid:
                await db.mock_exams.update_one(owned, {"$set": {
                    "generation_status": "error", "generation_message": "Your balance fell below 30 credits while the exam was generating. No credits were charged for this exam.",
                }})
                return
        await db.mock_exams.update_one(owned, {"$set": {
            "generation_status": "ready", "generation_phase": "complete",
            "generation_message": "Your exam is ready.", "generation_progress": 100,
            "ready_at": datetime.now(timezone.utc).isoformat(), "credits_used": EXAM_COST,
        }, "$unset": {"generation_parts": "", "lease_token": "", "lease_until": ""}})
        if debited:
            try:
                await increment_usage(job["user_id"], "mocks", 1)
                from credits import _record_credit_event
                await _record_credit_event(job["user_id"], "mock_exam_generate", EXAM_COST)
            except Exception:
                logger.exception("Mock exam usage counters failed")
    except asyncio.CancelledError:
        raise  # The lease expires, allowing the next worker to resume saved sections.
    except (asyncio.TimeoutError, ValueError, IndexError, TypeError):
        logger.exception("Mock exam generation failed: %s", job["exam_id"])
        await db.mock_exams.update_one(owned, {"$set": {
            "generation_status": "error", "generation_message": "The exam could not be generated in time or returned incomplete questions. No credits were charged. Please try again.",
        }})
    except Exception:
        # Leave the persisted job recoverable if saving or billing was interrupted.
        logger.exception("Mock exam job interrupted: %s", job["exam_id"])


async def mock_exam_generation_worker():
    """Claim persisted work with leases; continue independently of browser requests."""
    try:
        while True:
            try:
                _generation_tasks.difference_update(t for t in tuple(_generation_tasks) if t.done())
                if len(_generation_tasks) < 2:
                    now = datetime.now(timezone.utc)
                    job = await db.mock_exams.find_one_and_update(
                        {"generation_status": "generating", "$or": [
                            {"generation_phase": "queued"}, {"lease_until": {"$lt": now.isoformat()}},
                        ]},
                        {"$set": {"generation_phase": "working", "lease_token": uuid.uuid4().hex,
                                  "lease_until": (now + timedelta(seconds=JOB_LEASE_SECONDS)).isoformat(),
                                  "generation_message": "Building your exam sections."},
                         "$inc": {"generation_attempts": 1}},
                        sort=[("created_at", 1)], return_document=ReturnDocument.AFTER,
                    )
                    if job:
                        task = asyncio.create_task(_finish_exam_job(job))
                        _generation_tasks.add(task)
                        continue
                await asyncio.sleep(2)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Mock exam worker temporarily unavailable")
                await asyncio.sleep(5)
    finally:
        tasks = list(_generation_tasks)
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        _generation_tasks.clear()


@router.get("/mock-exam/history")
async def get_mock_exam_history(request: Request):
    user = await get_current_user(request)
    return await db.mock_exams.find(
        {"user_id": user["user_id"], "$or": [{"generation_status": "ready"}, {"generation_status": {"$exists": False}}]}, {"_id": 0, "sections": 0, "generation_request": 0}
    ).sort("created_at", -1).limit(10).to_list(10)


@router.post("/mock-exam/{exam_id}/submit")
async def submit_mock_exam(exam_id: str, body: QuizSubmitRequest, request: Request):
    user = await get_current_user(request)
    exam = await db.mock_exams.find_one({"exam_id": exam_id, "user_id": user["user_id"]}, {"_id": 0})
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    if exam.get("generation_status") in ("generating", "error"):
        raise HTTPException(status_code=409, detail="This exam is not ready to submit.")
    if exam.get("completed"):
        raise HTTPException(status_code=400, detail="This exam has already been submitted. Start a new exam to earn more XP.")

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
    # Level-up check
    if xp_earned > 0:
        updated = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0, "xp": 1, "level": 1})
        if updated:
            new_level = max(1, updated.get("xp", 0) // 500 + 1)
            if new_level > updated.get("level", 1):
                await db.users.update_one(
                    {"user_id": user["user_id"]}, {"$set": {"level": new_level}}
                )

    # Phase 7: Persist weak topics to student_profiles for cross-session recommendations
    if weak_unique:
        now_str = datetime.now(timezone.utc).isoformat()
        await db.student_profiles.update_one(
            {"user_id": user["user_id"]},
            {
                "$addToSet": {"weak_topics": {"$each": weak_unique}},
                "$set": {"updated_at": now_str},
            },
            upsert=True,
        )

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
            model="deepseek/deepseek-v4-flash",
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



@router.get("/weak-areas")
async def get_weak_areas(request: Request):
    """Return user's cumulative weak topics from exam history + student profile."""
    user = await get_current_user(request)
    uid = user["user_id"]

    # From student_profiles (persisted across all exams)
    profile = await db.student_profiles.find_one({"user_id": uid}, {"_id": 0, "weak_topics": 1, "topics": 1})
    profile_weak = profile.get("weak_topics", []) if profile else []

    # From recent 10 exams
    recent = await db.mock_exams.find(
        {"user_id": uid, "completed": True, "weak_topics": {"$exists": True, "$ne": []}},
        {"_id": 0, "weak_topics": 1, "subject": 1, "score": 1, "completed_at": 1},
    ).sort("completed_at", -1).limit(10).to_list(10)

    from collections import Counter
    exam_weak = [t for e in recent for t in e.get("weak_topics", [])]
    all_weak = profile_weak + exam_weak
    freq = Counter(all_weak).most_common(15)

    # Low-mastery topics from adaptive engine
    adaptive_weak = []
    if profile and profile.get("topics"):
        for topic, data in profile["topics"].items():
            if data.get("mastery", 1) < 0.45 and data.get("attempts", 0) >= 2:
                adaptive_weak.append({"topic": topic, "mastery": round(data["mastery"], 2)})
        adaptive_weak.sort(key=lambda x: x["mastery"])

    return {
        "weak_topics": [{"topic": t, "frequency": f} for t, f in freq],
        "adaptive_weak": adaptive_weak[:8],
        "exam_count": len(recent),
    }

