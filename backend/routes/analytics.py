"""Analytics routes — admin visibility into platform usage."""
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Request, HTTPException
from core import db, get_current_user

router = APIRouter()


def _is_admin(user: dict) -> bool:
    return user.get("email", "").endswith("@neuralearn.ai") or user.get("plan", "free") in ("pro", "elite")


@router.get("/analytics/dashboard")
async def analytics_dashboard(request: Request):
    """Admin analytics overview: credits, quiz performance, adaptive profiles, verification."""
    user = await get_current_user(request)
    if not _is_admin(user):
        raise HTTPException(status_code=403, detail="Admin only")

    # Total users, verified vs unverified
    total_users     = await db.users.count_documents({})
    verified_users  = await db.users.count_documents({"is_verified": True})
    google_users    = await db.users.count_documents({"auth_type": "google"})

    # Credits consumed in last 7 days
    since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    credit_pipeline = [
        {"$match": {"timestamp": {"$gte": since}}},
        {"$group": {
            "_id": "$kind",
            "total_credits": {"$sum": "$credits_used"},
            "count": {"$sum": 1},
            "avg_word_count": {"$avg": "$word_count"},
        }},
    ]
    credit_stats = await db.credit_analytics.aggregate(credit_pipeline).to_list(20)

    # Quiz performance
    quiz_pipeline = [
        {"$unwind": "$quiz_history"},
        {"$group": {
            "_id": None,
            "avg_score": {"$avg": "$quiz_history.score_pct"},
            "total_quizzes": {"$sum": 1},
        }},
    ]
    quiz_agg = await db.student_profiles.aggregate(quiz_pipeline).to_list(1)
    quiz_stats = quiz_agg[0] if quiz_agg else {"avg_score": 0, "total_quizzes": 0}
    quiz_stats.pop("_id", None)

    # Topic mastery heatmap — most weak topics across all students
    mastery_pipeline = [
        {"$project": {"topics": {"$objectToArray": "$topics"}}},
        {"$unwind": "$topics"},
        {"$group": {
            "_id": "$topics.k",
            "avg_mastery": {"$avg": "$topics.v.mastery"},
            "student_count": {"$sum": 1},
        }},
        {"$sort": {"avg_mastery": 1}},
        {"$limit": 10},
    ]
    weak_topics = await db.student_profiles.aggregate(mastery_pipeline).to_list(10)
    for t in weak_topics:
        t.pop("_id", None) if "_id" not in (t.get("_id") or {}) else None
        t["topic"] = t.pop("_id", "")
        t["avg_mastery"] = round(t.get("avg_mastery", 0), 3)

    # Question bank stats
    kb_count = await db.question_bank.count_documents({})

    # Chapter title confidence (chapters with cbse_data fallback vs verified)
    verified_chapters = await db.curriculum.count_documents({"verified": True})
    total_chapters    = await db.curriculum.count_documents({})

    return {
        "users": {
            "total": total_users,
            "verified": verified_users,
            "unverified": total_users - verified_users,
            "google_auth": google_users,
            "jwt_auth": total_users - google_users,
        },
        "credits_7d": credit_stats,
        "quiz_stats": quiz_stats,
        "weak_topics_platform": weak_topics,
        "question_bank": {"total_qa_pairs": kb_count},
        "curriculum": {
            "total_chapters": total_chapters,
            "verified_chapters": verified_chapters,
        },
    }


@router.get("/analytics/student/{user_id}")
async def student_analytics(user_id: str, request: Request):
    """Per-student analytics: adaptive profile + credit history."""
    caller = await get_current_user(request)
    if caller.get("user_id") != user_id and not _is_admin(caller):
        raise HTTPException(status_code=403, detail="Forbidden")

    profile = await db.student_profiles.find_one({"user_id": user_id}, {"_id": 0})
    if not profile:
        return {"profile": None, "credits_used": 0}

    # Credits consumed
    credit_total_pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": None, "total": {"$sum": "$credits_used"}, "requests": {"$sum": 1}}},
    ]
    credit_agg = await db.credit_analytics.aggregate(credit_total_pipeline).to_list(1)
    credit_totals = credit_agg[0] if credit_agg else {"total": 0, "requests": 0}
    credit_totals.pop("_id", None)

    return {"profile": profile, "credit_stats": credit_totals}
