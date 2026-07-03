"""Admin routes: leaderboard management, grade change requests, earnings."""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from core import db, get_current_user, logger

router = APIRouter()

ADMIN_EMAILS = {
    "taniknpoojari@gmail.com",
    "truecursemahito28@gmail.com",
    "samanvayrakesh7@gmail.com",
}


async def _require_admin(request: Request) -> dict:
    user = await get_current_user(request)
    if user.get("email", "").lower() not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# ── Leaderboard management ────────────────────────────────────────────────────

@router.get("/admin/leaderboard/users")
async def admin_list_leaderboard_users(request: Request):
    """List all users with leaderboard visibility status."""
    await _require_admin(request)
    users = await db.users.find(
        {"role": {"$ne": "admin"}},
        {"_id": 0, "user_id": 1, "name": 1, "email": 1, "xp": 1,
         "class_level": 1, "hide_from_leaderboard": 1, "school": 1, "created_at": 1}
    ).sort("xp", -1).limit(200).to_list(200)
    return {"users": users, "total": len(users)}


@router.post("/admin/leaderboard/hide/{user_id}")
async def admin_hide_from_leaderboard(user_id: str, request: Request):
    """Toggle hide/show a user on the leaderboard."""
    await _require_admin(request)
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "hide_from_leaderboard": 1})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    hidden = not user.get("hide_from_leaderboard", False)
    await db.users.update_one({"user_id": user_id}, {"$set": {"hide_from_leaderboard": hidden}})
    action = "hidden from" if hidden else "shown on"
    return {"success": True, "message": f"User {action} leaderboard", "hidden": hidden}


# ── Grade change requests ─────────────────────────────────────────────────────

@router.get("/admin/grade-requests")
async def admin_get_grade_requests(request: Request):
    """List all grade change requests."""
    await _require_admin(request)
    requests = await db.grade_change_requests.find(
        {}, {"_id": 0}
    ).sort("created_at", -1).limit(100).to_list(100)
    return {"requests": requests, "total": len(requests)}


@router.post("/admin/grade-requests/{request_id}/resolve")
async def admin_resolve_grade_request(request_id: str, request: Request, body: dict = {}):
    """Approve or deny a grade change request. Body: {action: 'approve'|'deny'}"""
    await _require_admin(request)
    action = (body.get("action") or "approve").lower()
    if action not in ("approve", "deny"):
        raise HTTPException(status_code=400, detail="action must be 'approve' or 'deny'")

    req = await db.grade_change_requests.find_one({"request_id": request_id}, {"_id": 0})
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    if action == "approve":
        # Support both field name conventions
        target_class = req.get("new_class") or req.get("desired_class")
        if target_class:
            await db.users.update_one(
                {"user_id": req["user_id"]},
                {"$set": {"class_level": target_class, "last_grade_change_at": datetime.now(timezone.utc).isoformat()}}
            )

    await db.grade_change_requests.update_one(
        {"request_id": request_id},
        {"$set": {"status": action + "d", "resolved_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"success": True, "message": f"Grade change request {action}d"}


# ── Earnings dashboard ────────────────────────────────────────────────────────

@router.get("/admin/earnings")
async def admin_get_earnings(request: Request):
    """Total earnings overview from subscription data."""
    await _require_admin(request)

    total_users = await db.users.count_documents({"role": {"$ne": "admin"}})
    
    # Count by plan
    plan_pipeline = [
        {"$match": {"role": {"$ne": "admin"}}},
        {"$group": {"_id": "$plan", "count": {"$sum": 1}}}
    ]
    plan_counts = {r["_id"]: r["count"] async for r in db.users.aggregate(plan_pipeline)}
    
    # Subscription payments
    payments = await db.subscription_payments.find(
        {}, {"_id": 0}
    ).sort("created_at", -1).limit(50).to_list(50)
    
    # Revenue totals (in INR)
    PLAN_PRICES = {"starter": 199, "pro": 499}
    total_revenue = sum(p.get("amount", 0) for p in payments)
    
    # Monthly breakdown from payments
    monthly = {}
    for p in payments:
        try:
            month = p.get("created_at", "")[:7]  # YYYY-MM
            monthly[month] = monthly.get(month, 0) + p.get("amount", 0)
        except Exception:
            pass
    
    # Estimated MRR (mock calculation based on active subscriptions)
    starter_count = plan_counts.get("starter", 0)
    pro_count = plan_counts.get("pro", 0)
    mrr = starter_count * 199 + pro_count * 499

    return {
        "total_users": total_users,
        "plan_distribution": {
            "free": plan_counts.get(None, 0) + plan_counts.get("free", 0),
            "starter": starter_count,
            "pro": pro_count,
        },
        "total_revenue_inr": total_revenue,
        "estimated_mrr_inr": mrr,
        "recent_payments": payments[:20],
        "monthly_revenue": monthly,
    }


# ── All users overview ────────────────────────────────────────────────────────

@router.get("/admin/users")
async def admin_get_users(request: Request):
    """List all registered users."""
    await _require_admin(request)
    users = await db.users.find(
        {}, {"_id": 0, "password_hash": 0, "verification_token": 0}
    ).sort("created_at", -1).limit(500).to_list(500)
    return {"users": users, "total": len(users)}
