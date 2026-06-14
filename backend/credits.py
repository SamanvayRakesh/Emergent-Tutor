"""Credit system — dynamic 2-10 credits based on response length.

Chat credit tiers (words generated):
  0–250    → 2 credits
  251–500  → 4 credits
  501–800  → 6 credits
  801–1200 → 8 credits
  1201+    → 10 credits

Fixed costs:
  quiz_generate       15 cr
  mock_exam_generate  30 cr
  mock_exam_cached     3 cr
"""

from datetime import datetime, timezone
from fastapi import HTTPException
from pymongo import ReturnDocument
from core import db

CREDIT_COSTS = {
    "ai_message":          2,    # minimum — actual deduction calculated per word count
    "quiz_generate":       15,
    "mock_exam_generate":  30,
    "mock_exam_cached":    3,
}

CHAT_WORD_LIMIT = 1500   # soft cap — warning injected if exceeded

# Monthly hard token caps per plan
PLAN_TOKEN_CAPS = {
    "free":    40_000,
    "starter": 200_000,
    "pro":     600_000,
    "elite":   1_500_000,
}

PLAN_STARTER_CREDITS = {
    "free":    100,
    "starter": 500,
    "pro":     1500,
    "elite":   5000,
}

STARTER_CREDITS = 100


def calculate_chat_credits(word_count: int) -> int:
    """Dynamic tier: 2-10 credits based on words generated."""
    if word_count <= 250:
        return 2
    elif word_count <= 500:
        return 4
    elif word_count <= 800:
        return 6
    elif word_count <= 1200:
        return 8
    else:
        return 10


async def get_credits(user_id: str) -> int:
    doc = await db.users.find_one({"user_id": user_id}, {"_id": 0, "credits": 1}) or {}
    return int(doc.get("credits") or 0)


async def ensure_credits(user_id: str, kind: str) -> int:
    """Raise 402 if user can't afford `kind`. Returns balance before deduction."""
    cost = CREDIT_COSTS.get(kind, 0)
    balance = await get_credits(user_id)
    if balance < cost:
        raise HTTPException(
            status_code=402,
            detail={
                "code": "INSUFFICIENT_CREDITS",
                "feature": kind,
                "cost": cost,
                "balance": balance,
                "message": _msg_for(kind, balance),
            },
        )
    return balance


async def deduct_credits_for_chat(user_id: str, word_count: int) -> dict:
    """Atomically deduct credits based on word count tier."""
    cost = calculate_chat_credits(word_count)
    result = await db.users.find_one_and_update(
        {"user_id": user_id, "credits": {"$gte": cost}},
        {
            "$inc": {"credits": -cost},
            "$set": {"last_credit_deduct": datetime.now(timezone.utc).isoformat()},
        },
        projection={"_id": 0, "credits": 1},
        return_document=ReturnDocument.AFTER,
    )
    if not result:
        # Partial deduct: use whatever is left
        balance = await get_credits(user_id)
        if balance > 0:
            await db.users.update_one({"user_id": user_id}, {"$inc": {"credits": -balance}})
            return {"deducted": balance, "balance": 0, "cost": cost}
        return {"deducted": 0, "balance": 0, "cost": cost}

    # Record analytics
    await _record_credit_event(user_id, "chat", cost, word_count)
    return {"deducted": cost, "balance": result.get("credits", 0), "cost": cost}


async def deduct_credits(user_id: str, kind: str) -> dict:
    """Atomically deduct fixed credits. Raises 402 on insufficient balance."""
    cost = CREDIT_COSTS.get(kind, 0)
    if cost <= 0:
        return {"deducted": 0, "balance": await get_credits(user_id)}
    result = await db.users.find_one_and_update(
        {"user_id": user_id, "credits": {"$gte": cost}},
        {"$inc": {"credits": -cost}},
        projection={"_id": 0, "credits": 1},
        return_document=ReturnDocument.AFTER,
    )
    if not result:
        balance = await get_credits(user_id)
        raise HTTPException(
            status_code=402,
            detail={
                "code": "INSUFFICIENT_CREDITS", "feature": kind,
                "cost": cost, "balance": balance,
                "message": _msg_for(kind, balance),
            },
        )
    await _record_credit_event(user_id, kind, cost)
    return {"deducted": cost, "balance": result.get("credits", 0)}


async def grant_plan_credits(user_id: str, plan_id: str):
    """Grant credits on plan activation/renewal."""
    amount = PLAN_STARTER_CREDITS.get(plan_id, STARTER_CREDITS)
    await db.users.update_one(
        {"user_id": user_id},
        {"$inc": {"credits": amount}},
        upsert=True,
    )
    return amount


async def _record_credit_event(user_id: str, kind: str, cost: int, word_count: int = 0):
    """Append to analytics.credit_events for admin visibility."""
    try:
        await db.credit_analytics.insert_one({
            "user_id": user_id,
            "kind": kind,
            "credits_used": cost,
            "word_count": word_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    except Exception:
        pass  # analytics is non-critical


def _msg_for(kind: str, balance: int) -> str:
    pretty = {
        "ai_message":         "Not enough credits to send an AI message.",
        "quiz_generate":      f"Not enough credits to generate a quiz (costs {CREDIT_COSTS['quiz_generate']} credits).",
        "mock_exam_generate": f"Not enough credits for a mock exam (costs {CREDIT_COSTS['mock_exam_generate']} credits).",
        "mock_exam_cached":   "Not enough credits.",
    }.get(kind, "Not enough credits.")
    return f"{pretty} You have {balance} credit{'s' if balance != 1 else ''} left."
