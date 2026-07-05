"""
Grade 8 BNPS PDF Downloader — Final Authoritative Script
=========================================================
Downloads ALL Grade 8 PDFs from NCERT for:
  • Science (Curiosity):       hecu1{01-13}.pdf  — 13 chapters
  • Social Science (Exploring Society): hees1{01-07}.pdf  — 7 chapters
  • Mathematics (Ganita Prakash Part 1 + Part 2): hegp1{01-07} + hegp2{02-07}

Chapter names follow the BNPS school_curriculum.py naming convention exactly.
English is NOT downloaded (removed from curriculum).

Run with: python3 /app/backend/scripts/download_grade8_final.py
"""

import os
import sys
import time
import ssl
import urllib.request
import urllib.error

NCERT_BASE = "https://ncert.nic.in/textbook/pdf/"
OUTPUT_DIR = "/app/backend/curriculum_data/bnps_pdfs/grade8"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://ncert.nic.in/",
    "Accept": "application/pdf,*/*",
}

# ─── Chapter mappings ────────────────────────────────────────────────────────
# Format: (bnps_order, bnps_name, ncert_book_code, ncert_ch_no)

SCIENCE_CHAPTERS = [
    (1,  "Exploring the Investigative World of Science",        "hecu1", 1),
    (2,  "The Invisible Living World: Beyond Our Naked Eye",    "hecu1", 2),
    (3,  "Health: The Ultimate Treasure",                       "hecu1", 3),
    (4,  "Electricity: Magnetic and Heating Effects",           "hecu1", 4),
    (5,  "Exploring Forces",                                    "hecu1", 5),
    (6,  "Pressure, Winds, Storms, and Cyclones",               "hecu1", 6),
    (7,  "Particulate Nature of Matter",                        "hecu1", 7),
    (8,  "Nature of Matter: Elements, Compounds, and Mixtures", "hecu1", 8),
    (9,  "The Amazing World of Solutes, Solvents and Solutions","hecu1", 9),
    (10, "Light: Mirrors and Lenses",                           "hecu1", 10),
    (11, "Keeping Time with the Skies",                         "hecu1", 11),
    (12, "How Nature Works in Harmony",                         "hecu1", 12),
    (13, "Our Home: Earth, a Unique Life Sustaining Planet",    "hecu1", 13),
]

SOCIAL_SCIENCE_CHAPTERS = [
    (1, "Natural Resources: Treasures of The Earth",                  "hees1", 1),
    (2, "The Changing Political Landscape of India",                   "hees1", 2),
    (3, "The Rise of the Marathas",                                    "hees1", 3),
    (4, "The Colonial Transformation of India",                        "hees1", 4),
    (5, "From Ballot to Bharat: The Spirit of Universal Franchise",    "hees1", 5),
    (6, "The Parliamentary System: Legislature and Executive",         "hees1", 6),
    (7, "Resources at Work",                                           "hees1", 7),
]

# Mathematics: hegp1 (Part 1) has ch01-07, hegp2 (Part 2) has ch02-07
# BNPS chapter → correct NCERT book+chapter mapping
MATH_CHAPTERS = [
    (1,  "Rational Numbers",                          "hegp1", 1),   # hegp101
    (2,  "Exponents and Powers",                      "hegp2", 2),   # hegp202
    (3,  "Squares and Square Roots",                  "hegp1", 6),   # hegp106
    (4,  "Cubes and Cube Roots",                      "hegp1", 7),   # hegp107
    (5,  "Playing with Numbers",                      "hegp2", 3),   # hegp203
    (6,  "Algebraic Expressions and Identities",      "hegp2", 4),   # hegp204
    (7,  "Factorisation",                             "hegp2", 5),   # hegp205
    (8,  "Linear Equations in One Variable",          "hegp1", 2),   # hegp102
    (9,  "Comparing Quantities",                      "hegp2", 6),   # hegp206
    (10, "Direct and Indirect Variations",            "hegp2", 7),   # hegp207
    (11, "Understanding Quadrilaterals",              "hegp1", 3),   # hegp103
    # 12 Visualising Solid Shapes — no PDF available
    (13, "Practical Geometry",                        "hegp1", 4),   # hegp104
    (14, "Mensuration",                               "hegp1", 5),   # TESTING hegp105 (Data Handling is ch5 in part1)
    (16, "Data Handling",                             "hegp1", 5),   # hegp105
]

