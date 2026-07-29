"""Generate Q&A for BNPS chapters that are missing PDFs.
Uses chapter name + topic knowledge (no PDF required).
Run: cd /app/backend && python3 scripts/fill_missing_bnps_qa.py
"""
import asyncio
import os
import json
import re
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__) + "/..")

from motor.motor_asyncio import AsyncIOMotorClient
from openai import AsyncOpenAI

MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
QA_PER_CHAPTER = 20

# BNPS chapters that need Q&A
BNPS_ALL_CHAPTERS = {
    "Mathematics": [
        (1, "Rational Numbers"), (2, "Exponents and Powers"),
        (3, "Squares and Square Roots"), (4, "Cubes and Cube Roots"),
        (5, "Playing with Numbers"), (6, "Algebraic Expressions and Identities"),
        (7, "Factorisation"), (8, "Linear Equations in One Variable"),
        (9, "Comparing Quantities"), (10, "Direct and Indirect Variations"),
        (11, "Understanding Quadrilaterals"), (12, "Visualising Solid Shapes"),
        (13, "Practical Geometry"), (14, "Mensuration"),
        (15, "Introduction to Graphs"), (16, "Data Handling"),
    ],
    "Science": [
        (1, "Exploring the Investigative World of Science"),
        (2, "The Invisible Living World: Beyond Our Naked Eye"),
        (3, "Health: The Ultimate Treasure"),
        (4, "Electricity: Magnetic and Heating Effects"),
        (5, "Exploring Forces"),
        (6, "Pressure, Winds, Storms, and Cyclones"),
        (7, "Particulate Nature of Matter"),
        (8, "Nature of Matter: Elements, Compounds, and Mixtures"),
        (9, "The Amazing World of Solutes, Solvents and Solutions"),
        (10, "Light: Mirrors and Lenses"),
        (11, "Keeping Time with the Skies"),
        (12, "How Nature Works in Harmony"),
        (13, "Our Home: Earth, a Unique Life Sustaining Planet"),
    ],
    "Social Studies": [
        (1, "Natural Resources: Treasures of The Earth"),
        (2, "The Changing Political Landscape of India"),
        (3, "The Rise of the Marathas"),
        (4, "The Colonial Transformation of India"),
        (5, "From Ballot to Bharat: The Spirit of Universal Franchise"),
        (6, "The Parliamentary System: Legislature and Executive"),
        (7, "Resources at Work"),
    ],
    "English": [
        (1, "The Time Machine"),
        (2, "When the Mop Count Did Not Tally"),
        (3, "Stopping by Woods on a Snowy Evening"),
        (4, "The Portrait of a Lady"),
        (5, "Stuart Little"),
        (6, "Robots in Everyday Life"),
        (7, "Knowing Your Strengths"),
        (8, "The Children's Hour"),
        (9, "That Little Square Box"),
        (10, "Haunted"),
        (11, "On the Grasshopper and Cricket"),
        (12, "The Canterville Ghost"),
        (13, "Night of the Scorpion"),
    ],
}


async def generate_qa(subject: str, chapter: str, ch_no: int, client: AsyncOpenAI) -> list:
    subject_desc = {
        "Mathematics": "Grade 8 Mathematics",
        "Science": "Grade 8 Science (NCERT Curiosity textbook)",
        "Social Studies": "Grade 8 Social Studies (NCERT Exploring Society textbook)",
        "English": "Grade 8 English (NCERT Poorvi textbook)",
    }.get(subject, f"Grade 8 {subject}")

    prompt = (
        f"Generate {QA_PER_CHAPTER} high-quality MCQ-style Q&A pairs for {subject_desc}, "
        f"Chapter {ch_no}: \"{chapter}\".\n\n"
        "For each Q&A, include 3 rephrased variants of the question.\n"
        "Cover all key sub-topics of this chapter.\n"
        "Mix difficulties: easy (40%), medium (40%), hard (20%).\n\n"
        "Respond ONLY with valid JSON:\n"
        '{"qa_pairs":[{"question":"...","variants":["...","...","..."],'
        '"answer":"...","topic":"sub-topic","difficulty":"easy|medium|hard","keywords":["..."]}]}'
    )
    try:
        resp = await client.chat.completions.create(
            model="deepseek/deepseek-v4-flash",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000, temperature=0.7,
        )
        raw = resp.choices[0].message.content.strip()
        raw = re.sub(r"^```json|^```|```$", "", raw, flags=re.MULTILINE).strip()
        return json.loads(raw).get("qa_pairs", [])
    except Exception as e:
        print(f"  [ERR] {chapter}: {e}")
        return []


async def main():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    ai = AsyncOpenAI(api_key=OPENAI_KEY)
    total_added = 0

    for subject, chapters in BNPS_ALL_CHAPTERS.items():
        print(f"\n[{subject}]")
        for (ch_no, ch_name) in chapters:
            existing = await db.question_bank.count_documents({
                "school": "brooklyn_national", "class_level": "8",
                "subject": subject, "chapter_no": ch_no,
            })
            if existing >= QA_PER_CHAPTER // 2:
                print(f"  [SKIP] Ch{ch_no}: {ch_name} ({existing} exist)")
                continue

            print(f"  [GEN]  Ch{ch_no}: {ch_name}")
            qa_pairs = await generate_qa(subject, ch_name, ch_no, ai)
            if not qa_pairs:
                continue

            now = datetime.now(timezone.utc).isoformat()
            docs = []
            for qa in qa_pairs:
                all_q = [qa["question"]] + qa.get("variants", [])
                docs.append({
                    "school": "brooklyn_national", "class_level": "8",
                    "subject": subject, "chapter_title": ch_name,
                    "chapter_no": ch_no, "question": qa["question"],
                    "variants": qa.get("variants", []),
                    "all_questions": all_q, "answer": qa["answer"],
                    "topic": qa.get("topic", ""), "difficulty": qa.get("difficulty", "medium"),
                    "keywords": qa.get("keywords", []),
                    "created_at": now, "hit_count": 0,
                })
            if docs:
                await db.question_bank.insert_many(docs)
                total_added += len(docs)
                print(f"  [OK]   Added {len(docs)} Q&As")
            await asyncio.sleep(1)

    print(f"\n=== Done. Added {total_added} Q&As ===")
    final_count = await db.question_bank.count_documents({"school": "brooklyn_national"})
    print(f"Total BNPS Q&As: {final_count}")


if __name__ == "__main__":
    asyncio.run(main())
