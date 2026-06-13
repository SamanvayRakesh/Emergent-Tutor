"""Credit system — cost-calibrated to keep ₹399/month plan profitable.

Credits for AI chat scale with words generated:
  - 1 credit per 100 words (rounded up), min 1 credit
  - Max response capped at 1000 words (soft warning injected)

Fixed costs:
  quiz_generate   15 cr → ~1,200 tokens
  mock_exam       30 cr → ~4,000 tokens
"""

from fastapi import HTTPException
from pymongo import ReturnDocument
from core import db

CREDIT_COSTS = {
    "ai_message":          1,    # base — actual deduction calculated per response word count
    "quiz_generate":       15,   # ~1,200 tokens
    "mock_exam_generate":  30,   # ~4,000 tokens
    "mock_exam_cached":    3,    # cache hit — no generation cost
}

# Credit cost per 100 words generated (chat only)
CREDITS_PER_100_WORDS = 1
CHAT_WORD_LIMIT = 1000  # soft cap — warning injected if exceeded


def calculate_chat_credits(word_count: int) -> int:
    """Calculate credits for a chat response based on word count. Min 1 credit."""
    return max(1, (word_count + 99) // 100)  # ceil(words / 100)

# Monthly hard token caps per plan (safety ceiling on top of credits)
# gpt-4o-mini: $0.15/1M input, $0.60/1M output → ~₹0.10/1K tokens blended
PLAN_TOKEN_CAPS = {
    "free":    40_000,    # ~₹4/month max
    "starter": 200_000,   # ~₹20/month max   ← ₹399 plan
    "pro":     600_000,   # ~₹60/month max   ← ₹699 plan (future)
    "elite":   1_500_000, # ~₹150/month max
}

# Credits bundled with each plan on signup / renewal
PLAN_STARTER_CREDITS = {
    "free":    100,
    "starter": 500,
    "pro":     1500,
    "elite":   5000,
}

STARTER_CREDITS = 100   # free tier default (legacy compat)


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
    """Atomically deduct credits based on chat response word count. Min 1 credit."""
    cost = calculate_chat_credits(word_count)
    if cost <= 0:
        return {"deducted": 0, "balance": await get_credits(user_id)}
    result = await db.users.find_one_and_update(
        {"user_id": user_id, "credits": {"$gte": cost}},
        {"$inc": {"credits": -cost}},
        projection={"_id": 0, "credits": 1},
        return_document=ReturnDocument.AFTER,
    )
    if not result:
        # Not enough credits — deduct minimum 1 if any available, else just proceed
        balance = await get_credits(user_id)
        if balance > 0:
            await db.users.update_one({"user_id": user_id}, {"$inc": {"credits": -1}})
            return {"deducted": 1, "balance": max(0, balance - 1)}
        return {"deducted": 0, "balance": 0}
    return {"deducted": cost, "balance": result.get("credits", 0)}


async def deduct_credits(user_id: str, kind: str) -> dict:
    """Atomically deduct credits. Raises 402 on insufficient balance."""
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
    return {"deducted": cost, "balance": result.get("credits", 0)}


async def grant_plan_credits(user_id: str, plan_id: str):
    """Grant credits on plan activation/renewal. Idempotent — adds to existing balance."""
    amount = PLAN_STARTER_CREDITS.get(plan_id, STARTER_CREDITS)
    await db.users.update_one(
        {"user_id": user_id},
        {"$inc": {"credits": amount}},
        upsert=True,
    )
    return amount


def _msg_for(kind: str, balance: int) -> str:
    pretty = {
        "ai_message":         "Not enough credits to send an AI message.",
        "quiz_generate":      f"Not enough credits to generate a quiz (costs {CREDIT_COSTS['quiz_generate']} credits).",
        "mock_exam_generate": f"Not enough credits for a mock exam (costs {CREDIT_COSTS['mock_exam_generate']} credits).",
        "mock_exam_cached":   "Not enough credits.",
    }.get(kind, "Not enough credits.")
    return f"{pretty} You have {balance} credit{'s' if balance != 1 else ''} left."
