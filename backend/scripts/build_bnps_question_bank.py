"""BNPS Question Bank Builder.

Reads downloaded BNPS PDFs from curriculum_data/bnps_pdfs/grade8/,
extracts text, generates Q&A pairs with GPT, and stores in MongoDB with
school="brooklyn_national" so queries can filter school-specific content.

Run AFTER bnps_pdf_downloader.py has completed.

Usage:
    cd /app && python backend/scripts/build_bnps_question_bank.py
"""

import asyncio
import os
import json
import re
import sys
import fitz  # pymupdf
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from motor.motor_asyncio import AsyncIOMotorClient
from openai import AsyncOpenAI

MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME   = os.environ.get("DB_NAME")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")

PDF_DIR  = "/app/backend/curriculum_data/bnps_pdfs/grade8"
META_FILE = os.path.join(PDF_DIR, "metadata.json")

QA_PER_CHAPTER = 20
VARIANT_COUNT  = 3
MAX_CHARS      = 6000

mongo_client = AsyncIOMotorClient(MONGO_URL)
db = mongo_client[DB_NAME]
openai_client = AsyncOpenAI(api_key=OPENAI_KEY, base_url="https://openrouter.ai/api/v1")


def extract_pdf_text(pdf_path: str) -> str:
    if not os.path.exists(pdf_path):
        return ""
    try:
        doc = fitz.open(pdf_path)
        pages, total = [], 0
        for page in doc:
            t = page.get_text()
            pages.append(t)
            total += len(t)
            if total >= MAX_CHARS:
                break
        doc.close()
        text = "\n".join(pages)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)
        return text[:MAX_CHARS]
    except Exception as e:
        print(f"  [WARN] PDF read error {pdf_path}: {e}")
        return ""


async def generate_qa_pairs(text: str, chapter: str, subject: str) -> list:
    if not text.strip():
        return []
    prompt = f"""You are building a Q&A knowledge base for Grade 8 {subject} at Brooklyn National Public School.
Chapter: "{chapter}"

CHAPTER TEXT:
{text[:4000]}

TASK: Generate exactly {QA_PER_CHAPTER} question-answer pairs from this chapter.

For each question also generate {VARIANT_COUNT} semantic variants.

Rules:
- Answers must be factual, 2-4 sentences max
- Mix: easy (40%), medium (40%), hard (20%)
- Cover different sub-topics
- For math: include numerical/formula questions
- Answers self-contained

Respond ONLY with valid JSON:
{{
  "qa_pairs": [
    {{
      "question": "...",
      "variants": ["...", "...", "..."],
      "answer": "...",
      "topic": "sub-topic",
      "difficulty": "easy|medium|hard",
      "keywords": ["key", "terms"]
    }}
  ]
}}"""
    try:
        resp = await openai_client.chat.completions.create(
            model="deepseek/deepseek-v4-flash",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000,
            temperature=0.7,
        )
        raw = resp.choices[0].message.content.strip()
        raw = re.sub(r"^```json|^```|```$", "", raw, flags=re.MULTILINE).strip()
        return json.loads(raw).get("qa_pairs", [])
    except Exception as e:
        print(f"  [ERR] LLM failed for {chapter}: {e}")
        return []


async def store_qa_pairs(qa_pairs: list, subject: str, chapter: str, chapter_no: int) -> int:
    if not qa_pairs:
        return 0
    now = datetime.now(timezone.utc).isoformat()
    docs = []
    for qa in qa_pairs:
        all_q = [qa["question"]] + qa.get("variants", [])
        docs.append({
            "school": "brooklyn_national",
            "class_level": "8",
            "subject": subject,
            "chapter_title": chapter,
            "chapter_no": chapter_no,
            "question": qa["question"],
            "variants": qa.get("variants", []),
            "all_questions": all_q,
            "answer": qa["answer"],
            "topic": qa.get("topic", ""),
            "difficulty": qa.get("difficulty", "medium"),
            "keywords": qa.get("keywords", []),
            "created_at": now,
            "hit_count": 0,
        })
    if docs:
        await db.question_bank.insert_many(docs)
    return len(docs)


async def build():
    if not os.path.exists(META_FILE):
        print(f"[ERR] metadata.json not found at {META_FILE}")
        print("      Run bnps_pdf_downloader.py first.")
        return

    with open(META_FILE, "r") as f:
        meta = json.load(f)

    # Ensure indexes (skip text index if conflicts with existing)
    try:
        await db.question_bank.create_index(
            [("all_questions", "text"), ("keywords", "text")]
        )
    except Exception as idx_e:
        logger.warning(f"Text index skipped (conflict): {idx_e}") if False else print(f"  [INFO] Text index already exists, skipping: {str(idx_e)[:80]}")
    await db.question_bank.create_index(
        [("school", 1), ("class_level", 1), ("subject", 1), ("chapter_no", 1)]
    )

    total_qa = total_ch = 0

    for subject, info in meta.get("subjects", {}).items():
        print(f"\n[{subject}]")
        for ch_info in info.get("chapters", []):
            if ch_info.get("status") == "failed":
                print(f"  [SKIP] Ch{ch_info['bnps_order']}: PDF not available")
                continue

            ch_no   = ch_info["bnps_order"]
            ch_name = ch_info["bnps_name"]
            pdf_path = os.path.join(PDF_DIR, subject, ch_info["file"])

            # Skip if already built
            existing = await db.question_bank.count_documents({
                "school": "brooklyn_national",
                "class_level": "8",
                "subject": subject,
                "chapter_no": ch_no,
            })
            if existing >= QA_PER_CHAPTER:
                print(f"  [SKIP] Ch{ch_no}: {ch_name} ({existing} Q&As exist)")
                continue

            text = extract_pdf_text(pdf_path)
            if not text:
                print(f"  [WARN] No text: {ch_name}")
                continue

            print(f"  [GEN]  Ch{ch_no}: {ch_name} ({len(text)} chars)")
            qa_pairs = await generate_qa_pairs(text, ch_name, subject)
            if not qa_pairs:
                continue

            stored = await store_qa_pairs(qa_pairs, subject, ch_name, ch_no)
            total_qa += stored
            total_ch += 1
            print(f"  [OK]   Stored {stored} Q&As")
            await asyncio.sleep(1)

    print(f"\n{'='*50}")
    print(f"BNPS Question Bank Build Complete")
    print(f"  Chapters  : {total_ch}")
    print(f"  Q&A pairs : {total_qa}")
    print(f"{'='*50}")


if __name__ == "__main__":
    asyncio.run(build())
