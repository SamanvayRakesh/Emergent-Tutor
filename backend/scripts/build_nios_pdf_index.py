"""NIOS PDF Chunk Indexer.

Reads every NIOS PDF from /app/nios_syllabus/, splits it into ~1 200-char
chunks (preserving paragraph boundaries), and stores them in the
`nios_pdf_chunks` MongoDB collection with a full-text search index.

Run ONCE offline (idempotent — skips subjects that already have chunks):
    cd /app && python backend/scripts/build_nios_pdf_index.py

These chunks power the PDF-grounded RAG in chat.py for NIOS students.
"""

import asyncio
import os
import re
import sys

import fitz  # pymupdf

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME   = os.environ.get("DB_NAME")

if not MONGO_URL or not DB_NAME:
    sys.exit("[ERR] MONGO_URL / DB_NAME not set")

PDF_DIR = "/app/nios_syllabus"

# Map subject → PDF file(s) — same as ingest_nios.py
SUBJECT_PDF_MAP: dict[str, list[str]] = {
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
    "Home Science":          [
        os.path.join(PDF_DIR, "Home Science", "216_ClassX_Home-Science_English_Part1.pdf"),
        os.path.join(PDF_DIR, "Home Science", "216_ClassX_Home-Science_English_Part2.pdf"),
    ],
}

CHUNK_SIZE   = 1200   # target chars per chunk
OVERLAP_CHARS = 100   # overlap between consecutive chunks for context continuity


def _clean(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def _chunk_text(full_text: str) -> list[str]:
    """Split text into overlapping chunks while preserving paragraph breaks."""
    paras = re.split(r"\n\n+", full_text)
    chunks, buf = [], ""
    for para in paras:
        if len(buf) + len(para) > CHUNK_SIZE:
            if buf:
                chunks.append(buf.strip())
            # Start new chunk with overlap
            buf = buf[-OVERLAP_CHARS:] + "\n\n" + para if buf else para
        else:
            buf = (buf + "\n\n" + para) if buf else para
    if buf.strip():
        chunks.append(buf.strip())
    return [c for c in chunks if len(c) > 80]  # drop tiny fragments


async def build():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    # Create text index if it doesn't exist
    try:
        await db.nios_pdf_chunks.create_index([("text", "text")])
        await db.nios_pdf_chunks.create_index([("subject", 1)])
    except Exception:
        pass

    total_chunks = 0
    now = datetime.now(timezone.utc).isoformat()

    for subject, pdf_paths in SUBJECT_PDF_MAP.items():
        # Idempotency: skip if we already have chunks for this subject
        existing = await db.nios_pdf_chunks.count_documents({"subject": subject})
        if existing > 0:
            print(f"[SKIP] {subject} ({existing} chunks already indexed)")
            continue

        # Extract text from all PDFs for this subject
        full_text = ""
        for path in pdf_paths:
            if not os.path.exists(path):
                print(f"  [WARN] missing: {path}")
                continue
            try:
                doc = fitz.open(path)
                for page in doc:
                    full_text += page.get_text() + "\n\n"
                doc.close()
                print(f"  [PDF]  read {path} ({len(full_text)} chars so far)")
            except Exception as e:
                print(f"  [ERR]  {path}: {e}")

        if not full_text.strip():
            print(f"[SKIP] {subject} — no text extracted")
            continue

        full_text = _clean(full_text)
        chunks = _chunk_text(full_text)
        print(f"[{subject}] {len(chunks)} chunks from {len(full_text)} chars")

        docs = [
            {
                "subject": subject,
                "chunk_index": i,
                "text": chunk,
                "curriculum": "nios",
                "class_level": "10",
                "created_at": now,
            }
            for i, chunk in enumerate(chunks)
        ]
        await db.nios_pdf_chunks.insert_many(docs)
        total_chunks += len(docs)
        print(f"  [OK]  stored {len(docs)} chunks")

    print(f"\nDone. Total new chunks stored: {total_chunks}")
    client.close()


if __name__ == "__main__":
    asyncio.run(build())
