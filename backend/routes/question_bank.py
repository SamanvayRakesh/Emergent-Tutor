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


async def _get_build_status() -> dict:
    """Get build status from MongoDB (persists across restarts)."""
    doc = await db.kb_build_status.find_one({}, {"_id": 0}) or {}
    # Merge with in-memory running state
    return {**doc, "running": _build_status.get("running", False), "done_chapters": _build_status.get("done_chapters", doc.get("done_chapters", 0))}


async def _save_build_status():
    await db.kb_build_status.update_one({}, {"$set": {
        "done_chapters": _build_status["done_chapters"],
        "total_chapters": _build_status["total_chapters"],
        "last_run": _build_status["last_run"],
        "error": _build_status["error"],
    }}, upsert=True)


@router.get("/question-bank/stats")
async def get_kb_stats():
    """Public stats about the question bank."""
    count = await db.question_bank.count_documents({})
    status = await _get_build_status()
    return {
        "total_qa_pairs": count,
        "build_running": status.get("running", False),
        "done_chapters": status.get("done_chapters", 0),
        "total_chapters": status.get("total_chapters", 0),
        "last_run": status.get("last_run"),
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


# ── BNPS build status ──────────────────────────────────────────────────────────
_bnps_build_status = {"running": False, "phase": None, "progress": "", "error": None}


@router.post("/question-bank/build-bnps")
async def trigger_bnps_build(request: Request, background_tasks: BackgroundTasks):
    """Admin-only: download BNPS PDFs and build BNPS question bank."""
    user = await get_current_user(request)
    if not user.get("email", "").endswith("@neuralearn.ai"):
        raise HTTPException(status_code=403, detail="Admin only")
    if _bnps_build_status["running"]:
        return {"message": "BNPS build already running", "status": _bnps_build_status}
    background_tasks.add_task(_run_bnps_build)
    return {"message": "BNPS PDF download + question bank build started in background"}


@router.get("/question-bank/build-bnps/status")
async def get_bnps_build_status(request: Request):
    """Get BNPS build progress."""
    await get_current_user(request)
    bnps_count = await db.question_bank.count_documents({"school": "brooklyn_national"})
    return {**_bnps_build_status, "bnps_qa_count": bnps_count}


async def _run_bnps_build():
    """Download BNPS chapter PDFs and generate Q&A pairs inline."""
    global _bnps_build_status
    import json, re
    import fitz
    import aiohttp
    from openai import AsyncOpenAI

    _bnps_build_status.update({"running": True, "phase": "downloading", "progress": "Starting PDF download...", "error": None})

    NCERT_PDF_BASE = "https://ncert.nic.in/textbook/pdf/"
    PDF_DIR = "/app/backend/curriculum_data/bnps_pdfs/grade8"
    OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
    QA_PER_CHAPTER = 20

    HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    # Chapter mapping: subject → [(bnps_order, bnps_name, ncert_ch_no, book_code)]
    ALL_CHAPTERS = {
        "Mathematics": [
            (1,"Rational Numbers",1,"hegp1"),(2,"Exponents and Powers",12,"hegp1"),
            (3,"Squares and Square Roots",6,"hegp1"),(4,"Cubes and Cube Roots",7,"hegp1"),
            (5,"Playing with Numbers",16,"hegp1"),(6,"Algebraic Expressions and Identities",9,"hegp1"),
            (7,"Factorisation",14,"hegp1"),(8,"Linear Equations in One Variable",2,"hegp1"),
            (9,"Comparing Quantities",8,"hegp1"),(10,"Direct and Indirect Variations",13,"hegp1"),
            (11,"Understanding Quadrilaterals",3,"hegp1"),(12,"Visualising Solid Shapes",10,"hegp1"),
            (13,"Practical Geometry",4,"hegp1"),(14,"Mensuration",11,"hegp1"),
            (15,"Introduction to Graphs",15,"hegp1"),(16,"Data Handling",5,"hegp1"),
        ],
        "Science": [
            (1,"Exploring the Investigative World of Science",1,"hecu1"),
            (2,"The Invisible Living World: Beyond Our Naked Eye",2,"hecu1"),
            (3,"Health: The Ultimate Treasure",3,"hecu1"),
            (4,"Electricity: Magnetic and Heating Effects",4,"hecu1"),
            (5,"Exploring Forces",5,"hecu1"),(6,"Pressure, Winds, Storms, and Cyclones",6,"hecu1"),
            (7,"Particulate Nature of Matter",7,"hecu1"),
            (8,"Nature of Matter: Elements, Compounds, and Mixtures",8,"hecu1"),
            (9,"The Amazing World of Solutes, Solvents and Solutions",9,"hecu1"),
            (10,"Light: Mirrors and Lenses",10,"hecu1"),(11,"Keeping Time with the Skies",11,"hecu1"),
            (12,"How Nature Works in Harmony",12,"hecu1"),
            (13,"Our Home: Earth, a Unique Life Sustaining Planet",13,"hecu1"),
        ],
        "Social Studies": [
            (1,"Natural Resources: Treasures of The Earth",1,"hees1"),
            (2,"The Changing Political Landscape of India",2,"hees1"),
            (3,"The Rise of the Marathas",3,"hees1"),
            (4,"The Colonial Transformation of India",4,"hees1"),
            (5,"From Ballot to Bharat: The Spirit of Universal Franchise",5,"hees1"),
            (6,"The Parliamentary System: Legislature and Executive",6,"hees1"),
            (7,"Resources at Work",7,"hees1"),
        ],
        "English": [
            (1,"The Time Machine",1,"hepr1"),(2,"When the Mop Count Did Not Tally",2,"hepr1"),
            (3,"Stopping by Woods on a Snowy Evening",3,"hepr1"),
            (4,"The Portrait of a Lady",4,"hepr1"),(5,"Stuart Little",5,"hepr1"),
            (6,"Robots in Everyday Life",6,"hepr1"),(7,"Knowing Your Strengths",7,"hepr1"),
            (8,"The Children's Hour",8,"hepr1"),(9,"That Little Square Box",9,"hepr1"),
            (10,"Haunted",10,"hepr1"),(11,"On the Grasshopper and Cricket",11,"hepr1"),
            (12,"The Canterville Ghost",12,"hepr1"),(13,"Night of the Scorpion",13,"hepr1"),
        ],
    }

    try:
        os.makedirs(PDF_DIR, exist_ok=True)
        openai_client = AsyncOpenAI(api_key=OPENAI_KEY, base_url="https://openrouter.ai/api/v1")

        # Ensure DB indexes (handle conflict with existing text index)
        try:
            await db.question_bank.create_index(
                [("all_questions", "text"), ("keywords", "text")],
                background=True
            )
        except Exception:
            pass  # Text index already exists — OK to continue
        await db.question_bank.create_index(
            [("school", 1), ("class_level", 1), ("subject", 1), ("chapter_no", 1)],
            background=True
        )

        total_downloaded = total_qa = 0
        connector = aiohttp.TCPConnector(limit=3)
        async with aiohttp.ClientSession(connector=connector) as http:
            for subject, chapters in ALL_CHAPTERS.items():
                subj_dir = os.path.join(PDF_DIR, subject)
                os.makedirs(subj_dir, exist_ok=True)

                for (bnps_order, bnps_name, ncert_ch_no, book_code) in chapters:
                    _bnps_build_status["progress"] = f"[{subject}] Ch{bnps_order}: {bnps_name}"
                    pdf_path = os.path.join(subj_dir, f"chapter_{bnps_order:02d}.pdf")

                    # Download if needed
                    if not (os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 1000):
                        url = f"{NCERT_PDF_BASE}{book_code}{ncert_ch_no:02d}.pdf"
                        try:
                            async with http.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                                if resp.status == 200:
                                    data = await resp.read()
                                    if data.startswith(b"%PDF"):
                                        with open(pdf_path, "wb") as f:
                                            f.write(data)
                                        total_downloaded += 1
                                        logger.info(f"BNPS PDF downloaded: {subject} Ch{bnps_order}")
                        except Exception as e:
                            logger.warning(f"BNPS PDF download failed {url}: {e}")

                    # Build Q&A if not already done
                    existing = await db.question_bank.count_documents({
                        "school": "brooklyn_national", "class_level": "8",
                        "subject": subject, "chapter_no": bnps_order,
                    })
                    if existing >= QA_PER_CHAPTER // 2:
                        continue

                    # Extract text from PDF
                    text = ""
                    if os.path.exists(pdf_path):
                        try:
                            doc = fitz.open(pdf_path)
                            pages, total = [], 0
                            for page in doc:
                                t = page.get_text()
                                pages.append(t)
                                total += len(t)
                                if total >= 6000:
                                    break
                            doc.close()
                            text = re.sub(r"\n{3,}", "\n\n", "\n".join(pages))[:6000]
                        except Exception as e:
                            logger.warning(f"BNPS PDF read error {pdf_path}: {e}")

                    if not text.strip():
                        continue

                    # Generate Q&A
                    _bnps_build_status["phase"] = "building"
                    try:
                        resp = await openai_client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[{"role": "user", "content": (
                                f"Build a Q&A knowledge base for Grade 8 {subject} at Brooklyn National Public School.\n"
                                f"Chapter: \"{bnps_name}\"\n\nTEXT:\n{text[:4000]}\n\n"
                                f"Generate exactly {QA_PER_CHAPTER} question-answer pairs. "
                                "Include 3 phrasing variants per question.\n"
                                "JSON format:\n"
                                '{"qa_pairs":[{"question":"...","variants":["...","...","..."],"answer":"...","topic":"...","difficulty":"easy|medium|hard","keywords":["..."]}]}'
                            )}],
                            max_tokens=4000, temperature=0.7,
                        )
                        raw = resp.choices[0].message.content.strip()
                        raw = re.sub(r"^```json|^```|```$", "", raw, flags=re.MULTILINE).strip()
                        qa_pairs = json.loads(raw).get("qa_pairs", [])

                        now = datetime.now(timezone.utc).isoformat()
                        docs = []
                        for qa in qa_pairs:
                            all_q = [qa["question"]] + qa.get("variants", [])
                            docs.append({
                                "school": "brooklyn_national", "class_level": "8",
                                "subject": subject, "chapter_title": bnps_name,
                                "chapter_no": bnps_order, "question": qa["question"],
                                "variants": qa.get("variants", []),
                                "all_questions": all_q, "answer": qa["answer"],
                                "topic": qa.get("topic", ""), "difficulty": qa.get("difficulty", "medium"),
                                "keywords": qa.get("keywords", []),
                                "created_at": now, "hit_count": 0,
                            })
                        if docs:
                            await db.question_bank.insert_many(docs)
                            total_qa += len(docs)
                            logger.info(f"BNPS QB: {len(docs)} Q&As for {subject} Ch{bnps_order}")
                    except Exception as e:
                        logger.error(f"BNPS QB LLM error {subject} Ch{bnps_order}: {e}")

                    await asyncio.sleep(1)

        _bnps_build_status.update({
            "running": False, "phase": "done",
            "progress": f"Done. {total_downloaded} PDFs downloaded, {total_qa} Q&A pairs stored.",
        })
        logger.info(f"BNPS QB build complete: {total_qa} Q&As")
    except Exception as e:
        _bnps_build_status.update({"running": False, "error": str(e)})
        logger.error(f"BNPS QB build failed: {e}")


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
        openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY, base_url="https://openrouter.ai/api/v1")
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
