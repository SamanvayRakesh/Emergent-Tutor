"""Plan & usage gates — backend-enforced limits per plan."""
from datetime import datetime, timezone, timedelta
from core import db

PLANS = {
    "free": {
        "id": "free", "name": "Free",
        "price_monthly": 0, "price_yearly": 0,
        "tagline": "Start your learning journey",
        "color": "#94a3b8",
        "limits": {
            "ai_messages_per_day": 10,
            "mock_exams_per_week": 1,
            "quizzes_per_day": 3,
            "study_plan": True,
            "adaptive_quizzes": False,
            "leaderboard_full": False,
            "deep_analytics": False,
            "ai_memory": False,
            "ai_model": "gpt-4o-mini",
        },
        "highlights": [
            "10 AI messages / day",
            "1 mock exam / week",
            "3 quizzes / day",
            "Basic study plan",
        ],
    },
    "starter": {
        "id": "starter", "name": "Starter",
        "price_monthly": 399, "price_yearly": 3830,
        "tagline": "Everything you need to score better",
        "color": "#2563eb",
        "badge": "MOST POPULAR",
        "limits": {
            "ai_messages_per_day": None,   # credit-gated, not day-gated
            "mock_exams_per_week": 5,
            "quizzes_per_day": None,
            "study_plan": True,
            "adaptive_quizzes": True,
            "leaderboard_full": True,
            "deep_analytics": True,
            "ai_memory": True,
            "ai_model": "gpt-4o-mini",
        },
        "highlights": [
            "500 AI credits / month",
            "5 mock exams / week",
            "Unlimited quizzes",
            "Adaptive weak-topic quizzes",
            "Full leaderboard",
            "AI memory & personalisation",
            "Deep analytics",
        ],
    },
    "pro": {
        "id": "pro", "name": "Pro",
        "price_monthly": 699, "price_yearly": 6710,
        "tagline": "Unlock your full potential",
        "color": "#7c3aed",
        "limits": {
            "ai_messages_per_day": None,
            "mock_exams_per_week": None,
            "quizzes_per_day": None,
            "study_plan": True,
            "adaptive_quizzes": True,
            "leaderboard_full": True,
            "deep_analytics": True,
            "ai_memory": True,
            "exam_countdown": True,
            "ai_model": "gpt-4o-mini",
        },
        "highlights": [
            "1,500 AI credits / month",
            "Unlimited mock exams",
            "Exam countdown mode",
            "Everything in Starter",
        ],
    },
    "elite": {
        "id": "elite", "name": "Elite",
        "price_monthly": 999, "price_yearly": 9590,
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
            "exam_countdown": True,
            "priority_responses": True,
            "performance_prediction": True,
            "ai_model": "gpt-4o",
        },
        "highlights": [
            "5,000 AI credits / month",
            "GPT-4o for complex topics",
            "Priority response queue",
            "Performance prediction",
            "Everything in Pro",
        ],
    },
}

# Legacy alias — old 'pro' plan maps to 'starter' pricing tier
PLANS["pro_legacy"] = PLANS["starter"]


def get_plan(plan_id: str) -> dict:
    return PLANS.get(plan_id, PLANS["free"])


async def get_user_plan(user_id: str) -> dict:
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
    return {**get_plan("free"), "subscription": {"plan": "free", "status": "free", "expires_at": None}}


def _today_key() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _week_key() -> str:
    now = datetime.now(timezone.utc)
    monday = now - timedelta(days=now.weekday())
    return monday.strftime("week-%Y-%m-%d")


async def get_usage(user_id: str) -> dict:
    today = _today_key()
    week  = _week_key()
    doc   = await db.usage_counters.find_one({"user_id": user_id}, {"_id": 0}) or {}
    return {
        "ai_messages_today": (doc.get("ai_messages_by_day") or {}).get(today, 0),
        "quizzes_today":     (doc.get("quizzes_by_day") or {}).get(today, 0),
        "mocks_this_week":   (doc.get("mocks_by_week") or {}).get(week, 0),
    }


async def increment_usage(user_id: str, kind: str, n: int = 1):
    today = _today_key()
    week  = _week_key()
    field = {
        "ai_messages": f"ai_messages_by_day.{today}",
        "quizzes":     f"quizzes_by_day.{today}",
        "mocks":       f"mocks_by_week.{week}",
    }.get(kind)
    if not field:
        return
    await db.usage_counters.update_one(
        {"user_id": user_id},
        {"$inc": {field: n}, "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )


async def check_limit(user_id: str, kind: str) -> tuple:
    plan_info = await get_user_plan(user_id)
    limits    = plan_info["limits"]
    usage     = await get_usage(user_id)

    if kind == "ai_message":
        limit   = limits.get("ai_messages_per_day")
        current = usage["ai_messages_today"]
        unit    = "messages today"
    elif kind == "quiz":
        limit   = limits.get("quizzes_per_day")
        current = usage["quizzes_today"]
        unit    = "quizzes today"
    elif kind == "mock_exam":
        limit   = limits.get("mock_exams_per_week")
        current = usage["mocks_this_week"]
        unit    = "mock exams this week"
    else:
        return True, {}

    info = {
        "plan": plan_info["id"], "current": current, "limit": limit,
        "remaining": (limit - current) if limit is not None else None,
        "unit": unit,
    }
    if limit is None:
        return True, info
    return current < limit, info


async def has_feature(user_id: str, feature_key: str) -> bool:
    plan_info = await get_user_plan(user_id)
    return bool(plan_info["limits"].get(feature_key, False))


def get_ai_model_for_complexity(user_plan_id: str, complexity: str) -> str:
    """Legacy compat helper."""
    if complexity == "simple":
        return "gpt-4o-mini"
    if complexity == "complex" and user_plan_id == "elite":
        return "gpt-4o"
    return "gpt-4o-mini"
