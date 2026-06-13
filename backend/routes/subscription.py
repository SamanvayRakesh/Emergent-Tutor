"""Subscription + onboarding routes."""
import os
import uuid
import hmac
import hashlib
from datetime import datetime, timezone, timedelta

import razorpay
from fastapi import APIRouter, HTTPException, Request

from core import db, get_current_user, logger
from credits import get_credits, CREDIT_COSTS, STARTER_CREDITS
from models import OnboardingSubmit, SubscribeRequest
from plan_gates import PLANS, get_user_plan, get_usage

router = APIRouter()


# ---- Razorpay client (lazy — only when keys configured) ----
RZP_KEY = os.environ.get("RAZORPAY_KEY_ID", "").strip()
RZP_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "").strip()
_rzp_client = None


def _razorpay():
    global _rzp_client
    if not RZP_KEY or not RZP_SECRET:
        return None
    if _rzp_client is None:
        _rzp_client = razorpay.Client(auth=(RZP_KEY, RZP_SECRET))
    return _rzp_client


@router.get("/credits")
async def my_credits(request: Request):
    """Current credit balance + cost catalog."""
    user = await get_current_user(request)
    balance = await get_credits(user["user_id"])
    return {
        "credits": balance,
        "starter_credits": STARTER_CREDITS,
        "costs": CREDIT_COSTS,
        "low_threshold": 10,
    }


# ----- Plan catalog -----
@router.get("/subscription/plans")
async def list_plans():
    """Public catalog of all plans — deduplicated by plan id."""
    seen = set()
    unique_plans = []
    for plan in PLANS.values():
        if plan["id"] not in seen:
            seen.add(plan["id"])
            unique_plans.append(plan)
    return {"plans": unique_plans}


@router.get("/subscription/me")
async def my_subscription(request: Request):
    """Current user's plan + usage."""
    user = await get_current_user(request)
    plan_info = await get_user_plan(user["user_id"])
    usage = await get_usage(user["user_id"])
    return {
        "plan_id": plan_info["id"],
        "plan_name": plan_info["name"],
        "color": plan_info.get("color"),
        "limits": plan_info["limits"],
        "highlights": plan_info.get("highlights", []),
        "locked": plan_info.get("locked", []),
        "subscription": plan_info.get("subscription"),
        "usage": usage,
    }


@router.post("/subscription/create-order")
async def create_order(body: SubscribeRequest, request: Request):
    """Create a Razorpay order for the chosen plan. Returns order details + key_id.
    If RAZORPAY_KEY_ID isn't configured, returns mock_mode=true so frontend can fall back."""
    user = await get_current_user(request)
    if body.plan not in ("pro", "elite"):
        raise HTTPException(status_code=400, detail="Plan must be 'pro' or 'elite'")
    if body.billing_cycle not in ("monthly", "yearly"):
        raise HTTPException(status_code=400, detail="billing_cycle must be 'monthly' or 'yearly'")

    plan = PLANS[body.plan]
    amount_inr = plan["price_yearly"] if body.billing_cycle == "yearly" else plan["price_monthly"]
    amount_paise = amount_inr * 100

    rzp = _razorpay()
    if not rzp:
        # Mock fallback so the demo keeps working until you add real Razorpay keys
        return {
            "mock_mode": True,
            "amount_inr": amount_inr,
            "plan": body.plan,
            "billing_cycle": body.billing_cycle,
        }

    try:
        receipt = f"nl_{user['user_id'][-8:]}_{uuid.uuid4().hex[:8]}"[:40]
        order = rzp.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "receipt": receipt,
            "notes": {
                "user_id": user["user_id"], "plan": body.plan,
                "billing_cycle": body.billing_cycle, "email": user.get("email", ""),
            },
        })
    except Exception as e:
        logger.error(f"Razorpay create_order failed: {e}")
        raise HTTPException(status_code=502, detail=f"Could not create payment order: {e}")

    return {
        "mock_mode": False,
        "order_id": order["id"],
        "amount_paise": amount_paise,
        "amount_inr": amount_inr,
        "currency": "INR",
        "key_id": RZP_KEY,
        "plan": body.plan,
        "billing_cycle": body.billing_cycle,
        "prefill": {"name": user.get("name"), "email": user.get("email")},
    }


