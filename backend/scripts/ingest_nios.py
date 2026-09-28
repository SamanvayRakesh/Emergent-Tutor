"""NIOS Secondary Question Bank Builder.

Reads NIOS PDFs from /app/nios_syllabus/, extracts text via PyMuPDF,
generates Q&A pairs using OpenRouter (DeepSeek), and stores them in
MongoDB with curriculum="nios" for quiz/exam/RAG retrieval.

Run once offline — uses the user's own OPENAI_API_KEY (OpenRouter):
    cd /app && python backend/scripts/ingest_nios.py

Estimated cost: ~15–20 OpenRouter credits for all 7 subjects.
"""

import asyncio
import os
import json
import re
import sys
import fitz   # pymupdf

from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from motor.motor_asyncio import AsyncIOMotorClient
from openai import AsyncOpenAI

MONGO_URL  = os.environ.get("MONGO_URL")
DB_NAME    = os.environ.get("DB_NAME")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")

if not MONGO_URL or not DB_NAME:
    sys.exit("[ERR] MONGO_URL / DB_NAME not set in environment")
if not OPENAI_KEY:
    sys.exit("[ERR] OPENAI_API_KEY not set — needed for question generation")

PDF_DIR    = "/app/nios_syllabus"
QA_PER_CHAPTER = 10   # 10 per LLM call — fits comfortably in one response without truncation
QA_BATCH = 5          # generate in two batches of 5 per chapter (more reliable JSON)
MAX_CHARS  = 6000

mongo_client  = AsyncIOMotorClient(MONGO_URL)
db            = mongo_client[DB_NAME]
openai_client = AsyncOpenAI(api_key=OPENAI_KEY, base_url="https://openrouter.ai/api/v1")

# ── NIOS chapters sourced from nios_curriculum.py ─────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from nios_curriculum import NIOS_CURRICULUM  # noqa: E402

# Map subject name → PDF path(s)
SUBJECT_PDF_MAP = {
    "Accountancy":           [os.path.join(PDF_DIR, "Accountancy", "ilovepdf_merged.pdf")],
    "Business Studies":      [os.path.join(PDF_DIR, "Business Studies", "215_ClassX_Business-Studies_Eng - NIOS.pdf")],
    "Data Entry Operations": [os.path.join(PDF_DIR, "Data Entry Operations", "Data Entry Operations.pdf")],
    "Economics":             [os.path.join(PDF_DIR, "Economics", "214_ClassX_Economics_English.pdf")],
    "English":               [
        os.path.join(PDF_DIR, "English", "202_ClassX_English_part 1.pdf"),
        os.path.join(PDF_DIR, "English", "202_ClassX_English_part 2.pdf"),
    ],
    "Entrepreneurship":      [os.path.join(PDF_DIR, "Entrepreneurship", "ilovepdf_merged.pdf")],
    "Folk Art":              [os.path.join(PDF_DIR, "Folk Art", "Theory_Folk-Art-whole.pdf")],
}

# Approximate page count per chapter (used to slice text from merged PDFs)
PAGES_PER_CHAPTER = 15


def extract_subject_text(pdf_paths: list[str], max_chars: int = MAX_CHARS) -> str:
    """Extract and concatenate text from a list of PDFs."""
    combined = ""
    for path in pdf_paths:
        if not os.path.exists(path):
            print(f"  [WARN] PDF not found: {path}")
            continue
        try:
            doc = fitz.open(path)
            for i, page in enumerate(doc):
                if len(combined) >= max_chars:
                    break
                combined += page.get_text()
            doc.close()
        except Exception as e:
            print(f"  [WARN] {path}: {e}")
    combined = re.sub(r"\n{3,}", "\n\n", combined)
    combined = re.sub(r" {2,}", " ", combined)
    return combined[:max_chars]


async def _call_llm(prompt: str) -> list:
    """Single LLM call with JSON extraction. Returns [] on any failure."""
    try:
        resp = await openai_client.chat.completions.create(
            model="deepseek/deepseek-v4-flash",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.7,
            extra_body={"include_reasoning": False},
        )
        raw = (resp.choices[0].message.content or "").strip()
        raw = re.sub(r"^```json|^```|```$", "", raw, flags=re.MULTILINE).strip()
        m = re.search(r"\{[\s\S]*\}", raw)
        if not m:
            return []
        return json.loads(m.group()).get("qa_pairs", [])
    except Exception as e:
        print(f"  [ERR] LLM call failed: {e}")
        return []


