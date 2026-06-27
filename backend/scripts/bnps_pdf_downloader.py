"""BNPS Grade 8 PDF Downloader.

Downloads official NCERT textbook chapter PDFs that map to Brooklyn National
Public School Grade 8 curriculum.  Saves files to:
  /app/backend/curriculum_data/bnps_pdfs/grade8/{Subject}/chapter_{nn}.pdf

After running this script, run build_bnps_question_bank.py to generate Q&A pairs.

Book code mapping (NCERT 2024-25 new textbooks):
  Mathematics  → Ganita Prakash    (hegp1)
  Science      → Curiosity         (hecu1)
  Social Studies → Exploring Society (hees1)
  English      → Poorvi            (hepr1)
"""

import asyncio
import os
import aiohttp

NCERT_PDF_BASE = "https://ncert.nic.in/textbook/pdf/"
OUTPUT_DIR = "/app/backend/curriculum_data/bnps_pdfs/grade8"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

# ── Chapter mapping: BNPS chapter name → NCERT PDF code ──────────────────────
# Format: (bnps_chapter_name, ncert_chapter_number_in_book, ncert_book_code)
# NCERT hegp1 chapter order (Ganita Prakash Class 8):
#   1=Rational Numbers, 2=Linear Eq One Variable, 3=Understanding Quadrilaterals,
#   4=Practical Geometry, 5=Data Handling, 6=Squares & Sq Roots, 7=Cubes & Cube Roots,
#   8=Comparing Quantities, 9=Algebraic Expr & Identities, 10=Visualising Solid Shapes,
#   11=Mensuration, 12=Exponents & Powers, 13=Direct & Inverse Proportions,
#   14=Factorisation, 15=Introduction to Graphs, 16=Playing with Numbers

BNPS_MATH_CHAPTERS = [
    # (bnps_order, bnps_name,                          ncert_ch_no, book_code)
    (1,  "Rational Numbers",                            1,  "hegp1"),
    (2,  "Exponents and Powers",                        12, "hegp1"),
    (3,  "Squares and Square Roots",                    6,  "hegp1"),
    (4,  "Cubes and Cube Roots",                        7,  "hegp1"),
    (5,  "Playing with Numbers",                        16, "hegp1"),
    (6,  "Algebraic Expressions and Identities",        9,  "hegp1"),
    (7,  "Factorisation",                               14, "hegp1"),
    (8,  "Linear Equations in One Variable",            2,  "hegp1"),
    (9,  "Comparing Quantities",                        8,  "hegp1"),
    (10, "Direct and Indirect Variations",              13, "hegp1"),
    (11, "Understanding Quadrilaterals",                3,  "hegp1"),
    (12, "Visualising Solid Shapes",                    10, "hegp1"),
    (13, "Practical Geometry",                          4,  "hegp1"),
    (14, "Mensuration",                                 11, "hegp1"),
    (15, "Introduction to Graphs",                      15, "hegp1"),
    (16, "Data Handling",                               5,  "hegp1"),
]

# NCERT Curiosity (hecu1) chapters for Class 8 Science — exactly match BNPS order
BNPS_SCIENCE_CHAPTERS = [
    (1,  "Exploring the Investigative World of Science",         1,  "hecu1"),
    (2,  "The Invisible Living World: Beyond Our Naked Eye",     2,  "hecu1"),
    (3,  "Health: The Ultimate Treasure",                        3,  "hecu1"),
    (4,  "Electricity: Magnetic and Heating Effects",            4,  "hecu1"),
    (5,  "Exploring Forces",                                     5,  "hecu1"),
    (6,  "Pressure, Winds, Storms, and Cyclones",                6,  "hecu1"),
    (7,  "Particulate Nature of Matter",                         7,  "hecu1"),
    (8,  "Nature of Matter: Elements, Compounds, and Mixtures",  8,  "hecu1"),
    (9,  "The Amazing World of Solutes, Solvents and Solutions", 9,  "hecu1"),
    (10, "Light: Mirrors and Lenses",                            10, "hecu1"),
    (11, "Keeping Time with the Skies",                          11, "hecu1"),
    (12, "How Nature Works in Harmony",                          12, "hecu1"),
    (13, "Our Home: Earth, a Unique Life Sustaining Planet",     13, "hecu1"),
]

# NCERT Exploring Society (hees1) for Social Studies
BNPS_SST_CHAPTERS = [
    (1, "Natural Resources: Treasures of The Earth",                  1, "hees1"),
    (2, "The Changing Political Landscape of India",                  2, "hees1"),
    (3, "The Rise of the Marathas",                                   3, "hees1"),
    (4, "The Colonial Transformation of India",                       4, "hees1"),
    (5, "From Ballot to Bharat: The Spirit of Universal Franchise",   5, "hees1"),
    (6, "The Parliamentary System: Legislature and Executive",        6, "hees1"),
    (7, "Resources at Work",                                          7, "hees1"),
]