# Correct mapping after analysis:
# hegp1: 01=Rational, 02=LinearEq, 03=Quadrilaterals, 04=PractGeom, 05=DataHandling, 06=SqRoots, 07=CubeRoots
# hegp2: 02=Exponents, 03=PlayingNums, 04=AlgExpr, 05=Factorisation, 06=ComparingQty, 07=DirectInverse

MATH_CHAPTERS_FINAL = [
    (1,  "Rational Numbers",                          "hegp1", 1),
    (2,  "Exponents and Powers",                      "hegp2", 2),
    (3,  "Squares and Square Roots",                  "hegp1", 6),
    (4,  "Cubes and Cube Roots",                      "hegp1", 7),
    (5,  "Playing with Numbers",                      "hegp2", 3),
    (6,  "Algebraic Expressions and Identities",      "hegp2", 4),
    (7,  "Factorisation",                             "hegp2", 5),
    (8,  "Linear Equations in One Variable",          "hegp1", 2),
    (9,  "Comparing Quantities",                      "hegp2", 6),
    (10, "Direct and Indirect Variations",            "hegp2", 7),
    (11, "Understanding Quadrilaterals",              "hegp1", 3),
    (13, "Practical Geometry",                        "hegp1", 4),
    (16, "Data Handling",                             "hegp1", 5),
    # Chapter 12 (Visualising Solid Shapes), 14 (Mensuration), 15 (Intro Graphs)
    # — not available as separate PDFs in NCERT 2024-25 new textbooks
]

ALL_SUBJECTS = {
    "Science":        SCIENCE_CHAPTERS,
    "Social Science": SOCIAL_SCIENCE_CHAPTERS,
    "Mathematics":    MATH_CHAPTERS_FINAL,
}


def download_pdf(url: str, dest: str, force: bool = False) -> tuple[bool, str]:
    """Download a PDF from NCERT. Returns (success, message)."""
    if not force and os.path.exists(dest) and os.path.getsize(dest) > 10000:
        size_kb = os.path.getsize(dest) // 1024
        return True, f"CACHED ({size_kb} KB)"

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=45) as resp:
            if resp.status != 200:
                return False, f"HTTP {resp.status}"
            data = resp.read()
            if not data.startswith(b"%PDF"):
                return False, f"Not a PDF (got: {data[:8]})"
            if len(data) < 10000:
                return False, f"File too small ({len(data)} bytes)"
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as f:
                f.write(data)
            size_kb = len(data) // 1024
            return True, f"OK ({size_kb} KB)"
    except Exception as e:
        return False, f"ERROR: {e}"


def remove_english():
    """Remove English PDF folder entirely."""
    import shutil
    eng_dir = os.path.join(OUTPUT_DIR, "English")
    if os.path.exists(eng_dir):
        shutil.rmtree(eng_dir)
        print("  [DELETED] English folder removed")
    else:
        print("  [SKIP] English folder not found")


def rename_social_studies():
    """Rename 'Social Studies' folder to 'Social Science' if needed."""
    import shutil
    old = os.path.join(OUTPUT_DIR, "Social Studies")
    new = os.path.join(OUTPUT_DIR, "Social Science")
    if os.path.exists(old) and not os.path.exists(new):
        shutil.move(old, new)
        print("  [RENAMED] Social Studies → Social Science")
    elif os.path.exists(old) and os.path.exists(new):
        # Merge: copy missing files from old to new
        for f in os.listdir(old):
            src = os.path.join(old, f)
            dst = os.path.join(new, f)
            if not os.path.exists(dst):
                shutil.copy2(src, dst)
        shutil.rmtree(old)
        print("  [MERGED] Social Studies merged into Social Science, old folder removed")
    elif os.path.exists(new):
        print("  [OK] Social Science folder already exists")


