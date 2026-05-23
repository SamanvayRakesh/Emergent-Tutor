"""Leaderboard, recommendations, referrals."""
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from core import db, get_current_user
from models import ReferralApplyRequest

router = APIRouter()


# ----- Leaderboard -----
@router.get("/leaderboard")
async def get_leaderboard(request: Request):
    users = await db.users.find(
        {}, {"_id": 0, "user_id": 1, "name": 1, "xp": 1, "streak": 1, "class_level": 1}
    ).sort("xp", -1).limit(50).to_list(50)

    leaderboard = []
    for i, u in enumerate(users):
        xp = u.get("xp", 0)
        leaderboard.append({
            "rank": i + 1, "user_id": u["user_id"],
            "name": u.get("name", "Anonymous"),
            "xp": xp, "level": max(1, xp // 500 + 1),
            "streak": u.get("streak", 0),
            "class_level": u.get("class_level", "?"),
            "badge": "gold" if i == 0 else "silver" if i == 1 else "bronze" if i == 2 else None,
        })

    user_rank = None
    current_user_entry = None
    try:
        user = await get_current_user(request)
        for entry in leaderboard:
            if entry["user_id"] == user["user_id"]:
                user_rank = entry["rank"]
                current_user_entry = entry
                break
    except Exception:
        pass

    return {
        "leaderboard": leaderboard[:20], "user_rank": user_rank,
        "current_user": current_user_entry, "total_users": len(users),
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
