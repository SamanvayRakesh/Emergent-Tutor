"""Lightweight credit system.

- New users seeded with 100 credits.
- Deduction helpers raise HTTPException(402) if insufficient.
- Costs:
    AI tutor message     = 1
    Quiz generation      = 5
    Mock exam generation = 10
"""
from fastapi import HTTPException
from pymongo import ReturnDocument

from core import db

CREDIT_COSTS = {
    "ai_message": 1,
    "quiz_generate": 5,
    "mock_exam_generate": 10,
}

STARTER_CREDITS = 100


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
    """Atomically deduct `cost(kind)` credits. Idempotent on failure (re-raises 402)."""
    cost = CREDIT_COSTS.get(kind, 0)
    if cost <= 0:
        return {"deducted": 0, "balance": await get_credits(user_id)}
    # Atomic conditional decrement
    result = await db.users.find_one_and_update(
        {"user_id": user_id, "credits": {"$gte": cost}},
        {"$inc": {"credits": -cost}},
        projection={"_id": 0, "credits": 1},
        return_document=ReturnDocument.AFTER,
    )
    if not result:
        # Race condition or low balance — bubble up cleanly
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


def _msg_for(kind: str, balance: int) -> str:
    pretty = {
        "ai_message": "Not enough credits to send another AI message.",
        "quiz_generate": "Not enough credits to generate a quiz.",
        "mock_exam_generate": "Not enough credits to generate a mock exam.",
    }.get(kind, "Not enough credits.")
    return f"{pretty} You have {balance} credit{'s' if balance != 1 else ''} left."
