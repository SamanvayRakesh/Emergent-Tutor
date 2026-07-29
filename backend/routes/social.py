"""Leaderboard, recommendations, referrals, streak reminders."""
import json
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, HTTPException, Query, Request

from core import db, openai_client, get_current_user, logger
from plan_gates import has_feature
from models import ReferralApplyRequest

router = APIRouter()


# ----- Leaderboard helpers -----
def _rank_entries(users: list, current_user_id: str = None) -> tuple[list, int, dict]:
    """Convert user docs to ranked leaderboard entries. Returns (entries, user_rank, current_user_entry)."""
    entries = []
    for i, u in enumerate(users):
        xp = u.get("xp", 0)
        entries.append({
            "rank": i + 1, "user_id": u["user_id"],
            "name": u.get("name", "Anonymous"),
            "xp": xp, "level": max(1, xp // 500 + 1),
            "streak": u.get("streak", 0),
            "class_level": u.get("class_level", "?"),
            "badge": "gold" if i == 0 else "silver" if i == 1 else "bronze" if i == 2 else None,
        })
    user_rank = None
    current_user_entry = None
    if current_user_id:
        for e in entries:
            if e["user_id"] == current_user_id:
                user_rank = e["rank"]
                current_user_entry = e
                break
    return entries, user_rank, current_user_entry


async def _friend_ids(user_id: str) -> set:
    """Bidirectional friends via referral graph (you referred them OR they referred you)."""
    friends = set()
    async for ref in db.referrals.find({"referrer_id": user_id}, {"_id": 0, "referred_id": 1}):
        friends.add(ref["referred_id"])
    async for ref in db.referrals.find({"referred_id": user_id}, {"_id": 0, "referrer_id": 1}):
        friends.add(ref["referrer_id"])
    return friends


# ----- Leaderboard endpoint -----
@router.get("/leaderboard")
async def get_leaderboard(request: Request, scope: str = Query("global", regex="^(global|class|friends)$")):
    """Leaderboard with scope: global (all), class (same class_level), friends (referral graph + self)."""
    current_user = None
    try:
        current_user = await get_current_user(request)
    except Exception:
        pass

    # Base filter: exclude admin accounts, internal test accounts, and hidden users
    base_filter = {
        "role": {"$ne": "admin"},
        "email": {"$not": {"$regex": "^test_.*@neuralearn\\.ai"}},
        "hide_from_leaderboard": {"$ne": True},
    }

    if scope == "class":
        if not current_user:
            raise HTTPException(status_code=401, detail="Sign in to view your class leaderboard")
        query = {**base_filter, "class_level": current_user.get("class_level", "9")}
    elif scope == "friends":
        if not current_user:
            raise HTTPException(status_code=401, detail="Sign in to view your friends leaderboard")
        friends = await _friend_ids(current_user["user_id"])
        friends.add(current_user["user_id"])  # include self
        query = {**base_filter, "user_id": {"$in": list(friends)}}
    else:
        query = base_filter

    users = await db.users.find(
        query, {"_id": 0, "user_id": 1, "name": 1, "xp": 1, "streak": 1, "class_level": 1}
    ).sort("xp", -1).limit(50).to_list(50)

    cur_id = current_user["user_id"] if current_user else None
    entries, user_rank, current_user_entry = _rank_entries(users, cur_id)

    # Plan gate: free users see top 10 only
    full_access = True
    if current_user:
        full_access = await has_feature(current_user["user_id"], "leaderboard_full")
    limit = 20 if full_access else 10

    return {
        "scope": scope,
        "leaderboard": entries[:limit],
        "user_rank": user_rank,
        "current_user": current_user_entry,
        "total_users": len(users),
        "class_level": current_user.get("class_level") if scope == "class" and current_user else None,
        "leaderboard_locked_beyond": limit if not full_access else None,
    }


# ----- Recommendations -----
@router.get("/recommendations")
async def get_recommendations(request: Request):
    user = await get_current_user(request)
    progress = await db.progress.find({"user_id": user["user_id"]}, {"_id": 0}).to_list(50)
    recent_sessions = await db.chat_sessions.find({"user_id": user["user_id"]}, {"_id": 0}).sort("updated_at", -1).limit(3).to_list(3)
    quiz_results = await db.quizzes.find({"user_id": user["user_id"], "completed": True}, {"_id": 0}).sort("created_at", -1).limit(3).to_list(3)

    recs = []
    if recent_sessions:
        s = recent_sessions[0]
        recs.append({
            "type": "resume", "icon": "play",
            "title": f"Continue: {s['chapter']}",
            "description": f"Pick up where you left off in {s['subject']}",
            "action": "chat", "data": {"session_id": s["session_id"]},
        })

    weak = [p for p in progress if p.get("mastery", 100) < 50]
    if weak:
        w = weak[0]
        recs.append({
            "type": "revision", "icon": "refresh",
            "title": f"Revise: {w['chapter_name']}",
            "description": f"Only {w.get('mastery', 0)}% mastery — quick revision will boost your confidence!",
            "action": "chat",
            "data": {
                "subject": w.get("subject"), "chapter_id": w.get("chapter_id"),
                "chapter": w.get("chapter_name"), "class_level": w.get("class_level"),
            },
        })

    low_quiz = [q for q in quiz_results if q.get("score", 100) < 70]
    if low_quiz:
        q = low_quiz[0]
        recs.append({
            "type": "practice", "icon": "target",
            "title": f"Practice: {q.get('topic', 'Quiz topic')}",
            "description": f"Scored {q.get('score', 0)}% — let's improve it with focused practice!",
            "action": "quiz",
        })

    recs.append({
        "type": "mock_exam", "icon": "trophy",
        "title": "Take a Mock Exam",
        "description": "Challenge yourself with a CBSE-pattern timed examination",
        "action": "mock_exam",
    })
    recs.append({
        "type": "explore", "icon": "book",
        "title": "Explore New Chapter",
        "description": "Browse the full CBSE syllabus and start something new",
        "action": "syllabus",
    })
    return {"recommendations": recs[:4]}


# ----- Streak Reminder -----
def _hours_since_active(last_active_str: str) -> float:
    if not last_active_str:
        return 999.0
    try:
        la = datetime.fromisoformat(last_active_str)
        if la.tzinfo is None:
            la = la.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - la).total_seconds() / 3600.0
    except Exception:
        return 999.0


