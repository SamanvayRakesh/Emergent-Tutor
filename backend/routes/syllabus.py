"""Syllabus + progress routes. Delegates to verified NCERT engine when available."""
from datetime import datetime, timezone
from urllib.parse import unquote

from fastapi import APIRouter, HTTPException, Request

from core import db, get_current_user
from models import ProgressUpdate
from learning_evidence import evidence_records, chapter_mastery, learning_scope
from cbse_data import get_classes, get_subjects, get_chapters, get_subject_meta
from curriculum_engine import (
    get_curriculum_meta, get_verified_chapters, get_verified_book_sources,
)
from school_curriculum import has_school_curriculum, get_school_subjects, get_school_chapters

router = APIRouter()


def _verified_classes():
    return set(get_curriculum_meta().get("classes_covered", []))


# ----- Syllabus -----
@router.get("/syllabus/classes")
async def get_all_classes():
    verified = _verified_classes()
    legacy = set(get_classes())
    all_cls = sorted(verified | legacy, key=lambda x: int(x) if x.isdigit() else 99)
    return [{"id": c, "name": f"Class {c}", "verified": c in verified} for c in all_cls]


SUBJ_META = {
    "mathematics": {"display": "Mathematics", "icon": "Calculator", "color": "#22d3ee"},
    "science": {"display": "Science", "icon": "Atom", "color": "#8b5cf6"},
    "english": {"display": "English", "icon": "Book", "color": "#f59e0b"},
    "social_science": {"display": "Social Science", "icon": "Globe", "color": "#3b82f6"},
}


@router.get("/syllabus/{class_id}/subjects")
async def get_class_subjects(class_id: str, request: Request):
    # Check if the logged-in user has a school with a custom curriculum for this grade
    try:
        user = await get_current_user(request)
        school_id = user.get("school")
        if school_id and has_school_curriculum(school_id, class_id):
            return get_school_subjects(school_id, class_id)
    except Exception:
        pass  # unauthenticated → fall through to NCERT

    meta = get_curriculum_meta()
    verified_subj_keys = set(meta.get("subjects_per_class", {}).get(class_id, []))

    result = []
    seen = set()

    for subj_key in verified_subj_keys:
        info = SUBJ_META.get(subj_key, {"display": subj_key.title(), "icon": "BookOpen", "color": "#94a3b8"})
        chapters = get_verified_chapters(class_id, info["display"]) or []
        seen.add(info["display"].lower())
        result.append({
            "name": info["display"], "icon": info["icon"], "color": info["color"],
            "chapter_count": len(chapters), "verified": True,
        })

    legacy_subjects = get_subjects(class_id) or []
    for s in legacy_subjects:
        if s.lower() in seen:
            continue
        m = get_subject_meta(class_id, s)
        legacy_chapters = get_chapters(class_id, s) or []
        result.append({
            "name": s, "icon": m["icon"], "color": m["color"],
            "chapter_count": len(legacy_chapters), "verified": False,
        })

    if not result:
        raise HTTPException(status_code=404, detail="Class not found")
    return result


@router.get("/syllabus/{class_id}/{subject}/chapters")
async def get_subject_chapters(class_id: str, subject: str, request: Request):
    subject = unquote(subject)

    # School-specific chapters take priority over NCERT
    try:
        user = await get_current_user(request)
        school_id = user.get("school")
        if school_id and has_school_curriculum(school_id, class_id):
            school_chapters = get_school_chapters(school_id, class_id, subject)
            if school_chapters:
                return school_chapters
    except Exception:
        pass  # unauthenticated → fall through

    verified = get_verified_chapters(class_id, subject)
    if verified:
        ay = get_curriculum_meta().get("academic_year")
        return [
            {
                "id": c["id"], "name": c["name"], "order": c["order"],
                "chapter_no": c.get("chapter_no"),
                "verified": True,
                "book_title": c.get("book_title"),
                "_meta": {"academic_year": ay, "source": "ncert.nic.in"},
            }
            for c in verified
        ]

    legacy = get_chapters(class_id, subject)
    if legacy is None:
        raise HTTPException(status_code=404, detail="Subject not found")
    return [{**ch, "verified": False} for ch in legacy]


# ----- Progress -----
@router.get("/progress")
async def get_progress(request: Request):
    user = await get_current_user(request)
    records = await evidence_records(user)

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
    if body.class_level != user.get("class_level"):
        raise HTTPException(status_code=403, detail="This chapter is outside your active course.")
    # Visiting a chapter records activity, never awards unassessed mastery.
    now = datetime.now(timezone.utc).isoformat()
    measured = await chapter_mastery(user, body.chapter_name, body.subject)
    scope = learning_scope(user)
    await db.progress.update_one(
        {**scope, "chapter_id": body.chapter_id},
        {"$set": {"subject": body.subject, "chapter_name": body.chapter_name,
                  "mastery": measured["mastery_pct"], "updated_at": now},
         "$setOnInsert": {"created_at": now}}, upsert=True,
    )
    return {"message": "Progress updated", "mastery": measured["mastery_pct"]}