@router.post("/subscription/verify-payment")
async def verify_payment(body: dict, request: Request):
    """Verify Razorpay payment signature and activate subscription.
    Expects: {razorpay_order_id, razorpay_payment_id, razorpay_signature, plan, billing_cycle}"""
    user = await get_current_user(request)
    order_id = body.get("razorpay_order_id")
    payment_id = body.get("razorpay_payment_id")
    signature = body.get("razorpay_signature")
    plan_id = body.get("plan")
    cycle = body.get("billing_cycle", "monthly")

    if not (order_id and payment_id and signature and plan_id):
        raise HTTPException(status_code=400, detail="Missing payment fields")
    if plan_id not in ("pro", "elite") or cycle not in ("monthly", "yearly"):
        raise HTTPException(status_code=400, detail="Invalid plan/cycle")

    # HMAC-SHA256 signature verification
    expected = hmac.new(
        RZP_SECRET.encode(), f"{order_id}|{payment_id}".encode(), hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=400, detail="Payment signature verification failed")

    return await _activate_subscription(user, plan_id, cycle, provider="razorpay",
                                        order_id=order_id, payment_id=payment_id)


async def _activate_subscription(user: dict, plan_id: str, cycle: str,
                                  provider: str = "mock", order_id: str = None,
                                  payment_id: str = None) -> dict:
    plan = PLANS[plan_id]
    amount = plan["price_yearly"] if cycle == "yearly" else plan["price_monthly"]
    days = 365 if cycle == "yearly" else 30
    bonus_credits = {"pro": 500, "elite": 2000}.get(plan_id, 0)
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=days)

    await db.subscriptions.update_one(
        {"user_id": user["user_id"]},
        {"$set": {
            "user_id": user["user_id"], "plan": plan_id, "billing_cycle": cycle,
            "status": "active", "amount_inr": amount,
            "started_at": now.isoformat(), "expires_at": expires.isoformat(),
            "payment_provider": provider,
            "payment_order_id": order_id or f"mock_{uuid.uuid4().hex[:12]}",
            "payment_id": payment_id,
            "updated_at": now.isoformat(),
        }}, upsert=True,
    )
    # Top up credits as part of subscription activation
    if bonus_credits:
        await db.users.update_one(
            {"user_id": user["user_id"]},
            {"$inc": {"credits": bonus_credits}},
        )

    return {
        "success": True,
        "message": f"Welcome to NeuraLearn {plan['name']}!",
        "plan": plan_id, "billing_cycle": cycle, "amount_inr": amount,
        "expires_at": expires.isoformat(), "credits_added": bonus_credits,
        "provider": provider,
    }


@router.post("/subscription/subscribe")
async def subscribe(body: SubscribeRequest, request: Request):
    """Legacy/mock subscribe — flips DB record. Used as fallback when Razorpay keys absent."""
    user = await get_current_user(request)
    if body.plan not in ("pro", "elite"):
        raise HTTPException(status_code=400, detail="Plan must be 'pro' or 'elite'")
    if body.billing_cycle not in ("monthly", "yearly"):
        raise HTTPException(status_code=400, detail="billing_cycle must be 'monthly' or 'yearly'")
    return await _activate_subscription(user, body.plan, body.billing_cycle, provider="mock")


@router.post("/subscription/cancel")
async def cancel_subscription(request: Request):
    user = await get_current_user(request)
    await db.subscriptions.update_one(
        {"user_id": user["user_id"]},
        {"$set": {"status": "cancelled", "cancelled_at": datetime.now(timezone.utc).isoformat()}},
    )
    return {"success": True, "message": "Subscription cancelled. You'll keep Pro access until the end of your billing period."}


# ----- Onboarding -----
@router.get("/onboarding/status")
async def onboarding_status(request: Request):
    user = await get_current_user(request)
    data = await db.onboarding.find_one({"user_id": user["user_id"]}, {"_id": 0})
    return {"completed": bool(data), "data": data}


@router.post("/onboarding/submit")
async def submit_onboarding(body: OnboardingSubmit, request: Request):
    user = await get_current_user(request)
    if body.class_level not in [str(i) for i in range(6, 13)]:
        raise HTTPException(status_code=400, detail="class_level must be between 6 and 12")
    if body.learning_style not in {"visual", "quizzes", "explanations", "interactive", "balanced"}:
        raise HTTPException(status_code=400, detail="invalid learning_style")

    now = datetime.now(timezone.utc).isoformat()
    record = {
        "user_id": user["user_id"],
        "name": body.name.strip(),
        "class_level": body.class_level,
        "exam_goal": body.exam_goal.strip(),
        "weak_subjects": body.weak_subjects,
        "learning_style": body.learning_style,
        "completed_at": now,
    }
    await db.onboarding.update_one(
        {"user_id": user["user_id"]},
        {"$set": record},
        upsert=True,
    )
    # Lock user's class_level + flag onboarded
    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {
            "name": body.name.strip(),
            "class_level": body.class_level,
            "exam_goal": body.exam_goal.strip(),
            "weak_subjects": body.weak_subjects,
            "learning_style": body.learning_style,
            "is_onboarded": True,
        }},
    )
    return {"success": True, "message": "Welcome aboard!", "data": record}