@router.get("/streak-reminder")
async def get_streak_reminder(request: Request):
    """Returns the user's current streak state + an AI-personalized motivational nudge if at risk."""
    user = await get_current_user(request)
    streak = user.get("streak", 0)
    longest_streak = user.get("longest_streak", streak)
    hours = _hours_since_active(user.get("last_active", ""))
    active_today = hours < 24
    # "at risk" = active yesterday but not yet today (24-48h gap)
    at_risk = (not active_today) and hours < 48 and streak > 0
    # "broken" = >48h
    broken = hours >= 48 and streak > 0

    # Get a quick context for the AI message
    weak_topics = []
    plan = await db.study_plans.find_one({"user_id": user["user_id"]}, {"_id": 0, "subjects": 1, "exam_date": 1})
    days_to_exam = None
    if plan and plan.get("exam_date"):
        try:
            exam_dt = datetime.fromisoformat(plan["exam_date"].replace("Z", "+00:00"))
            days_to_exam = max(0, (exam_dt.replace(tzinfo=None) - datetime.now()).days)
        except Exception:
            pass

    last_mock = await db.mock_exams.find_one({"user_id": user["user_id"], "completed": True}, {"_id": 0, "weak_topics": 1}, sort=[("completed_at", -1)])
    if last_mock and last_mock.get("weak_topics"):
        weak_topics = last_mock["weak_topics"][:3]

    # Generate message
    message = None
    cta = None
    if active_today:
        message = f"You're on fire 🔥 — {streak}-day streak locked in for today!" if streak >= 2 else "Welcome back — let's start today's mission."
        cta = "Keep going"
    elif broken:
        message = f"Your {streak}-day streak slipped. No worries — every champion restarts. One quick win brings it back."
        cta = "Restart streak"
    elif at_risk:
        # AI-personalized only when at risk
        ctx_lines = [f"Student name: {user.get('name', 'Student')}", f"Current streak: {streak} days", f"Longest streak: {longest_streak} days"]
        if days_to_exam is not None:
            ctx_lines.append(f"Exam in: {days_to_exam} days")
        if weak_topics:
            ctx_lines.append(f"Recent weak topics: {', '.join(weak_topics)}")
        prompt = (
            "You are a warm, hype CBSE study coach. Write ONE punchy reminder (max 22 words) to a student "
            "who's about to break their learning streak today. Be specific, motivational, mention their streak number, "
            "and reference exam-day urgency or a weak topic if available. NO emoji-spam (max 1 emoji). "
            "Return JSON: {\"message\":\"...\", \"cta\":\"2-3 word button label\"}\n\n"
            "Context:\n" + "\n".join(ctx_lines)
        )
        try:
            resp = await openai_client.chat.completions.create(
                model="deepseek/deepseek-v4-flash", messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}, temperature=0.9, max_tokens=120,
            )
            data = json.loads(resp.choices[0].message.content)
            message = data.get("message", f"Don't break your {streak}-day streak! 5 minutes is all it takes.")
            cta = data.get("cta", "Keep streak")
        except Exception as e:
            logger.warning(f"streak-reminder AI failed: {e}")
            message = f"Don't break your {streak}-day streak! 5 minutes of learning is all it takes."
            cta = "Keep streak"
    else:
        # no streak / first-time user
        message = "Start your first learning streak today — even 5 minutes counts."
        cta = "Begin"

    return {
        "streak": streak,
        "longest_streak": longest_streak,
        "hours_since_active": round(hours, 1),
        "active_today": active_today,
        "at_risk": at_risk,
        "broken": broken,
        "days_to_exam": days_to_exam,
        "message": message,
        "cta": cta,
    }


# ----- Referral -----
@router.get("/referral/code")
async def get_referral_code(request: Request):
    user = await get_current_user(request)
    code = user.get("referral_code")
    if not code:
        code = user["user_id"][-6:].upper()
        await db.users.update_one({"user_id": user["user_id"]}, {"$set": {"referral_code": code}})
    count = await db.referrals.count_documents({"referrer_id": user["user_id"]})
    return {"code": code, "referral_count": count, "xp_per_referral": 150, "referred_xp": 100}


@router.post("/referral/apply")
async def apply_referral(body: ReferralApplyRequest, request: Request):
    user = await get_current_user(request)
    code = body.code.upper().strip()
    if await db.referrals.find_one({"referred_id": user["user_id"]}):
        raise HTTPException(status_code=400, detail="You've already used a referral code")
    referrer = await db.users.find_one({"referral_code": code}, {"_id": 0})
    if not referrer:
        raise HTTPException(status_code=404, detail="Invalid referral code")
    if referrer["user_id"] == user["user_id"]:
        raise HTTPException(status_code=400, detail="Can't use your own code")

    await db.users.update_one({"user_id": user["user_id"]}, {"$inc": {"xp": 100}})
    await db.users.update_one({"user_id": referrer["user_id"]}, {"$inc": {"xp": 150}})
    await db.referrals.insert_one({
        "referrer_id": referrer["user_id"],
        "referred_id": user["user_id"],
        "applied_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"message": "Referral applied! You earned 100 XP!", "xp_earned": 100}

