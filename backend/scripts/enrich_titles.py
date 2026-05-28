"""Post-processing: enrich ncert_ai_metadata.json with real chapter titles
extracted from the downloaded prelims PDFs (table of contents pages).
"""
import json
import os
import re
import fitz  # pymupdf

METADATA = "/app/backend/curriculum_data/ncert_ai_ready/ncert_ai_metadata.json"
BASE_DIR = "/app/backend/curriculum_data/ncert_ai_ready"


def extract_toc_titles(prelims_pdf_path: str, expected_count: int) -> dict:
    """Parse the prelims PDF's table of contents page(s) for chapter titles.
    Returns {chapter_no: title}."""
    if not os.path.exists(prelims_pdf_path):
        return {}
    titles = {}
    try:
        doc = fitz.open(prelims_pdf_path)
        full = ""
        for page in doc:
            full += page.get_text() + "\n"
        doc.close()
    except Exception:
        return {}

    # Locate the Contents section to avoid pulling junk from earlier pages.
    # Look for the standalone "Contents" heading (not "Contents of the textbooks...")
    scope = full
    for m in re.finditer(r"(?im)^\s*Contents\s*$", full):
        scope = full[m.start():m.start() + 12000]
        break
    else:
        m = re.search(r"\n\s*1\.\s*\n", full)
        if m:
            scope = full[m.start():m.start() + 12000]

    lines = [line.strip() for line in scope.split("\n")]
    # Pattern: a line is just "1." or "12." and the NEXT non-empty line is the chapter title
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.fullmatch(r"(\d{1,2})\.?", line)
        if m:
            num = int(m.group(1))
            # Look at next non-empty line
            j = i + 1
            while j < len(lines) and not lines[j]:
                j += 1
            if j < len(lines):
                cand = lines[j]
                # Skip sub-section lines like "1.1" or empty / digits
                if (cand and 3 <= len(cand) <= 80
                        and not re.match(r"^\d+\.?\d*", cand)
                        and cand[0].isupper()
                        and 1 <= num <= expected_count + 2
                        and num not in titles):
                    titles[num] = cand
        i += 1

    # Fallback: "1. Real Numbers ........ 12" inline
    if len(titles) < expected_count // 2:
        for m in re.finditer(r"^\s*(\d{1,2})\.\s+([A-Z][A-Za-z0-9 ,'\-/&()]{3,70}?)\s*\.{2,}\s*\d+", full, re.MULTILINE):
            num = int(m.group(1))
            title = m.group(2).strip()
            if 1 <= num <= expected_count and num not in titles:
                titles[num] = title

    # Fallback 2: "Chapter 1 : Real Numbers"
    if len(titles) < expected_count // 2:
        for m in re.finditer(r"Chapter\s+(\d+)\s*[:\-–—.]?\s*([A-Z][A-Za-z0-9 ,'\-/&()]+?)(?=\s+\d+\s*$|\s+\.\.|\n)", full, re.MULTILINE):
            num = int(m.group(1))
            title = m.group(2).strip().rstrip(".").strip()
            if 3 <= len(title) <= 80 and num not in titles:
                titles[num] = title

    return titles


def main():
    with open(METADATA, "r", encoding="utf-8") as f:
        data = json.load(f)

    enriched = 0
    for book in data.get("books", []):
        cls = book["class"]
        bt = book["book_title"]
        safe = bt.replace("/", "-").replace("\\", "-")
        prelims = os.path.join(BASE_DIR, f"Class_{cls}", safe, "prelims.pdf")
        chapter_count = sum(1 for c in book["chapters"] if c.get("chapter_no"))
        toc = extract_toc_titles(prelims, chapter_count)
        if not toc:
            continue
        for ch in book["chapters"]:
            no = ch.get("chapter_no")
            if no and toc.get(no):
                # Only overwrite if current name is the generic fallback
                if ch.get("title", "").startswith("Chapter ") or len(ch.get("title", "")) < 3:
                    ch["title"] = toc[no]
                    enriched += 1
        print(f"[OK] Class {cls} | {bt} → extracted {len(toc)} titles from prelims")

    with open(METADATA, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\n[DONE] Enriched {enriched} chapter titles.")


if __name__ == "__main__":
    main()