async def generate_qa_for_chapter(text_snippet: str, chapter: str, subject: str) -> list:
    """Generate Q&A pairs for a chapter.

    If `text_snippet` is empty (no PDF available), falls back to generating
    from general NIOS curriculum knowledge — still NIOS-accurate, just not
    PDF-verbatim.
    Generates in two batches of QA_BATCH to avoid JSON truncation.
    """
    has_pdf = bool(text_snippet.strip())
    results = []

    for batch_num in range(1, 3):  # 2 batches per chapter
        if has_pdf:
            prompt = f"""Build NIOS Secondary (Class 10) {subject} Q&A knowledge base.
Chapter: "{chapter}" | Batch {batch_num}/2

TEXTBOOK EXCERPT:
{text_snippet[:2000]}

Generate exactly {QA_BATCH} question-answer pairs (different from batch {batch_num-1}).

Rules:
- Factual, 2-3 sentence answers
- Mix: easy/medium/hard
- No repeated questions

Respond ONLY valid JSON:
{{"qa_pairs":[{{"question":"...","answer":"...","difficulty":"easy","topic":"..."}}]}}"""
        else:
            prompt = f"""Build NIOS Secondary Course (Class 10) {subject} Q&A knowledge base.
Chapter: "{chapter}" | Batch {batch_num}/2

Based on the official NIOS curriculum for this chapter, generate exactly {QA_BATCH} question-answer pairs.

Rules:
- Strictly from NIOS syllabus content for this chapter
- Factual, 2-3 sentence answers suitable for a 16-year-old
- Mix: easy/medium/hard
- No repeated questions across batches

Respond ONLY valid JSON:
{{"qa_pairs":[{{"question":"...","answer":"...","difficulty":"easy","topic":"..."}}]}}"""

        pairs = await _call_llm(prompt)
        results.extend(pairs)
        await asyncio.sleep(0.2)

    return results


async def store_qa(qa_pairs: list, subject: str, chapter: str, chapter_no: int) -> int:
    if not qa_pairs:
        return 0
    now = datetime.now(timezone.utc).isoformat()
    docs = [
        {
            "curriculum": "nios",
            "class_level": "10",
            "subject": subject,
            "chapter_title": chapter,
            "chapter_no": chapter_no,
            "question": qa["question"],
            "answer": qa["answer"],
            "difficulty": qa.get("difficulty", "medium"),
            "topic": qa.get("topic", ""),
            "created_at": now,
            "hit_count": 0,
        }
        for qa in qa_pairs
    ]
    await db.question_bank.insert_many(docs)
    return len(docs)


async def build():
    print("NIOS Secondary Question Bank Builder")
    print("=" * 50)

    # Ensure index
    try:
        await db.question_bank.create_index(
            [("curriculum", 1), ("class_level", 1), ("subject", 1), ("chapter_no", 1)]
        )
    except Exception:
        pass

    total_qa = total_ch = 0

    for subject, chapters in NIOS_CURRICULUM.items():
        pdf_paths = SUBJECT_PDF_MAP.get(subject, [])
        subject_text = extract_subject_text(pdf_paths)
        source_label = f"PDF ({len(subject_text)} chars)" if subject_text else "NIOS curriculum knowledge"
        print(f"\n[{subject}] — {source_label}")

        for ch in chapters:
            ch_no   = ch["chapter_no"]
            ch_name = ch["name"]

            # Idempotency: skip if already built
            existing = await db.question_bank.count_documents({
                "curriculum": "nios", "subject": subject, "chapter_no": ch_no,
            })
            if existing >= QA_PER_CHAPTER:
                print(f"  [SKIP] Ch{ch_no}: {ch_name} ({existing} Q&As exist)")
                continue

            # For PDF subjects: use a proportional text slice
            if subject_text:
                slice_start = max(0, (ch_no - 1) * 800)
                slice_end   = min(len(subject_text), slice_start + 4000)
                text_slice  = subject_text[slice_start:slice_end]
            else:
                text_slice = ""  # no PDF — will use curriculum-knowledge prompt

            print(f"  [GEN]  Ch{ch_no}: {ch_name}")
            qa_pairs = await generate_qa_for_chapter(text_slice, ch_name, subject)
            if not qa_pairs:
                print(f"  [WARN] No Q&As returned for {ch_name}")
                continue

            stored = await store_qa(qa_pairs, subject, ch_name, ch_no)
            total_qa  += stored
            total_ch  += 1
            print(f"  [OK]   Stored {stored} Q&As")
            await asyncio.sleep(0.3)   # gentle rate limit

    print(f"\n{'=' * 50}")
    print(f"NIOS Question Bank Build Complete")
    print(f"  Chapters processed: {total_ch}")
    print(f"  Q&A pairs stored  : {total_qa}")
    print(f"{'=' * 50}")
    mongo_client.close()


if __name__ == "__main__":
    asyncio.run(build())
