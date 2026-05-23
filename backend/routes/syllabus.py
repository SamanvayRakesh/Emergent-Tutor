"""Syllabus + progress routes."""
from datetime import datetime, timezone
from urllib.parse import unquote

from fastapi import APIRouter, HTTPException, Request

from core import db, get_current_user
from models import ProgressUpdate
from cbse_data import get_classes, get_subjects, get_chapters, get_subject_meta

router = APIRouter()


# ----- Syllabus -----
@router.get("/syllabus/classes")
async def get_all_classes():
    return [{"id": c, "name": f"Class {c}"} for c in get_classes()]


@router.get("/syllabus/{class_id}/subjects")
async def get_class_subjects(class_id: str):
    subjects = get_subjects(class_id)
    if not subjects:
        raise HTTPException(status_code=404, detail="Class not found")
    result = []
    for s in subjects:
        meta = get_subject_meta(class_id, s)
        chapters = get_chapters(class_id, s)
        result.append({"name": s, "icon": meta["icon"], "color": meta["color"], "chapter_count": len(chapters)})
    return result


@router.get("/syllabus/{class_id}/{subject}/chapters")
async def get_subject_chapters(class_id: str, subject: str):
    subject = unquote(subject)
    chapters = get_chapters(class_id, subject)
    if chapters is None:
        raise HTTPException(status_code=404, detail="Subject not found")
    return chapters


# ----- Progress -----
@router.get("/progress")
async def get_progress(request: Request):
    user = await get_current_user(request)
    records = await db.progress.find({"user_id": user["user_id"]}, {"_id": 0}).to_list(200)

    subject_progress = {}
    for rec in records:
        subj = rec.get("subject", "")
        sp = subject_progress.setdefault(subj, {"chapters": 0, "total_mastery": 0, "weak_topics": []})
        sp["chapters"] += 1
        sp["total_mastery"] += rec.get("mastery", 0)
        if rec.get("mastery", 0) < 40:
            sp["weak_topics"].append(rec.get("chapter_name", ""))

    for sp in subject_progress.values():
        sp["avg_mastery"] = sp["total_mastery"] // sp["chapters"] if sp["chapters"] else 0

    total_mastery = sum(r.get("mastery", 0) for r in records)
    avg_overall = total_mastery // len(records) if records else 0
    return {
        "overall_mastery": avg_overall,
        "total_chapters_studied": len(records),
        "subject_progress": subject_progress,
        "recent_progress": records[-10:] if records else [],
    }


@router.post("/progress/update")
async def update_progress(body: ProgressUpdate, request: Request):
    user = await get_current_user(request)
    existing = await db.progress.find_one(
        {"user_id": user["user_id"], "chapter_id": body.chapter_id}, {"_id": 0}
    )
    now = datetime.now(timezone.utc).isoformat()
    if existing:
        new_mastery = min(100, existing.get("mastery", 0) + body.mastery_delta)
        await db.progress.update_one(
            {"user_id": user["user_id"], "chapter_id": body.chapter_id},
            {"$set": {"mastery": new_mastery, "updated_at": now}},
        )
    else:
        await db.progress.insert_one({
            "user_id": user["user_id"],
            "class_level": body.class_level, "subject": body.subject,
            "chapter_id": body.chapter_id, "chapter_name": body.chapter_name,
            "mastery": min(100, body.mastery_delta),
            "created_at": now, "updated_at": now,
        })
    return {"message": "Progress updated"}
