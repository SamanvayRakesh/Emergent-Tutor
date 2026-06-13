"""Curriculum engine — reads verified NCERT chapter manifests from ncert_ai_metadata.json.

This is the canonical syllabus source for the platform. Every chapter exposed by this
module carries verification metadata (NCERT book code, PDF source URL, scrape timestamp)
so the UI can show "Verified ✓" badges and the AI tutor can be grounded.
"""
import json
import os
import re
from datetime import datetime, timezone
from typing import Optional

from core import db, logger
import cbse_data as _cbse

METADATA_JSON = "/app/backend/curriculum_data/ncert_ai_ready/ncert_ai_metadata.json"
BOOKS_JSON = "/app/backend/curriculum_data/ncert_books.json"

# In-memory cache. Shape:
# { "10": { "mathematics": {
#     "books": [{book_title, book_code, chapters: [...]}],
#     "chapters": [{id, name, order, verified, pdf_url, book_title, book_code}],
#     "verified": True
# }}}
_CACHE: dict = {}
_LOAD_META: dict = {"loaded": False, "source": None, "academic_year": None, "scraped_at": None, "books": 0}


def _normalize_subject(name: str) -> str:
    n = (name or "").lower().strip().replace(" ", "_")
    aliases = {
        "math": "mathematics", "maths": "mathematics", "ganita": "mathematics",
        "social": "social_science", "sst": "social_science",
        "social_studies": "social_science",
    }
    return aliases.get(n, n)


def _denormalize_subject(key: str) -> str:
    """Pretty label for UI."""
    return {"social_science": "Social Science"}.get(key, key.replace("_", " ").title())


def _is_generic_title(title: str) -> bool:
    return bool(re.fullmatch(r"chapter\s+\d+", (title or "").strip(), re.IGNORECASE))


def _clean_chapter_title(raw: str, fallback_no: int, cls: str = "", subj: str = "") -> str:
    """Strip junk; cross-reference cbse_data for generic 'Chapter N' fallbacks."""
    if not raw or _is_generic_title(raw):
        if cls and subj:
            chapters = _cbse.get_chapters(cls, subj) or []
            idx = fallback_no - 1
            if 0 <= idx < len(chapters):
                return chapters[idx]["name"]
        return f"Chapter {fallback_no}"
    cleaned = re.sub(r"\s+", " ", raw).strip()
    return cleaned


async def load_curriculum_from_json():
    """Load ncert_ai_metadata.json into memory + MongoDB. Idempotent — safe to re-run."""
    if not os.path.exists(METADATA_JSON):
        logger.info("ncert_ai_metadata.json not present yet; curriculum engine in fallback mode")
        return

    try:
        with open(METADATA_JSON, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception as e:
        logger.warning(f"ncert_ai_metadata.json unreadable: {e}")
        return

    books = payload.get("books", []) or []
    if not books:
        logger.warning("Metadata file has no books — scraper output empty")
        return

    academic_year = payload.get("academic_year", "2025-26")
    source = payload.get("source", "ncert.nic.in")
    scraped_at = payload.get("scraped_at", datetime.now(timezone.utc).isoformat())

    _LOAD_META.update({
        "loaded": True, "source": source,
        "academic_year": academic_year, "scraped_at": scraped_at,
        "books": len(books),
    })

    # Merge multiple books per (class, subject) — e.g. Class 12 Math has Part 1 + Part 2
    grouped: dict = {}
    for book in books:
        cls = str(book.get("class", "")).strip()
        subj_raw = book.get("subject", "")
        subj = _normalize_subject(subj_raw)
        if not cls or not subj:
            continue
        key = (cls, subj)
        grouped.setdefault(key, []).append(book)

    docs_written = 0
    for (cls, subj), book_list in grouped.items():
        merged_chapters = []
        books_meta = []
        running_order = 0
        for book in book_list:
            book_title = book.get("book_title", "")
            book_code = book.get("book_code", "")
            books_meta.append({"book_title": book_title, "book_code": book_code})
            for ch in book.get("chapters", []):
                # Skip 'prelims' / table-of-contents entries from chapter list
                if ch.get("id") == "prelims" or ch.get("chapter_no") is None:
                    continue
                running_order += 1
                ch_no = ch.get("chapter_no", running_order)
                title = _clean_chapter_title(ch.get("title", ""), ch_no, cls, _denormalize_subject(subj))
                merged_chapters.append({
                    "id": f"{cls}-{subj}-{running_order}",
                    "name": title,
                    "order": running_order,
                    "chapter_no": ch_no,
                    "book_title": book_title,
                    "book_code": book_code,
                    "pdf_url": ch.get("pdf_url"),
                    "verified": True,
                })

        doc = {
            "class_level": cls, "subject": subj,
            "subject_display": _denormalize_subject(subj),
            "academic_year": academic_year, "source": source,
            "books": books_meta, "chapters": merged_chapters,
            "verified": True, "verified_at": scraped_at,
        }
        _CACHE.setdefault(cls, {})[subj] = doc

        await db.curriculum.update_one(
            {"class_level": cls, "subject": subj, "academic_year": academic_year},
            {"$set": doc}, upsert=True,
        )
        docs_written += 1

    logger.info(f"Curriculum engine loaded: {docs_written} class-subject manifests from {len(books)} NCERT books ({academic_year})")


def get_verified_chapters(class_level: str, subject: str) -> Optional[list]:
    """Return verified chapter list for class+subject, or None if not verified."""
    cls_data = _CACHE.get(str(class_level))
    if not cls_data:
        return None
    entry = cls_data.get(_normalize_subject(subject))
    if not entry:
        return None
    return entry.get("chapters")


def get_curriculum_meta() -> dict:
    classes_covered = sorted(_CACHE.keys(), key=lambda x: int(x) if x.isdigit() else 99)
    subjects_per_class = {c: sorted(_CACHE[c].keys()) for c in classes_covered}
    return {
        **_LOAD_META,
        "classes_covered": classes_covered,
        "subjects_per_class": subjects_per_class,
    }


def get_verified_book_sources(class_level: str, subject: str) -> list:
    cls_data = _CACHE.get(str(class_level))
    if not cls_data:
        return []
    entry = cls_data.get(_normalize_subject(subject))
    if not entry:
        return []
    return entry.get("books", [])


def build_ai_chapter_manifest(class_level: str, subject: str) -> str:
    """AI grounding manifest — injected into the tutor's system prompt."""
    chapters = get_verified_chapters(class_level, subject)
    if not chapters:
        return ""
    names = [c["name"] for c in chapters[:30]]
    return (
        "\n═══════ VERIFIED NCERT CHAPTER MANIFEST ═══════\n"
        f"Class {class_level} · {subject} · official NCERT textbook chapters (academic year {_LOAD_META.get('academic_year','2025-26')}):\n"
        + "\n".join(f"  {i+1}. {n}" for i, n in enumerate(names))
        + "\n\nGROUNDING RULE: If a student asks about a topic NOT on this list, "
          "you MUST prefix your answer with: 'Note: this topic isn't in the official "
          f"Class {class_level} {subject} NCERT chapters — sharing it for context only.' "
          "NEVER invent chapter names not on this manifest.\n"
    )
