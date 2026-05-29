"""Subscription + onboarding routes."""
import uuid
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, HTTPException, Request

from core import db, get_current_user
from models import OnboardingSubmit, SubscribeRequest
from plan_gates import PLANS, get_user_plan, get_usage

router = APIRouter()


# ----- Plan catalog -----
@router.get("/subscription/plans")
async def list_plans():
    """Public catalog of all plans."""
    return {"plans": list(PLANS.values())}


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


@router.post("/subscription/subscribe")
async def subscribe(body: SubscribeRequest, request: Request):
    """Mocked subscribe — flips DB record. Razorpay integration drops in here later."""
    user = await get_current_user(request)
    if body.plan not in ("pro", "elite"):
        raise HTTPException(status_code=400, detail="Plan must be 'pro' or 'elite'")
    if body.billing_cycle not in ("monthly", "yearly"):
        raise HTTPException(status_code=400, detail="billing_cycle must be 'monthly' or 'yearly'")

    plan = PLANS[body.plan]
    amount = plan["price_yearly"] if body.billing_cycle == "yearly" else plan["price_monthly"]
    days = 365 if body.billing_cycle == "yearly" else 30
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=days)

    # MOCKED PAYMENT — Razorpay order would be created here
    mock_order_id = f"mock_order_{uuid.uuid4().hex[:12]}"

    await db.subscriptions.update_one(
        {"user_id": user["user_id"]},
        {"$set": {
            "user_id": user["user_id"],
            "plan": body.plan,
            "billing_cycle": body.billing_cycle,
            "status": "active",
            "amount_inr": amount,
            "started_at": now.isoformat(),
            "expires_at": expires.isoformat(),
            "payment_provider": "mock",
            "payment_order_id": mock_order_id,
            "updated_at": now.isoformat(),
        }},
        upsert=True,
    )
    return {
        "success": True,
        "message": f"Welcome to NeuraLearn {plan['name']}!",
        "plan": body.plan,
        "billing_cycle": body.billing_cycle,
        "amount_inr": amount,
        "expires_at": expires.isoformat(),
        "mock_order_id": mock_order_id,
    }


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
