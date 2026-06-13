"""One-time script: reads downloaded NCERT chapter PDFs, extracts text,
generates Q&A pairs using LLM ONCE, stores in MongoDB question_bank collection.

Run this ONCE after ncert_scraper.py has downloaded the PDFs.
After that, chat.py uses the stored answers — no per-question LLM cost.

Usage:
    python backend/scripts/build_question_bank.py

Cost: runs LLM once per chapter (not per user question). One-time spend.
"""

import asyncio
import os
import json
import re
import sys
import fitz  # pymupdf
from datetime import datetime, timezone

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from motor.motor_asyncio import AsyncIOMotorClient
from openai import AsyncOpenAI

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "neuralearn")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
METADATA_JSON = "/app/backend/curriculum_data/ncert_ai_ready/ncert_ai_metadata.json"
PDF_BASE = "/app/backend/curriculum_data/ncert_ai_ready"
QA_PER_CHAPTER = 25   # seed questions per chapter
VARIANT_COUNT = 3     # semantic rephrasing variants per question

mongo_client = AsyncIOMotorClient(MONGO_URL)
db = mongo_client[DB_NAME]
openai_client = AsyncOpenAI(api_key="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")


# ── PDF text extraction ──────────────────────────────────────────────────────

def extract_pdf_text(pdf_path: str, max_chars: int = 6000) -> str:
    """Extract clean text from a PDF, capped to avoid token bloat."""
    if not os.path.exists(pdf_path):
        return ""
    try:
        doc = fitz.open(pdf_path)
        pages = []
        total = 0
        for page in doc:
            t = page.get_text()
            pages.append(t)
            total += len(t)
            if total >= max_chars:
                break
        doc.close()
        text = "\n".join(pages)
        # Clean up excessive whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)
        return text[:max_chars]
    except Exception as e:
        print(f"[WARN] Could not read {pdf_path}: {e}")
        return ""


# ── LLM Q&A generation ───────────────────────────────────────────────────────

async def generate_qa_pairs(
    chapter_text: str,
    chapter_title: str,
    subject: str,
    class_level: str,
) -> list:
    """Call LLM once per chapter to generate Q&A pairs + semantic variants.
    Returns list of {question, variants, answer, topic, difficulty} dicts.
    """
    if not chapter_text.strip():
        return []

    prompt = f"""You are building a Q&A knowledge base for Class {class_level} {subject} — Chapter: {chapter_title}.

CHAPTER TEXT:
{chapter_text[:4000]}

TASK:
Generate exactly {QA_PER_CHAPTER} question-answer pairs from this chapter content.

For EACH question also generate {VARIANT_COUNT} semantic variants — questions that lead to the SAME answer but are phrased differently. Example:
- Original: "What is photosynthesis?"
- Variant 1: "How do plants make their own food?"
- Variant 2: "What process do plants use to convert sunlight into energy?"
- Variant 3: "Explain the food-making process in green plants."

Rules:
- Answers must be factual, from the chapter text, 2-4 sentences max
- Mix difficulties: easy (40%), medium (40%), hard (20%)
- Cover different topics within the chapter
- NO repetitive answers
- Answers should be self-contained (student gets full understanding from the answer alone)

Respond ONLY with valid JSON, no markdown, no preamble:
{{
  "qa_pairs": [
    {{
      "question": "original question",
      "variants": ["variant 1", "variant 2", "variant 3"],
      "answer": "clear factual answer in 2-4 sentences",
      "topic": "sub-topic name within chapter",
      "difficulty": "easy|medium|hard",
      "keywords": ["key", "terms", "for", "matching"]
    }}
  ]
}}"""

    try:
        resp = await openai_client.chat.completions.create(
            model="gpt-4o-mini",   # cheapest model for generation
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000,
            temperature=0.7,
        )
        raw = resp.choices[0].message.content.strip()
        raw = re.sub(r"^```json|^```|```$", "", raw, flags=re.MULTILINE).strip()
        data = json.loads(raw)
        return data.get("qa_pairs", [])
    except Exception as e:
        print(f"[ERR] LLM generation failed for {chapter_title}: {e}")
        return []


