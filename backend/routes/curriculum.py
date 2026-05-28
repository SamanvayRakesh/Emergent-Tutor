"""Curriculum API — verified NCERT chapter data with source URLs + verification timestamps."""
import asyncio
import os
import subprocess

from fastapi import APIRouter, HTTPException, Request

from curriculum_engine import (
    get_curriculum_meta, get_verified_chapters, get_verified_book_sources,
    load_curriculum_from_json,
)
from core import get_current_user
from cbse_data import get_classes, get_subjects, get_chapters, get_subject_meta

router = APIRouter()


@router.get("/curriculum/status")
async def curriculum_status():
    """Engine status — coverage info + last verification timestamp."""
    return get_curriculum_meta()


@router.post("/curriculum/refresh")
async def curriculum_refresh(request: Request):
    """Admin-triggered refresh — re-runs the NCERT scraper and reloads curriculum."""
    user = await get_current_user(request)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    # Run scraper in background; return immediately
    script = "/app/backend/scripts/ncert_scraper.py"

    async def _bg():
        proc = await asyncio.create_subprocess_exec(
            "python", script,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        await proc.wait()
        await load_curriculum_from_json()

    asyncio.create_task(_bg())
    return {"message": "Scraper started — curriculum will reload when complete", "status": "running"}


@router.get("/curriculum/classes")
async def curriculum_classes():
    """All available classes (verified data first, then legacy fallback)."""
    meta = get_curriculum_meta()
    verified_classes = set(meta.get("classes_covered", []))
    all_classes = sorted(set(get_classes()) | verified_classes, key=lambda x: int(x) if x.isdigit() else 99)
    return [{"id": c, "name": f"Class {c}", "verified": c in verified_classes} for c in all_classes]


@router.get("/curriculum/{class_id}/subjects")
async def curriculum_subjects(class_id: str):
    """Subjects for a class, with verification flag per subject."""
    meta = get_curriculum_meta()
    verified_subjects = set(meta.get("subjects_per_class", {}).get(class_id, []))
    legacy_subjects = get_subjects(class_id) or []
    seen = set()
    result = []

    for s in legacy_subjects:
        norm = s.lower().replace(" ", "_")
        seen.add(norm)
        m = get_subject_meta(class_id, s)
        legacy_chapters = get_chapters(class_id, s)
        result.append({
            "name": s,
            "icon": m["icon"],
            "color": m["color"],
            "chapter_count": len(get_verified_chapters(class_id, s) or legacy_chapters or []),
            "verified": norm in verified_subjects,
        })

    # Add verified-only subjects that didn't appear in legacy data
    for vs in verified_subjects:
        if vs not in seen:
            display_name = vs.replace("_", " ").title()
            result.append({
                "name": display_name, "icon": "BookOpen", "color": "#94a3b8",
                "chapter_count": len(get_verified_chapters(class_id, vs) or []),
                "verified": True,
            })

    return result


@router.get("/curriculum/{class_id}/{subject}/chapters")
async def curriculum_chapters(class_id: str, subject: str):
    """Chapter list for a subject — verified NCERT data when available, legacy fallback otherwise."""
    from urllib.parse import unquote
    subject = unquote(subject)

    verified = get_verified_chapters(class_id, subject)
    if verified:
        return {
            "chapters": verified,
            "verified": True,
            "books": get_verified_book_sources(class_id, subject),
            "academic_year": get_curriculum_meta().get("academic_year"),
            "source": "ncert.nic.in (official NCERT textbook PDFs)",
        }

    legacy = get_chapters(class_id, subject)
    if legacy is None:
        raise HTTPException(status_code=404, detail="Subject not found")
    return {
        "chapters": [{"id": ch.get("id", f"legacy-{i}"), "name": ch.get("name", ""), "order": i + 1, "verified": False, **ch}
                     for i, ch in enumerate(legacy)],
        "verified": False,
        "books": [],
        "academic_year": None,
        "source": "legacy hardcoded fallback (pending NCERT verification)",
    }


@router.get("/curriculum/verify/{class_id}/{subject}")
async def curriculum_verify(class_id: str, subject: str):
    """Per-subject verification details — source URLs + scraped_at timestamp."""
    from urllib.parse import unquote
    subject = unquote(subject)
    chapters = get_verified_chapters(class_id, subject)
    if not chapters:
        return {"verified": False, "reason": "not yet ingested from NCERT"}
    return {
        "verified": True,
        "class_level": class_id,
        "subject": subject,
        "academic_year": get_curriculum_meta().get("academic_year"),
        "scraped_at": get_curriculum_meta().get("scraped_at"),
        "source": "ncert.nic.in (official NCERT textbook PDFs)",
        "books": get_verified_book_sources(class_id, subject),
        "chapter_count": len(chapters),
    }