# NCERT Poorvi (hepr1) for English — map by unit/chapter
BNPS_ENGLISH_CHAPTERS = [
    (1,  "The Time Machine",                        1,  "hepr1"),
    (2,  "When the Mop Count Did Not Tally",        2,  "hepr1"),
    (3,  "Stopping by Woods on a Snowy Evening",    3,  "hepr1"),
    (4,  "The Portrait of a Lady",                  4,  "hepr1"),
    (5,  "Stuart Little",                           5,  "hepr1"),
    (6,  "Robots in Everyday Life",                 6,  "hepr1"),
    (7,  "Knowing Your Strengths",                  7,  "hepr1"),
    (8,  "The Children's Hour",                     8,  "hepr1"),
    (9,  "That Little Square Box",                  9,  "hepr1"),
    (10, "Haunted",                                 10, "hepr1"),
    (11, "On the Grasshopper and Cricket",          11, "hepr1"),
    (12, "The Canterville Ghost",                   12, "hepr1"),
    (13, "Night of the Scorpion",                   13, "hepr1"),
]

ALL_SUBJECTS = {
    "Mathematics":     BNPS_MATH_CHAPTERS,
    "Science":         BNPS_SCIENCE_CHAPTERS,
    "Social Studies":  BNPS_SST_CHAPTERS,
    "English":         BNPS_ENGLISH_CHAPTERS,
}


async def download_pdf(session: aiohttp.ClientSession, url: str, path: str) -> bool:
    try:
        async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            if resp.status != 200:
                return False
            data = await resp.read()
            if not data.startswith(b"%PDF"):
                return False
            with open(path, "wb") as f:
                f.write(data)
            return True
    except Exception as e:
        print(f"  [ERR] {url}: {e}")
        return False


async def download_subject(session: aiohttp.ClientSession, subject: str, chapters: list) -> dict:
    subject_dir = os.path.join(OUTPUT_DIR, subject)
    os.makedirs(subject_dir, exist_ok=True)

    results = {"subject": subject, "chapters": [], "downloaded": 0, "failed": 0}

    for (bnps_order, bnps_name, ncert_ch_no, book_code) in chapters:
        filename = f"chapter_{bnps_order:02d}.pdf"
        filepath = os.path.join(subject_dir, filename)

        if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
            print(f"  [SKIP] {subject} Ch{bnps_order}: {bnps_name} (already downloaded)")
            results["chapters"].append({
                "bnps_order": bnps_order,
                "bnps_name": bnps_name,
                "ncert_chapter": ncert_ch_no,
                "file": filename,
                "status": "cached",
            })
            results["downloaded"] += 1
            continue

        url = f"{NCERT_PDF_BASE}{book_code}{ncert_ch_no:02d}.pdf"
        print(f"  [DL]  {subject} Ch{bnps_order}: {bnps_name}")
        print(f"        → {url}")

        ok = await download_pdf(session, url, filepath)
        status = "ok" if ok else "failed"
        if ok:
            size_kb = os.path.getsize(filepath) // 1024
            print(f"  [OK]  Downloaded {size_kb} KB")
            results["downloaded"] += 1
        else:
            print(f"  [FAIL] Could not download")
            results["failed"] += 1

        results["chapters"].append({
            "bnps_order": bnps_order,
            "bnps_name": bnps_name,
            "ncert_chapter": ncert_ch_no,
            "file": filename,
            "status": status,
        })

        await asyncio.sleep(0.5)

    return results


async def run():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 60)
    print("BNPS Grade 8 PDF Downloader")
    print(f"Output: {OUTPUT_DIR}")
    print("=" * 60)

    connector = aiohttp.TCPConnector(limit=3)
    async with aiohttp.ClientSession(connector=connector) as session:
        all_results = {}
        for subject, chapters in ALL_SUBJECTS.items():
            print(f"\n[{subject}] — {len(chapters)} chapters")
            result = await download_subject(session, subject, chapters)
            all_results[subject] = result

    # Save metadata JSON
    import json
    from datetime import datetime, timezone

    metadata = {
        "school": "brooklyn_national",
        "school_name": "Brooklyn National Public School",
        "grade": "8",
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
        "ncert_source": "ncert.nic.in",
        "subjects": all_results,
    }
    meta_path = os.path.join(OUTPUT_DIR, "metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"\n[DONE] Metadata saved: {meta_path}")

    total_ok = sum(r["downloaded"] for r in all_results.values())
    total_fail = sum(r["failed"] for r in all_results.values())
    print(f"       Downloaded: {total_ok} | Failed: {total_fail}")


if __name__ == "__main__":
    asyncio.run(run())
