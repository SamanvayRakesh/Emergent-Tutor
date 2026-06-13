"""Adaptive Learning Engine + Token Budget Guardian.

Two responsibilities:
1. Student profiles — mastery tracking, compact memory for AI prompts
2. Token budget — hard monthly caps per plan, model auto-downgrade

Token budget rules (maps to credits.py PLAN_TOKEN_CAPS):
  0–70%  → normal routing (gpt-4o-mini for B, gpt-4o for C on elite)
  70–90% → force gpt-4o-mini for everything, max_tokens halved
  90%+   → gpt-4o-mini only, max_tokens = 150 (bare minimum)
  100%   → hard block, serve static fallback response
"""

from datetime import datetime, timezone
from typing import Optional
from core import db, logger
from credits import PLAN_TOKEN_CAPS

COST_PER_1K_TOKENS_INR = 0.10   # gpt-4o-mini blended input+output @ ₹84/USD


# ── Student profile ──────────────────────────────────────────────────────────

async def get_student_profile(user_id: str) -> dict:
    doc = await db.student_profiles.find_one({"user_id": user_id}, {"_id": 0})
    if not doc:
        doc = {
            "user_id": user_id,
            "topics": {},
            "difficulty": "medium",
            "learning_pace": "normal",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.student_profiles.insert_one(doc)
        doc.pop("_id", None)
    return doc


async def update_topic_performance(user_id: str, topic: str, correct: bool):
    profile = await get_student_profile(user_id)
    topics = profile.get("topics", {})
    entry = topics.get(topic, {
        "mastery": 0.5, "attempts": 0, "correct": 0,
        "incorrect": 0, "streak": 0, "last_seen": None,
    })
    entry["attempts"] += 1
    if correct:
        entry["correct"] += 1
        entry["streak"] = entry.get("streak", 0) + 1
        entry["mastery"] = min(1.0, entry["mastery"] + 0.05 * (1 - entry["mastery"]))
    else:
        entry["incorrect"] += 1
        entry["streak"] = 0
        entry["mastery"] = max(0.0, entry["mastery"] - 0.08)
    entry["last_seen"] = datetime.now(timezone.utc).isoformat()

    all_mastery = [v["mastery"] for v in {**topics, topic: entry}.values() if "mastery" in v]
    avg = sum(all_mastery) / len(all_mastery) if all_mastery else 0.5
    difficulty = "easy" if avg < 0.4 else "hard" if avg > 0.75 else "medium"

    await db.student_profiles.update_one(
        {"user_id": user_id},
        {"$set": {
            f"topics.{topic}": entry,
            "difficulty": difficulty,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }},
        upsert=True,
    )


def build_compact_memory(profile: dict) -> dict:
    """~60 token summary injected into AI prompt. Never sends full history."""
    topics = profile.get("topics", {})
    weak   = [t for t, v in topics.items() if v.get("mastery", 1) < 0.45]
    strong = [t for t, v in topics.items() if v.get("mastery", 0) > 0.75]
    return {
        "weak_topics":   weak[:5],
        "strong_topics": strong[:5],
        "difficulty":    profile.get("difficulty", "medium"),
        "learning_pace": profile.get("learning_pace", "normal"),
    }


# ── Token budget ─────────────────────────────────────────────────────────────

def _month_key() -> str:
    n = datetime.now(timezone.utc)
    return f"{n.year}-{n.month:02d}"


async def record_token_usage(user_id: str, model: str, input_tokens: int, output_tokens: int):
    total = input_tokens + output_tokens
    cost_inr = total / 1000 * COST_PER_1K_TOKENS_INR
    month = _month_key()
    await db.token_budgets.update_one(
        {"user_id": user_id},
        {
            "$inc": {
                f"months.{month}.tokens": total,
                f"months.{month}.cost_inr": cost_inr,
                f"months.{month}.requests": 1,
            },
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()},
        },
        upsert=True,
    )
    return cost_inr


async def get_monthly_tokens(user_id: str) -> int:
    month = _month_key()
    doc = await db.token_budgets.find_one({"user_id": user_id}, {"_id": 0})
    if not doc:
        return 0
    return int(doc.get("months", {}).get(month, {}).get("tokens", 0))


async def check_budget(user_id: str, plan_id: str) -> dict:
    """Returns budget status + routing guidance for this request."""
    # Map plan names (starter = pro-tier at ₹399)
    cap_key = plan_id if plan_id in PLAN_TOKEN_CAPS else "starter"
    cap = PLAN_TOKEN_CAPS.get(cap_key, PLAN_TOKEN_CAPS["free"])
    used = await get_monthly_tokens(user_id)
    pct = (used / cap * 100) if cap else 0

    return {
        "cap": cap,
        "used": used,
        "remaining": max(0, cap - used),
        "pct_used": round(pct, 1),
        # Routing tiers
        "over_budget":  pct >= 100,   # hard block
        "critical":     pct >= 90,    # mini only, 150 tokens
        "near_budget":  pct >= 70,    # mini only, halved tokens
        "normal":       pct < 70,
    }
