"""Study plan: AI-generated weekly plan personalised with quiz history + weak areas."""
import json
from collections import Counter
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from core import db, openai_client, get_current_user
from models import StudyPlanRequest

router = APIRouter()


# ── Helper: build student context ────────────────────────────────────────────

async def _build_student_context(user_id: str) -> dict:
    """Gather quiz history, mock exam results, weak/strong topics for one user."""
    # Quiz history (last 30 completed)
    quizzes = await db.quizzes.find(
        {"user_id": user_id, "completed": True},
        {"_id": 0, "topic": 1, "subject": 1, "score": 1, "difficulty": 1, "chapter": 1}
    ).sort("created_at", -1).limit(30).to_list(30)

    # Mock exam results (last 10)
    exams = await db.mock_exams.find(
        {"user_id": user_id, "completed": True},
        {"_id": 0, "weak_topics": 1, "subject": 1, "score": 1, "title": 1}
    ).sort("completed_at", -1).limit(10).to_list(10)

    # Student adaptive profile
    profile = await db.student_profiles.find_one(
        {"user_id": user_id},
        {"_id": 0, "weak_topics": 1, "topics": 1}
    ) or {}

    # ── Derive weak topics ────────────────────────────────────────────────────
    all_weak: list[str] = []
    # From persistent profile
    all_weak.extend(profile.get("weak_topics", []))
    # From exam results
    for e in exams:
        all_weak.extend(e.get("weak_topics", []))
    # From quizzes with score < 60
    for q in quizzes:
        if q.get("score", 100) < 60 and q.get("topic"):
            all_weak.append(q["topic"])

    weak_freq = Counter(all_weak).most_common(10)

    # ── Derive strong topics (mastery > 0.70, ≥ 2 attempts) ──────────────────
    strong: list[str] = []
    for topic, data in profile.get("topics", {}).items():
        if data.get("mastery", 0) >= 0.70 and data.get("attempts", 0) >= 2:
            strong.append(f"{topic} ({int(data['mastery'] * 100)}%)")

    # ── Recent quiz performance summary ──────────────────────────────────────
    quiz_summary_lines: list[str] = []
    for q in quizzes[:8]:
        line = f"  • {q.get('subject','?')} / {q.get('topic','?')}: {q.get('score',0)}% ({q.get('difficulty','medium')})"
        quiz_summary_lines.append(line)

    # ── Subject coverage from quizzes ────────────────────────────────────────
    subject_scores: dict[str, list[int]] = {}
    for q in quizzes:
        subj = q.get("subject", "")
        if subj:
            subject_scores.setdefault(subj, []).append(q.get("score", 0))
    subject_avg = {s: int(sum(v) / len(v)) for s, v in subject_scores.items()}

    return {
        "quiz_count": len(quizzes),
        "exam_count": len(exams),
        "weak_topics": [{"topic": t, "frequency": f} for t, f in weak_freq],
        "strong_topics": strong[:6],
        "quiz_summary": quiz_summary_lines,
        "subject_avg": subject_avg,
        "has_history": len(quizzes) > 0 or len(exams) > 0,
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/study-plan/context")
async def get_plan_context(request: Request):
    """Return student's learning context preview (used by frontend before generation)."""
    user = await get_current_user(request)
    ctx = await _build_student_context(user["user_id"])
    return ctx


@router.post("/study-plan")
async def create_study_plan(body: StudyPlanRequest, request: Request):
    user = await get_current_user(request)

    # Days until exam
    try:
        exam_dt = datetime.fromisoformat(body.exam_date.replace("Z", "+00:00"))
        if exam_dt.tzinfo is None:
            exam_dt = exam_dt.replace(tzinfo=timezone.utc)
        days_until = max(1, (exam_dt - datetime.now(timezone.utc)).days)
    except Exception:
        days_until = 30

    weeks = max(1, min(days_until // 7, 12))
    subjects_str = ", ".join(body.subjects) if body.subjects else "All CBSE subjects"

    # ── Pull student context ──────────────────────────────────────────────────
    ctx = await _build_student_context(user["user_id"])

    # Build context block for prompt
    context_block = ""
    if ctx["has_history"]:
        weak_str = ", ".join(t["topic"] for t in ctx["weak_topics"]) if ctx["weak_topics"] else "None identified yet"
        strong_str = ", ".join(ctx["strong_topics"]) if ctx["strong_topics"] else "None identified yet"
        subj_perf = "; ".join(f"{s}: {a}% avg" for s, a in ctx["subject_avg"].items()) if ctx["subject_avg"] else "No quiz data"
        quiz_lines = "\n".join(ctx["quiz_summary"][:6]) if ctx["quiz_summary"] else "  None yet"

        context_block = f"""
PERSONALISED STUDENT DATA ({ctx['quiz_count']} quizzes, {ctx['exam_count']} mock exams analysed):
- WEAK TOPICS requiring urgent focus: {weak_str}
- STRONG TOPICS (skip or briefly revise): {strong_str}
- Subject performance averages: {subj_perf}
- Recent quiz details:
{quiz_lines}

CRITICAL INSTRUCTION: Allocate 60-70% of study time to the WEAK TOPICS listed above.
For strong topics, only include light revision in the final week.
"""
    else:
        context_block = "\nNo quiz/exam history yet — generate a balanced plan covering all subjects equally.\n"

    available_str = ", ".join(body.available_days) if body.available_days else "Mon-Sun"
    session_str = body.session_preference.title()

    prompt = f"""You are an expert CBSE study planner. Create a highly personalised study plan.

STUDENT PROFILE:
- Class: {body.class_level}
- Days until exam: {days_until} ({weeks} weeks)
- Target score: {body.target_score}%
- Daily study hours: {body.daily_hours}h
- Subjects: {subjects_str}
- Available days: {available_str}
- Study session preference: {session_str}
{context_block}
INSTRUCTIONS:
1. Create exactly {weeks} week(s) of the plan
2. Each week must have realistic daily tasks for {available_str} only
3. Session times should match {session_str} preference
4. Prioritise WEAK TOPICS throughout
5. Include CBSE board exam patterns (MCQ + short answer + long answer)
6. Be specific: name exact chapters, not just subjects

Return ONLY valid JSON (no markdown, no backticks):
{{
  "overview": "2-3 sentence personalised strategy mentioning specific weak areas",
  "weeks": [
    {{
      "week": 1,
      "theme": "Foundation / Weak Area Blitz / etc.",
      "focus": ["Chapter Name (Subject)", "..."],
      "daily_tasks": [
        {{"day": "Mon", "subject": "...", "topic": "specific chapter/topic", "hours": 1.5, "type": "learn|revise|practice|test", "session": "{session_str.lower()}"}}
      ],
      "goal": "specific measurable goal for the week"
    }}
  ],
  "weak_area_strategy": "specific advice for the identified weak topics",
  "exam_week": "final week strategy",
  "tips": ["personalised tip 1 referencing weak areas", "tip 2", "tip 3"]
}}"""

    try:
        response = await openai_client.chat.completions.create(
            model="deepseek/deepseek-v4-flash",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=3000,
        )
        plan_data = json.loads(response.choices[0].message.content)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Study plan generation failed: {e}")

    now = datetime.now(timezone.utc).isoformat()
    await db.study_plans.update_one(
        {"user_id": user["user_id"]},
        {"$set": {
            "user_id": user["user_id"],
            "exam_date": body.exam_date,
            "target_score": body.target_score,
            "daily_hours": body.daily_hours,
            "class_level": body.class_level,
            "subjects": body.subjects,
            "available_days": body.available_days,
            "session_preference": body.session_preference,
            "plan": plan_data,
            "context_used": {
                "quiz_count": ctx["quiz_count"],
                "exam_count": ctx["exam_count"],
                "weak_topics": [t["topic"] for t in ctx["weak_topics"]],
                "strong_topics": ctx["strong_topics"],
            },
            "updated_at": now,
        }},
        upsert=True,
    )
    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {"exam_date": body.exam_date, "target_score": body.target_score}},
    )

    return {
        "plan": plan_data,
        "days_until_exam": days_until,
        "exam_date": body.exam_date,
        "target_score": body.target_score,
        "daily_hours": body.daily_hours,
        "context_used": {
            "quiz_count": ctx["quiz_count"],
            "exam_count": ctx["exam_count"],
            "weak_topics": [t["topic"] for t in ctx["weak_topics"]],
            "personalised": ctx["has_history"],
        },
    }


@router.get("/study-plan")
async def get_study_plan(request: Request):
    user = await get_current_user(request)
    plan = await db.study_plans.find_one({"user_id": user["user_id"]}, {"_id": 0})
    if not plan:
        return {"plan": None}
    if plan.get("exam_date"):
        try:
            exam_dt = datetime.fromisoformat(plan["exam_date"].replace("Z", "+00:00"))
            if exam_dt.tzinfo is None:
                exam_dt = exam_dt.replace(tzinfo=timezone.utc)
            plan["days_remaining"] = max(0, (exam_dt - datetime.now(timezone.utc)).days)
        except Exception:
            pass
    return plan
