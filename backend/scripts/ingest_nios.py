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
QA_PER_CHAPTER = 15   # 15 Q&As per chapter — sufficient for RAG + quiz use
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


async def generate_qa_for_chapter(text_snippet: str, chapter: str, subject: str) -> list:
    if not text_snippet.strip():
        return []
    prompt = f"""You are building a Q&A knowledge base for NIOS Secondary (Class 10) {subject}.
Chapter: "{chapter}"

SUBJECT CONTEXT (first {len(text_snippet)} chars of textbook):
{text_snippet[:3000]}

TASK: Generate exactly {QA_PER_CHAPTER} question-answer pairs that a NIOS Secondary student
should know about this chapter.

Rules:
- Answers: factual, 2-3 sentences, self-contained
- Mix difficulty: easy (40%), medium (40%), hard (20%)
- Vary question types: definition, application, comparison, numerical/formula where relevant
- DO NOT repeat similar questions

Respond ONLY with valid JSON (no markdown):
{{
  "qa_pairs": [
    {{
      "question": "...",
      "answer": "...",
      "difficulty": "easy|medium|hard",
      "topic": "sub-topic name"
    }}
  ]
}}"""
    try:
        resp = await openai_client.chat.completions.create(
            model="deepseek/deepseek-v4-flash",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2500,
            temperature=0.7,
            extra_body={"include_reasoning": False},
        )
        raw = resp.choices[0].message.content.strip()
        raw = re.sub(r"^```json|^```|```$", "", raw, flags=re.MULTILINE).strip()
        m = re.search(r"\{[\s\S]*\}", raw)
        if not m:
            return []
        return json.loads(m.group()).get("qa_pairs", [])
    except Exception as e:
        print(f"  [ERR] LLM failed for {chapter}: {e}")
        return []


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
        if not subject_text:
            print(f"\n[SKIP] {subject} — no PDF text available")
            continue

        print(f"\n[{subject}] ({len(subject_text)} chars from PDF)")

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

            # Use a text slice proportional to chapter position within the book
            slice_start = max(0, (ch_no - 1) * 800)
            slice_end   = min(len(subject_text), slice_start + 4000)
            text_slice  = subject_text[slice_start:slice_end]

            print(f"  [GEN]  Ch{ch_no}: {ch_name}")
            qa_pairs = await generate_qa_for_chapter(text_slice, ch_name, subject)
            if not qa_pairs:
                continue

            stored = await store_qa(qa_pairs, subject, ch_name, ch_no)
            total_qa  += stored
            total_ch  += 1
            print(f"  [OK]   Stored {stored} Q&As")
            await asyncio.sleep(0.5)   # gentle rate limit

    print(f"\n{'=' * 50}")
    print(f"NIOS Question Bank Build Complete")
    print(f"  Chapters processed: {total_ch}")
    print(f"  Q&A pairs stored  : {total_qa}")
    print(f"{'=' * 50}")
    mongo_client.close()


if __name__ == "__main__":
    asyncio.run(build())
