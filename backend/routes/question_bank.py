"""Question Bank management routes — trigger build, check status."""
import asyncio
import os
import re
import sys
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from core import db, get_current_user

router = APIRouter()
logger = logging.getLogger("aceit")

# Build status — in-memory per pod (reset on restart)
_build_status = {"running": False, "done_chapters": 0, "total_chapters": 0, "last_run": None, "error": None}


@router.get("/question-bank/stats")
async def get_kb_stats():
    """Public stats about the question bank."""
    count = await db.question_bank.count_documents({})
    return {
        "total_qa_pairs": count,
        "build_running": _build_status["running"],
        "done_chapters": _build_status["done_chapters"],
        "total_chapters": _build_status["total_chapters"],
        "last_run": _build_status["last_run"],
    }


@router.post("/question-bank/build")
async def trigger_kb_build(request: Request, background_tasks: BackgroundTasks):
    """Admin-only: trigger question bank build in background."""
    user = await get_current_user(request)
    if user.get("plan", "free") not in ("pro", "elite") and not user.get("email", "").endswith("@neuralearn.ai"):
        raise HTTPException(status_code=403, detail="Admin only")
    if _build_status["running"]:
        return {"message": "Build already running", "status": _build_status}
    background_tasks.add_task(_run_kb_build)
    return {"message": "Question bank build started in background"}


async def _run_kb_build():
    """Runs the build_question_bank logic inline (no subprocess)."""
    global _build_status
    _build_status["running"] = True
    _build_status["error"] = None
    _build_status["done_chapters"] = 0
    _build_status["last_run"] = datetime.now(timezone.utc).isoformat()

    import fitz
    import json
    from openai import AsyncOpenAI

    METADATA_JSON = "/app/backend/curriculum_data/ncert_ai_ready/ncert_ai_metadata.json"
    PDF_BASE = "/app/backend/curriculum_data/ncert_ai_ready"
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    QA_PER_CHAPTER = 20

    try:
        openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        with open(METADATA_JSON) as f:
            meta = json.load(f)

        all_chapters = []
        for book in meta.get("books", []):
            cls = str(book.get("class", ""))
            subj = book.get("subject", "")  # e.g. "Science", "Mathematics"
            book_title = book.get("book_title", "")
            # Build the PDF directory path (matches actual folder structure)
            pdf_dir = os.path.join(PDF_BASE, f"Class_{cls}", subj.replace(" ", "_"))
            for ch in book.get("chapters", []):
                if ch.get("id") == "prelims" or ch.get("chapter_no") is None:
                    continue
                all_chapters.append({
                    "cls": cls, "subj": subj, "book_title": book_title,
                    "ch": ch, "pdf_dir": pdf_dir,
                })

        _build_status["total_chapters"] = len(all_chapters)

        for entry in all_chapters:
            ch = entry["ch"]
            ch_no = ch.get("chapter_no", 0)
            title = ch.get("title", f"Chapter {ch_no}")

            # Skip if already built
            existing = await db.question_bank.count_documents({
                "class_level": entry["cls"], "subject": entry["subj"], "chapter_no": ch_no
            })
            if existing >= QA_PER_CHAPTER // 2:
                _build_status["done_chapters"] += 1
                continue

            # PDF filename uses 'file' key in metadata
            pdf_filename = ch.get("file", ch.get("pdf_filename", ""))
            pdf_path = os.path.join(entry["pdf_dir"], pdf_filename) if pdf_filename else ""
            
            # Also try without replacing spaces in subj (Science folder directly)
            if not os.path.exists(pdf_path) and pdf_filename:
                pdf_path = os.path.join(PDF_BASE, f"Class_{entry['cls']}", entry['subj'], pdf_filename)
            text = ""
            if os.path.exists(pdf_path):
                try:
                    doc = fitz.open(pdf_path)
                    pages = []
                    total = 0
                    for page in doc:
                        t = page.get_text()
                        pages.append(t)
                        total += len(t)
                        if total >= 5000:
                            break
                    doc.close()
                    text = "\n".join(pages)[:5000]
                    text = re.sub(r"\n{3,}", "\n\n", text)
                except Exception as e:
                    logger.warning(f"PDF read error {pdf_path}: {e}")

            if not text.strip():
                _build_status["done_chapters"] += 1
                continue

            # Generate Q&A pairs
            try:
                resp = await openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                f"You are a CBSE expert generating exam Q&A for Class {entry['cls']} {entry['subj']} "
                                f"Chapter {ch_no}: {title}.\n"
                                f"Generate exactly {QA_PER_CHAPTER} Q&A pairs from the text. Each pair must be a real "
                                "CBSE-style question with a clear, factual answer (2-4 sentences).\n"
                                "Output JSON array ONLY:\n"
                                '[{"question":"...","answer":"...","topic":"...","difficulty":"easy|medium|hard"}]'
                            ),
                        },
                        {"role": "user", "content": f"TEXT:\n{text}"},
                    ],
                    max_tokens=3000,
                    temperature=0.3,
                )
                raw = resp.choices[0].message.content.strip()
                # Extract JSON array from response
                match = re.search(r"\[.*\]", raw, re.DOTALL)
                if not match:
                    _build_status["done_chapters"] += 1
                    continue
                pairs = json.loads(match.group())

                now = datetime.now(timezone.utc).isoformat()
                docs = []
                for pair in pairs:
                    if not pair.get("question") or not pair.get("answer"):
                        continue
                    docs.append({
                        "class_level": entry["cls"],
                        "subject": entry["subj"],
                        "chapter_no": ch_no,
                        "chapter_title": title,
                        "book_title": entry["book_title"],
                        "question": pair["question"],
                        "answer": pair["answer"],
                        "topic": pair.get("topic", ""),
                        "difficulty": pair.get("difficulty", "medium"),
                        "created_at": now,
                        "hit_count": 0,
                    })
                if docs:
                    await db.question_bank.insert_many(docs)
                    logger.info(f"QB: inserted {len(docs)} pairs for Class {entry['cls']} {entry['subj']} Ch{ch_no}")

            except Exception as e:
                logger.error(f"QB LLM error for {entry['cls']} {entry['subj']} Ch{ch_no}: {e}")

            _build_status["done_chapters"] += 1
            await asyncio.sleep(0.5)  # rate limit safety

        # Create text index if not exists
        try:
            await db.question_bank.create_index([("question", "text")], name="question_text_idx", background=True)
        except Exception:
            pass

        _build_status["running"] = False
        logger.info(f"Question bank build complete. Total Q&A pairs: {await db.question_bank.count_documents({})}")

    except Exception as e:
        _build_status["running"] = False
        _build_status["error"] = str(e)
        logger.error(f"QB build failed: {e}")
