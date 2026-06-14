"""True Adaptive Learning Engine.

Tracks per-student:
  - Topic mastery (weighted EMA)
  - Quiz performance per topic
  - Response time (seconds per answer)
  - Preferred explanation style (visual / step-by-step / examples / brief)
  - Difficulty progression (auto-adjusting)
  - Session performance history
  - Concept-level mastery within topics
  - Weak/strong areas with confidence scores

Persists in MongoDB student_profiles collection.
"""

from datetime import datetime, timezone
from typing import Optional
from core import db, logger
from credits import PLAN_TOKEN_CAPS

COST_PER_1K_TOKENS_INR = 0.10


# ── Student profile ───────────────────────────────────────────────────────────

async def get_student_profile(user_id: str) -> dict:
    doc = await db.student_profiles.find_one({"user_id": user_id}, {"_id": 0})
    if not doc:
        doc = {
            "user_id": user_id,
            "topics": {},
            "concepts": {},
            "difficulty": "medium",
            "learning_pace": "normal",
            "preferred_style": "balanced",   # visual | step-by-step | examples | brief | balanced
            "quiz_history": [],              # [{topic, score_pct, date}]
            "session_scores": [],            # [{date, accuracy, duration_s}]
            "total_questions_answered": 0,
            "total_correct": 0,
            "avg_response_time_s": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.student_profiles.insert_one(doc)
        doc.pop("_id", None)
    return doc


async def update_topic_performance(
    user_id: str,
    topic: str,
    correct: bool,
    response_time_s: Optional[float] = None,
    concept: Optional[str] = None,
):
    """Update mastery for a topic (and optional concept) after a quiz answer."""
    profile = await get_student_profile(user_id)
    topics = profile.get("topics", {})

    entry = topics.get(topic, {
        "mastery": 0.5, "attempts": 0, "correct": 0,
        "incorrect": 0, "streak": 0, "last_seen": None,
        "avg_time_s": None,
    })
    entry["attempts"] += 1

    if correct:
        entry["correct"] += 1
        entry["streak"] = entry.get("streak", 0) + 1
        # EMA: mastery increases faster when it's low (harder to gain near 100%)
        entry["mastery"] = min(1.0, entry["mastery"] + 0.07 * (1 - entry["mastery"]))
    else:
        entry["incorrect"] += 1
        entry["streak"] = 0
        entry["mastery"] = max(0.0, entry["mastery"] - 0.10)

    entry["last_seen"] = datetime.now(timezone.utc).isoformat()

    # Response time EMA
    if response_time_s is not None:
        prev = entry.get("avg_time_s")
        entry["avg_time_s"] = (
            response_time_s if prev is None
            else 0.7 * prev + 0.3 * response_time_s
        )

    # Recalculate difficulty from all topics
    all_topics = {**topics, topic: entry}
    all_mastery = [v["mastery"] for v in all_topics.values() if "mastery" in v]
    avg = sum(all_mastery) / len(all_mastery) if all_mastery else 0.5

    if avg < 0.35:
        difficulty = "easy"
        pace = "slow"
    elif avg < 0.55:
        difficulty = "easy"
        pace = "normal"
    elif avg < 0.72:
        difficulty = "medium"
        pace = "normal"
    elif avg < 0.88:
        difficulty = "hard"
        pace = "fast"
    else:
        difficulty = "hard"
        pace = "fast"

    # Concept tracking (sub-topic level)
    concepts = profile.get("concepts", {})
    if concept:
        ce = concepts.get(concept, {"mastery": 0.5, "attempts": 0})
        ce["attempts"] += 1
        if correct:
            ce["mastery"] = min(1.0, ce["mastery"] + 0.08 * (1 - ce["mastery"]))
        else:
            ce["mastery"] = max(0.0, ce["mastery"] - 0.12)
        concepts[concept] = ce

    # Total stats
    total_q = profile.get("total_questions_answered", 0) + 1
    total_c = profile.get("total_correct", 0) + (1 if correct else 0)

    await db.student_profiles.update_one(
        {"user_id": user_id},
        {"$set": {
            f"topics.{topic}": entry,
            "concepts": concepts,
            "difficulty": difficulty,
            "learning_pace": pace,
            "total_questions_answered": total_q,
            "total_correct": total_c,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }},
        upsert=True,
    )


async def record_quiz_result(user_id: str, topic: str, score_pct: int, correct: int, total: int):
    """Record a full quiz result; updates quiz history + topic mastery."""
    now = datetime.now(timezone.utc).isoformat()
    profile = await get_student_profile(user_id)

    # Add to quiz_history (keep last 50)
    history = profile.get("quiz_history", [])
    history.append({"topic": topic, "score_pct": score_pct, "correct": correct, "total": total, "date": now})
    history = history[-50:]

    # Adjust topic mastery based on quiz score
    topics = profile.get("topics", {})
    entry = topics.get(topic, {"mastery": 0.5, "attempts": 0, "correct": 0, "incorrect": 0, "streak": 0})
    score_ratio = score_pct / 100
    # Quiz performance pulls mastery towards score
    entry["mastery"] = 0.6 * entry["mastery"] + 0.4 * score_ratio
    entry["attempts"] = entry.get("attempts", 0) + total
    entry["correct"] = entry.get("correct", 0) + correct
    entry["incorrect"] = entry.get("incorrect", 0) + (total - correct)
    entry["last_seen"] = now

    # Infer explanation style preference from performance patterns
    preferred_style = profile.get("preferred_style", "balanced")
    avg_score_recent = sum(h["score_pct"] for h in history[-5:]) / min(5, len(history)) if history else 50
    if avg_score_recent < 40:
        preferred_style = "step-by-step"   # needs more guidance
    elif avg_score_recent > 80:
        preferred_style = "brief"          # grasps quickly, keep concise
    elif avg_score_recent < 60:
        preferred_style = "examples"       # needs more examples

    all_topics = {**topics, topic: entry}
    all_mastery = [v["mastery"] for v in all_topics.values() if "mastery" in v]
    avg = sum(all_mastery) / len(all_mastery) if all_mastery else 0.5
    difficulty = "easy" if avg < 0.4 else "hard" if avg > 0.75 else "medium"

    await db.student_profiles.update_one(
        {"user_id": user_id},
        {"$set": {
            f"topics.{topic}": entry,
            "quiz_history": history,
            "difficulty": difficulty,
            "preferred_style": preferred_style,
            "updated_at": now,
        }},
        upsert=True,
    )


def build_compact_memory(profile: dict) -> dict:
    """~80 token summary injected into every AI prompt."""
    topics = profile.get("topics", {})
    weak   = sorted([t for t, v in topics.items() if v.get("mastery", 1) < 0.45],
                    key=lambda t: topics[t].get("mastery", 1))[:5]
    strong = sorted([t for t, v in topics.items() if v.get("mastery", 0) > 0.75],
                    key=lambda t: topics[t].get("mastery", 0), reverse=True)[:5]

    # Recent quiz performance
    hist = profile.get("quiz_history", [])
    recent_avg = sum(h["score_pct"] for h in hist[-3:]) / min(3, len(hist)) if hist else None

    return {
        "weak_topics":    weak,
        "strong_topics":  strong,
        "difficulty":     profile.get("difficulty", "medium"),
        "learning_pace":  profile.get("learning_pace", "normal"),
        "style":          profile.get("preferred_style", "balanced"),
        "recent_quiz_avg": int(recent_avg) if recent_avg is not None else None,
    }


# ── Token budget ──────────────────────────────────────────────────────────────

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
    cap_key = plan_id if plan_id in PLAN_TOKEN_CAPS else "starter"
    cap = PLAN_TOKEN_CAPS.get(cap_key, PLAN_TOKEN_CAPS["free"])
    used = await get_monthly_tokens(user_id)
    pct = (used / cap * 100) if cap else 0

    return {
        "cap": cap,
        "used": used,
        "remaining": max(0, cap - used),
        "pct_used": round(pct, 1),
        "over_budget":  pct >= 100,
        "critical":     pct >= 90,
        "near_budget":  pct >= 70,
        "normal":       pct < 70,
    }
