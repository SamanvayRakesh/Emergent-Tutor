"""Feedback routes — users submit feedback, admins view and reply."""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from core import db, get_current_user

router = APIRouter()


class FeedbackBody(BaseModel):
    type: str = "general"   # bug | suggestion | general
    message: str


class ReplyBody(BaseModel):
    reply: str


@router.post("/feedback")
async def submit_feedback(body: FeedbackBody, request: Request):
    user = await get_current_user(request)
    if not body.message or len(body.message.strip()) < 5:
        raise HTTPException(status_code=400, detail="Feedback message is too short.")
    doc = {
        "feedback_id": f"fb_{uuid.uuid4().hex[:12]}",
        "user_id": user["user_id"],
        "user_name": user.get("name", "Unknown"),
        "user_email": user.get("email", ""),
        "type": body.type,
        "message": body.message.strip()[:2000],
        "status": "open",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.feedback.insert_one(doc)
    return {"success": True, "message": "Thank you! Your feedback has been submitted."}


@router.get("/feedback/my-feedback")
async def get_my_feedback(request: Request):
    """Return current user's own feedback items (with admin replies if any)."""
    user = await get_current_user(request)
    items = await db.feedback.find(
        {"user_id": user["user_id"]}, {"_id": 0}
    ).sort("created_at", -1).limit(20).to_list(20)
    return {"feedback": items}


@router.get("/admin/feedback")
async def admin_get_feedback(request: Request):
    from routes.admin import _require_admin
    await _require_admin(request)
    items = await db.feedback.find({}, {"_id": 0}).sort("created_at", -1).limit(200).to_list(200)
    return {"feedback": items, "total": len(items)}


@router.patch("/admin/feedback/{feedback_id}/resolve")
async def admin_resolve_feedback(feedback_id: str, request: Request):
    from routes.admin import _require_admin
    await _require_admin(request)
    result = await db.feedback.update_one(
        {"feedback_id": feedback_id},
        {"$set": {"status": "resolved", "resolved_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return {"success": True}


@router.post("/admin/feedback/{feedback_id}/reply")
async def admin_reply_feedback(feedback_id: str, body: ReplyBody, request: Request):
    """Admin replies to a feedback item. Stored in the feedback doc and visible to the user."""
    from routes.admin import _require_admin
    admin = await _require_admin(request)
    if not body.reply or not body.reply.strip():
        raise HTTPException(status_code=400, detail="Reply cannot be empty.")
    result = await db.feedback.update_one(
        {"feedback_id": feedback_id},
        {"$set": {
            "admin_reply": body.reply.strip()[:2000],
            "replied_at": datetime.now(timezone.utc).isoformat(),
            "replied_by": admin.get("name", "Admin"),
            "status": "resolved",
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return {"success": True}