@router.put("/users/grade")
async def update_user_grade(body: dict, request: Request):
    """Allow user to change their grade — once every 30 days. Otherwise must submit an appeal."""
    user = await get_current_user(request)
    class_level = str(body.get("class_level", "")).strip()
    if class_level not in [str(i) for i in range(6, 13)]:
        raise HTTPException(status_code=400, detail="class_level must be between 6 and 12")

    # Same grade — no-op
    if class_level == user.get("class_level"):
        return {"success": True, "class_level": class_level, "noop": True}

    # 30-day cooldown
    last_change = user.get("last_grade_change_at")
    if last_change:
        try:
            last_dt = datetime.fromisoformat(last_change)
            if last_dt.tzinfo is None:
                last_dt = last_dt.replace(tzinfo=timezone.utc)
            days_since = (datetime.now(timezone.utc) - last_dt).days
            if days_since < 30:
                days_remaining = 30 - days_since
                raise HTTPException(
                    status_code=429,
                    detail={
                        "code": "GRADE_CHANGE_COOLDOWN",
                        "message": f"You can change your grade again in {days_remaining} day{'s' if days_remaining != 1 else ''}.",
                        "days_remaining": days_remaining,
                        "last_change_at": last_change,
                        "current_class_level": user.get("class_level"),
                    },
                )
        except ValueError:
            pass

    now = datetime.now(timezone.utc).isoformat()
    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {"class_level": class_level, "last_grade_change_at": now}},
    )
    return {"success": True, "class_level": class_level, "last_grade_change_at": now}


@router.get("/users/grade-status")
async def grade_status(request: Request):
    """Returns current class + cooldown info for the Profile UI."""
    user = await get_current_user(request)
    last_change = user.get("last_grade_change_at")
    days_remaining = 0
    can_change = True
    if last_change:
        try:
            last_dt = datetime.fromisoformat(last_change)
            if last_dt.tzinfo is None:
                last_dt = last_dt.replace(tzinfo=timezone.utc)
            days_since = (datetime.now(timezone.utc) - last_dt).days
            if days_since < 30:
                days_remaining = 30 - days_since
                can_change = False
        except ValueError:
            pass
    return {
        "class_level": user.get("class_level"),
        "last_grade_change_at": last_change,
        "can_change": can_change,
        "days_remaining": days_remaining,
    }


@router.post("/users/grade-appeal")
async def grade_appeal(body: dict, request: Request):
    """Submit an early grade change request (when cooldown is active)."""
    user = await get_current_user(request)
    desired_class = str(body.get("desired_class", "")).strip()
    reason = str(body.get("reason", "")).strip()
    if desired_class not in [str(i) for i in range(6, 13)]:
        raise HTTPException(status_code=400, detail="desired_class must be between 6 and 12")
    if len(reason) < 10:
        raise HTTPException(status_code=400, detail="Please share a brief reason (at least 10 characters)")

    # Reject duplicate pending appeals
    existing = await db.grade_change_requests.find_one(
        {"user_id": user["user_id"], "status": "pending"}, {"_id": 0}
    )
    if existing:
        raise HTTPException(status_code=409, detail="You already have a pending grade-change request. Please wait for it to be reviewed.")

    record = {
        "user_id": user["user_id"],
        "user_email": user.get("email"),
        "user_name": user.get("name"),
        "current_class": user.get("class_level"),
        "desired_class": desired_class,
        "reason": reason,
        "status": "pending",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.grade_change_requests.insert_one(record)
    record.pop("_id", None)
    return {"success": True, "message": "Your request has been submitted to our team. You'll hear back within 48 hours.", "request": record}


@router.get("/users/grade-appeal")
async def get_my_grade_appeal(request: Request):
    """Returns the user's most recent grade-change request."""
    user = await get_current_user(request)
    req = await db.grade_change_requests.find_one(
        {"user_id": user["user_id"]}, {"_id": 0}, sort=[("submitted_at", -1)],
    )
    return {"request": req}
