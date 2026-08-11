"""Admin routes: leaderboard management, grade change requests, earnings."""
import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from core import db, get_current_user, logger

router = APIRouter()

ADMIN_EMAILS = {
    "taniknpoojari@gmail.com",
    "truecursemahito28@gmail.com",
    "samanvayrakesh7@gmail.com",
}


async def _require_admin(request: Request) -> dict:
    user = await get_current_user(request)
    is_admin = (
        user.get("email", "").lower() in ADMIN_EMAILS
        or user.get("role") == "admin"
    )
    if not is_admin:
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

PLAN_PRICES = {"starter": 399, "pro": 699}

@router.get("/admin/earnings")
async def admin_get_earnings(request: Request):
    """Real earnings data from PayU orders + subscriptions."""
    await _require_admin(request)

    now     = datetime.now(timezone.utc)
    now_iso = now.isoformat()

    # ── Subscription state ───────────────────────────────────────────────────
    # All subscriptions still within their paid period (active OR cancelled-but-not-expired)
    all_paid_subs = await db.subscriptions.find(
        {"expires_at": {"$gt": now_iso}},
        {"_id": 0}
    ).to_list(10000)

    active_subs    = [s for s in all_paid_subs if s.get("status") == "active"]
    cancelled_subs = [s for s in all_paid_subs if s.get("status") == "cancelled"]

    active_starter    = sum(1 for s in active_subs if s.get("plan") == "starter")
    active_pro        = sum(1 for s in active_subs if s.get("plan") == "pro")
    cancelled_starter = sum(1 for s in cancelled_subs if s.get("plan") == "starter")
    cancelled_pro     = sum(1 for s in cancelled_subs if s.get("plan") == "pro")
    total_paid_users  = len(all_paid_subs)

    # MRR = only truly active (will auto-renew) subscriptions
    mrr = active_starter * PLAN_PRICES["starter"] + active_pro * PLAN_PRICES["pro"]

    # ── PayU payment history ─────────────────────────────────────────────────
    payu_payments = await db.payu_orders.find(
        {"status": "paid"},
        {"_id": 0}
    ).sort("created_at", -1).limit(100).to_list(100)

    # Enrich payments with user info
    uid_set  = list({p["user_id"] for p in payu_payments if p.get("user_id")})
    users_raw = await db.users.find(
        {"user_id": {"$in": uid_set}},
        {"_id": 0, "user_id": 1, "name": 1, "email": 1}
    ).to_list(len(uid_set) + 1)
    user_map = {u["user_id"]: u for u in users_raw}

    enriched = []
    for p in payu_payments:
        u = user_map.get(p.get("user_id", ""), {})
        try:
            amt = float(p.get("amount", 0))
        except (ValueError, TypeError):
            amt = 0.0
        enriched.append({
            "txnid":       p.get("txnid", ""),
            "user_name":   u.get("name", "Unknown"),
            "user_email":  u.get("email", ""),
            "plan":        p.get("plan", ""),
            "amount":      amt,
            "status":      p.get("status", ""),
            "created_at":  p.get("created_at", ""),
            "mihpayid":    p.get("mihpayid", ""),
        })

    # Monthly revenue breakdown
    monthly: dict = {}
    for p in enriched:
        month = (p.get("created_at") or "")[:7]
        if month:
            monthly[month] = round(monthly.get(month, 0.0) + p["amount"], 2)

    total_revenue = round(sum(p["amount"] for p in enriched), 2)

    # Fallback: if no PayU orders exist yet, sum amount_inr from subscriptions so revenue isn't 0
    if total_revenue == 0 and all_paid_subs:
        total_revenue = round(sum(float(s.get("amount_inr") or 0) for s in all_paid_subs), 2)

    # ── All-time total users ─────────────────────────────────────────────────
    total_users = await db.users.count_documents({"role": {"$ne": "admin"}})

    # ── Paid users list (with subscription details) ──────────────────────────
    paid_user_ids = [s.get("user_id") for s in all_paid_subs]
    paid_users_raw = await db.users.find(
        {"user_id": {"$in": paid_user_ids}},
        {"_id": 0, "user_id": 1, "name": 1, "email": 1, "created_at": 1}
    ).to_list(len(paid_user_ids) + 1)
    paid_user_detail_map = {u["user_id"]: u for u in paid_users_raw}

    paid_users_list = []
    for s in all_paid_subs:
        u = paid_user_detail_map.get(s.get("user_id", ""), {})
        paid_users_list.append({
            "user_id":    s.get("user_id"),
            "name":       u.get("name", "Unknown"),
            "email":      u.get("email", ""),
            "plan":       s.get("plan", ""),
            "status":     s.get("status", ""),
            "expires_at": s.get("expires_at", ""),
            "started_at": s.get("started_at", ""),
            "amount_inr": s.get("amount_inr", 0),
        })
    paid_users_list.sort(key=lambda x: x.get("started_at", ""), reverse=True)

    return {
        "total_users":          total_users,
        "total_paid_users":     total_paid_users,
        "total_revenue_inr":    total_revenue,
        "mrr_inr":              mrr,
        "plan_distribution": {
            "free":     total_users - total_paid_users,
            "starter":  active_starter + cancelled_starter,
            "pro":      active_pro + cancelled_pro,
        },
        "active_subscriptions": {
            "starter":  active_starter,
            "pro":      active_pro,
        },
        "cancelled_subscriptions": {
            "starter":  cancelled_starter,
            "pro":      cancelled_pro,
        },
        "recent_payments":  enriched[:20],
        "monthly_revenue":  monthly,
        "paid_users":       paid_users_list,
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


# ── Bulk credit reset ──────────────────────────────────────────────────────────

class ResetCreditsRequest(BaseModel):
    amount: int = 100
    exclude_names: List[str] = []   # case-insensitive name fragments to preserve
    exclude_emails: List[str] = []  # exact emails to preserve
    exclude_user_ids: List[str] = []

@router.post("/admin/reset-credits")
async def admin_reset_credits(body: ResetCreditsRequest, request: Request):
    """
    Reset every non-admin user's credits to `amount` (default 100).
    Accounts matching any exclude_names / exclude_emails / exclude_user_ids are left untouched.
    """
    await _require_admin(request)

    # Always exclude admins
    exclude_emails_lower = {e.lower() for e in body.exclude_emails}
    exclude_uids         = set(body.exclude_user_ids)
    exclude_name_frags   = [n.lower() for n in body.exclude_names]

    # Fetch all non-admin users
    all_users = await db.users.find(
        {"role": {"$ne": "admin"}},
        {"user_id": 1, "email": 1, "name": 1, "credits": 1, "_id": 0}
    ).to_list(10000)

    reset_ids, skipped = [], []
    for u in all_users:
        uid   = u.get("user_id", "")
        email = (u.get("email") or "").lower()
        name  = (u.get("name")  or "").lower()

        # Check exclusions
        if uid in exclude_uids:
            skipped.append(uid); continue
        if email in exclude_emails_lower:
            skipped.append(uid); continue
        if any(frag in name for frag in exclude_name_frags):
            skipped.append(uid); continue

        reset_ids.append(uid)

    if reset_ids:
        await db.users.update_many(
            {"user_id": {"$in": reset_ids}},
            {"$set": {"credits": body.amount}},
        )

    logger.info(f"Admin credit reset: {len(reset_ids)} users → {body.amount} credits, {len(skipped)} skipped")
    return {
        "success":      True,
        "reset_count":  len(reset_ids),
        "skipped_count": len(skipped),
        "skipped_ids":  skipped,
        "new_amount":   body.amount,
    }