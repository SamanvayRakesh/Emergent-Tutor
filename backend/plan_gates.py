"""Plan & usage gates — the heart of feature gating.
Backend-enforced limits per plan. All limit checks return (allowed: bool, info: dict).
"""
from datetime import datetime, timezone, timedelta
from typing import Optional

from core import db


# ----- Plan catalog -----
PLANS = {
    "free": {
        "id": "free",
        "name": "Free",
        "price_monthly": 0,
        "price_yearly": 0,
        "tagline": "Start your learning journey",
        "color": "#94a3b8",
        "limits": {
            "ai_messages_per_day": 10,
            "mock_exams_per_week": 1,
            "quizzes_per_day": 3,
            "study_plan": True,            # basic only
            "adaptive_quizzes": False,
            "leaderboard_full": False,     # top 10 only
            "deep_analytics": False,
            "ai_memory": False,
            "priority_responses": False,
            "exam_countdown": False,
            "weak_topic_analytics": False,
            "ai_model": "gpt-4o-mini",
        },
        "highlights": [
            "10 AI tutor messages / day",
            "1 mock exam / week",
            "3 quizzes / day",
            "Basic study plan",
            "Top 10 leaderboard",
        ],
        "locked": [
            "Adaptive weak-topic quizzes",
            "Deep performance analytics",
            "Unlimited AI tutor",
            "Exam countdown strategy",
            "Priority AI responses",
        ],
    },
    "pro": {
        "id": "pro",
        "name": "Pro",
        "price_monthly": 299,
        "price_yearly": 2870,  # ~20% off
        "tagline": "Unlock your full potential",
        "color": "#2563eb",
        "badge": "MOST POPULAR",
        "limits": {
            "ai_messages_per_day": None,   # unlimited
            "mock_exams_per_week": 5,
            "quizzes_per_day": None,
            "study_plan": True,
            "adaptive_quizzes": True,
            "leaderboard_full": True,
            "deep_analytics": True,
            "ai_memory": True,
            "priority_responses": False,
            "exam_countdown": False,
            "weak_topic_analytics": True,
            "ai_model": "gpt-4o",
        },
        "highlights": [
            "Unlimited AI tutoring",
            "5 mock exams / week",
            "Adaptive weak-topic quizzes",
            "Full leaderboard rankings",
            "Personalised study plan",
            "Weak-topic analytics",
            "AI memory & smart recommendations",
            "Faster, smarter GPT-4o responses",
        ],
        "locked": [
            "Unlimited adaptive mocks",
            "Exam countdown intensive mode",
            "Priority response queue",
        ],
    },
    "elite": {
        "id": "elite",
        "name": "Elite",
        "price_monthly": 799,
        "price_yearly": 7670,  # ~20% off
        "tagline": "Built for board exam toppers",
        "color": "#dc2626",
        "badge": "PREMIUM",
        "limits": {
            "ai_messages_per_day": None,
            "mock_exams_per_week": None,
            "quizzes_per_day": None,
            "study_plan": True,
            "adaptive_quizzes": True,
            "leaderboard_full": True,
            "deep_analytics": True,
            "ai_memory": True,
            "priority_responses": True,
            "exam_countdown": True,
            "weak_topic_analytics": True,
            "performance_prediction": True,
            "ai_model": "gpt-4o",
        },
        "highlights": [
            "Everything in Pro",
            "Unlimited adaptive mock exams",
            "Advanced exam simulations",
            "AI-generated revision strategies",
            "Exam countdown intensive mode",
            "Performance prediction",
            "Priority AI response queue",
            "Deep weak-point tracking",
            "Competitive rankings & insights",
        ],
        "locked": [],
    },
}


def get_plan(plan_id: str) -> dict:
    return PLANS.get(plan_id, PLANS["free"])


# ----- User plan resolver -----
async def get_user_plan(user_id: str) -> dict:
    """Returns the current effective plan for a user (checks expiry)."""
    sub = await db.subscriptions.find_one({"user_id": user_id}, {"_id": 0})
    now = datetime.now(timezone.utc)
    if sub and sub.get("status") == "active":
        try:
            expires = datetime.fromisoformat(sub["expires_at"])
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if expires > now:
                plan = get_plan(sub["plan"])
                return {
                    **plan,
                    "subscription": {
                        "plan": sub["plan"],
                        "billing_cycle": sub.get("billing_cycle", "monthly"),
                        "status": "active",
                        "expires_at": sub["expires_at"],
                        "started_at": sub.get("started_at"),
                    },
                }
        except Exception:
            pass
    # default: free
    return {**get_plan("free"), "subscription": {"plan": "free", "status": "free", "expires_at": None}}


# ----- Usage counters -----
def _today_key() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _week_key() -> str:
    now = datetime.now(timezone.utc)
    monday = now - timedelta(days=now.weekday())
    return monday.strftime("week-%Y-%m-%d")


async def get_usage(user_id: str) -> dict:
    today = _today_key()
    week = _week_key()
    doc = await db.usage_counters.find_one({"user_id": user_id}, {"_id": 0}) or {}
    return {
        "ai_messages_today": (doc.get("ai_messages_by_day") or {}).get(today, 0),
        "quizzes_today": (doc.get("quizzes_by_day") or {}).get(today, 0),
        "mocks_this_week": (doc.get("mocks_by_week") or {}).get(week, 0),
    }


async def increment_usage(user_id: str, kind: str, n: int = 1):
    """kind: 'ai_messages' | 'quizzes' | 'mocks'"""
    today = _today_key()
    week = _week_key()
    bucket_map = {
        "ai_messages": (f"ai_messages_by_day.{today}", "ai_messages_by_day"),
        "quizzes": (f"quizzes_by_day.{today}", "quizzes_by_day"),
        "mocks": (f"mocks_by_week.{week}", "mocks_by_week"),
    }
    field, _ = bucket_map[kind]
    await db.usage_counters.update_one(
        {"user_id": user_id},
        {"$inc": {field: n}, "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )


# ----- Limit checks -----
async def check_limit(user_id: str, kind: str) -> tuple[bool, dict]:
    """kind: 'ai_message' | 'quiz' | 'mock_exam'
    Returns (allowed, info_dict). info contains current/limit/plan."""
    plan_info = await get_user_plan(user_id)
    limits = plan_info["limits"]
    usage = await get_usage(user_id)

    if kind == "ai_message":
        limit = limits.get("ai_messages_per_day")
        current = usage["ai_messages_today"]
        unit = "messages today"
    elif kind == "quiz":
        limit = limits.get("quizzes_per_day")
        current = usage["quizzes_today"]
        unit = "quizzes today"
    elif kind == "mock_exam":
        limit = limits.get("mock_exams_per_week")
        current = usage["mocks_this_week"]
        unit = "mock exams this week"
    else:
        return True, {}

    info = {
        "plan": plan_info["id"], "current": current, "limit": limit,
        "remaining": (limit - current) if limit is not None else None,
        "unit": unit,
    }
    if limit is None:  # unlimited
        return True, info
    return current < limit, info


async def has_feature(user_id: str, feature_key: str) -> bool:
    """Boolean feature gate. e.g. 'adaptive_quizzes', 'deep_analytics', 'priority_responses'."""
    plan_info = await get_user_plan(user_id)
    return bool(plan_info["limits"].get(feature_key, False))