# ── Store to MongoDB ─────────────────────────────────────────────────────────

async def store_qa_pairs(
    qa_pairs: list,
    class_level: str,
    subject: str,
    book_title: str,
    chapter_title: str,
    chapter_no: int,
):
    if not qa_pairs:
        return 0

    now = datetime.now(timezone.utc).isoformat()
    docs = []
    for qa in qa_pairs:
        # Store original question + all variants as searchable fields
        all_questions = [qa["question"]] + qa.get("variants", [])
        docs.append({
            "class_level": class_level,
            "subject": subject,
            "book_title": book_title,
            "chapter_title": chapter_title,
            "chapter_no": chapter_no,
            "question": qa["question"],
            "variants": qa.get("variants", []),
            "all_questions": all_questions,   # used for text search
            "answer": qa["answer"],
            "topic": qa.get("topic", ""),
            "difficulty": qa.get("difficulty", "medium"),
            "keywords": qa.get("keywords", []),
            "created_at": now,
            "hit_count": 0,   # track how often this Q is matched
        })

    if docs:
        await db.question_bank.insert_many(docs)
    return len(docs)


# ── Main runner ──────────────────────────────────────────────────────────────

async def build_bank():
    if not os.path.exists(METADATA_JSON):
        print("[ERR] ncert_ai_metadata.json not found. Run ncert_scraper.py first.")
        return

    with open(METADATA_JSON, "r", encoding="utf-8") as f:
        payload = json.load(f)

    books = payload.get("books", [])
    print(f"[INFO] Found {len(books)} books in metadata")

    # Ensure text search index on question_bank
    await db.question_bank.create_index([("all_questions", "text"), ("keywords", "text")])
    await db.question_bank.create_index([("class_level", 1), ("subject", 1), ("chapter_no", 1)])

    total_qa = 0
    total_chapters = 0

    for book in books:
        cls = str(book["class"])
        subject = book["subject"]
        book_title = book["book_title"]
        safe_title = book_title.replace("/", "-").replace("\\", "-")
        book_dir = os.path.join(PDF_BASE, f"Class_{cls}", safe_title)

        for ch in book.get("chapters", []):
            ch_no = ch.get("chapter_no")
            ch_title = ch.get("title")
            if not ch_no or not ch_title:
                continue

            # Skip if already generated for this chapter
            existing = await db.question_bank.count_documents({
                "class_level": cls,
                "subject": subject,
                "chapter_no": ch_no,
                "book_title": book_title,
            })
            if existing >= QA_PER_CHAPTER:
                print(f"[SKIP] Already built: Class {cls} | {subject} | Ch{ch_no} ({existing} Q&As)")
                continue

            # Extract PDF text
            ch_id = f"{ch_no:02d}"
            pdf_path = os.path.join(book_dir, f"chapter_{ch_id}.pdf")
            text = extract_pdf_text(pdf_path)

            if not text:
                print(f"[WARN] No text extracted: {book_title} Ch{ch_no}")
                continue

            print(f"[GEN]  Class {cls} | {subject} | Ch{ch_no}: {ch_title} ({len(text)} chars)")

            # Generate Q&A pairs via LLM (one call per chapter)
            qa_pairs = await generate_qa_pairs(text, ch_title, subject, cls)

            if not qa_pairs:
                print(f"[WARN] No Q&As generated for {ch_title}")
                continue

            # Store
            stored = await store_qa_pairs(qa_pairs, cls, subject, book_title, ch_title, ch_no)
            total_qa += stored
            total_chapters += 1
            print(f"[OK]   Stored {stored} Q&As for {ch_title}")

            # Small delay to avoid rate limits
            await asyncio.sleep(1)

    print(f"\n========== QUESTION BANK BUILD COMPLETE ==========")
    print(f"  Chapters processed : {total_chapters}")
    print(f"  Total Q&A pairs    : {total_qa}")
    print(f"  (Each has {VARIANT_COUNT} variants = {total_qa * (VARIANT_COUNT + 1)} total searchable questions)")
    print(f"==================================================\n")


if __name__ == "__main__":
    asyncio.run(build_bank())