def run():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 65)
    print("BNPS Grade 8 Final PDF Downloader")
    print(f"Output: {OUTPUT_DIR}")
    print("=" * 65)

    # 1. Remove English
    print("\n[CLEANUP] Removing English...")
    remove_english()

    # 2. Rename Social Studies → Social Science
    print("\n[CLEANUP] Fixing folder names...")
    rename_social_studies()

    # 3. Download all subjects
    report = {}
    for subject, chapters in ALL_SUBJECTS.items():
        print(f"\n{'=' * 65}")
        print(f"[{subject}] — {len(chapters)} chapters")
        print("=" * 65)

        subject_dir = os.path.join(OUTPUT_DIR, subject)
        os.makedirs(subject_dir, exist_ok=True)

        ok_count = 0
        fail_count = 0
        results = []

        for (bnps_order, bnps_name, book_code, ncert_ch_no) in chapters:
            filename = f"chapter_{bnps_order:02d}.pdf"
            filepath = os.path.join(subject_dir, filename)
            url = f"{NCERT_BASE}{book_code}{ncert_ch_no:02d}.pdf"

            existing = os.path.exists(filepath) and os.path.getsize(filepath) > 10000

            print(f"  Ch{bnps_order:02d}: {bnps_name[:52]}")
            print(f"         URL: {url}")

            success, msg = download_pdf(url, filepath, force=False)

            status = "CACHED" if "CACHED" in msg else ("OK" if success else "FAIL")
            print(f"         → {status}: {msg}")

            results.append({
                "ch": bnps_order, "name": bnps_name,
                "url": url, "file": filepath,
                "success": success, "msg": msg
            })

            if success:
                ok_count += 1
            else:
                fail_count += 1
                # Retry once with delay
                print(f"         Retrying in 3s...")
                time.sleep(3)
                success2, msg2 = download_pdf(url, filepath, force=True)
                if success2:
                    print(f"         → RETRY OK: {msg2}")
                    ok_count += 1
                    fail_count -= 1
                    results[-1]["success"] = True
                    results[-1]["msg"] = f"RETRY: {msg2}"
                else:
                    print(f"         → RETRY FAIL: {msg2}")

            time.sleep(0.3)

        report[subject] = {"ok": ok_count, "fail": fail_count, "chapters": results}
        print(f"\n  Summary: {ok_count} downloaded/cached, {fail_count} failed")

    # ── Final validation report ──────────────────────────────────────────────
    print("\n" + "=" * 65)
    print("FINAL VALIDATION REPORT")
    print("=" * 65)

    total_ok = 0
    total_fail = 0
    for subject, data in report.items():
        print(f"\n[{subject}] {data['ok']}/{data['ok'] + data['fail']} chapters OK")
        for ch in data["chapters"]:
            icon = "✓" if ch["success"] else "✗"
            size = ""
            if ch["success"] and os.path.exists(ch["file"]):
                size = f" [{os.path.getsize(ch['file']) // 1024} KB]"
            print(f"   {icon} Ch{ch['ch']:02d}: {ch['name'][:50]}{size}")
        total_ok += data["ok"]
        total_fail += data["fail"]

    print(f"\n{'=' * 65}")
    print(f"TOTAL: {total_ok} OK | {total_fail} FAILED")
    if total_fail == 0:
        print("ALL PDFS DOWNLOADED SUCCESSFULLY ✓")
    else:
        print(f"WARNING: {total_fail} PDFs could not be downloaded")
    print("=" * 65)

    # List final directory structure
    print("\nFinal directory structure:")
    for subject in ["Science", "Social Science", "Mathematics"]:
        sdir = os.path.join(OUTPUT_DIR, subject)
        if os.path.exists(sdir):
            files = sorted(os.listdir(sdir))
            print(f"  {subject}/: {len(files)} files → {', '.join(files[:5])}{'...' if len(files)>5 else ''}")

    return total_fail == 0


if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)
