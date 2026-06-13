"""Credit system — cost-calibrated to keep ₹399/month plan profitable.

Business target:
  100 users × ₹399 = ₹39,900 revenue
  Target AI cost  = ₹15,000–20,000/month (≤₹200/user)

Credit costs are set so 500 credits ≈ ₹150–180 worst-case AI spend per user.

Credit → token mapping (gpt-4o-mini, KB-assisted):
  ai_message      1 cr  → KB hit ~130 tok  (₹0.01) | KB miss ~800 tok (₹0.08)
  quiz_generate   8 cr  → ~1,200 tokens    (₹0.13)
  mock_exam       25 cr → ~4,000 tokens    (₹0.42)
  mock_exam_cached 3 cr → served from cache (₹0.00 AI cost)

Worst case all-KB-miss: 500 msg × ₹0.08 = ₹40. Fine.
Worst case mix: 300 msg + 10 quizzes + 4 mocks
  = 300×₹0.05 + 10×₹0.13 + 4×₹0.42 = ₹15+₹1.3+₹1.68 = ₹18/user ✅
"""

from fastapi import HTTPException
from pymongo import ReturnDocument
from core import db

CREDIT_COSTS = {
    "ai_message":          1,    # cheap — KB handles most
    "quiz_generate":       8,    # ~1,200 tokens
    "mock_exam_generate":  25,   # ~4,000 tokens
    "mock_exam_cached":    3,    # cache hit — no generation cost
}

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
        "quiz_generate":      "Not enough credits to generate a quiz (costs 8 credits).",
        "mock_exam_generate": "Not enough credits for a mock exam (costs 25 credits).",
        "mock_exam_cached":   "Not enough credits.",
    }.get(kind, "Not enough credits.")
    return f"{pretty} You have {balance} credit{'s' if balance != 1 else ''} left."
