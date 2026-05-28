"""NCERT AI-ready scraper — reads ncert_books.json and downloads real NCERT PDFs
with verified chapter titles (via learncbse.in / byjus.com cross-reference).
Outputs /app/backend/curriculum_data/ncert_ai_ready/ncert_ai_metadata.json
"""
import asyncio
import aiohttp
import os
import json
import logging
import re
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

CURRICULUM_DIR = "/app/backend/curriculum_data"
OUTPUT_DIR = os.path.join(CURRICULUM_DIR, "ncert_ai_ready")
BOOKS_JSON = os.path.join(CURRICULUM_DIR, "ncert_books.json")

ALLOWED_SUBJECTS = ["english", "mathematics", "math", "science", "social science", "social studies"]
BLOCKED_LANGUAGES = ["hindi", "urdu", "sanskrit", "marathi", "gujarati", "tamil", "telugu", "kannada", "malayalam", "bengali", "punjabi"]

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s",
                    filename=os.path.join(CURRICULUM_DIR, "scraper.log"))


class NCERTAIScraper:
    PDF_BASE_URL = "https://ncert.nic.in/textbook/pdf/"

    def __init__(self, output_dir=OUTPUT_DIR):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        self.semaphore = asyncio.Semaphore(3)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def fetch_text(self, session, url):
        async with self.semaphore:
            try:
                async with session.get(url, headers=self.headers, timeout=20) as response:
                    if response.status == 200:
                        return await response.text()
                    logging.error(f"Failed URL {url} | Status {response.status}")
            except Exception as e:
                logging.error(f"Fetch Error: {url} | {e}")
        return None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def download_pdf(self, session, url, filepath):
        async with self.semaphore:
            try:
                async with session.get(url, headers=self.headers, timeout=30) as response:
                    if response.status != 200:
                        return False
                    content = await response.read()
                    if not content.startswith(b"%PDF"):
                        logging.error(f"Invalid PDF: {url}")
                        return False
                    with open(filepath, "wb") as f:
                        f.write(content)
                    return True
            except Exception as e:
                logging.error(f"Download Error: {url} | {e}")
        return False

    async def get_real_chapter_titles(self, session, class_num, subject):
        slug = subject.lower().replace(" ", "-")
        urls = [
            f"https://www.learncbse.in/ncert-solutions-for-class-{class_num}-{slug}/",
            f"https://byjus.com/ncert-solutions-class-{class_num}-{slug}/",
        ]
        titles = {}
        for url in urls:
            html = await self.fetch_text(session, url)
            if not html:
                continue
            soup = BeautifulSoup(html, "html.parser")
            elements = soup.find_all(["li", "a", "p", "h2", "h3"])
            for element in elements:
                text = element.get_text(strip=True)
                match = re.search(r"Chapter\s+(\d+)[:\-\s]+(.+)", text, re.IGNORECASE)
                if match:
                    chapter_num = match.group(1).zfill(2)
                    title = match.group(2).split("–")[0].split("(")[0].strip()
                    if len(title) > 2:
                        titles[chapter_num] = title
            if titles:
                return titles
        return titles

    async def scrape_book(self, session, book):
        class_num = book["class"]
        subject = book["subject"]
        book_title = book["book_title"]
        book_code = book["book_code"]
        total_chapters = int(book["total_chapters"])
        safe_title = book_title.replace("/", "-").replace("\\", "-")
        save_dir = os.path.join(self.output_dir, f"Class_{class_num}", safe_title)
        os.makedirs(save_dir, exist_ok=True)

        print(f"[INFO] Processing: Class {class_num} | {subject} | {book_title}")
        chapter_titles = await self.get_real_chapter_titles(session, class_num, subject)

        metadata = {
            "class": class_num, "subject": subject,
            "book_title": book_title, "book_code": book_code, "chapters": [],
        }

        # Prelims
        prelims_url = f"{self.PDF_BASE_URL}{book_code}ps.pdf"
        prelims_path = os.path.join(save_dir, "prelims.pdf")
        if await self.download_pdf(session, prelims_url, prelims_path):
            metadata["chapters"].append({"id": "prelims", "title": "Table of Contents", "file": "prelims.pdf"})

        # Chapters
        tasks = []
        for i in range(1, total_chapters + 1):
            chapter_id = f"{i:02d}"
            chapter_title = chapter_titles.get(chapter_id, f"Chapter {i}")
            filename = f"chapter_{chapter_id}.pdf"
            filepath = os.path.join(save_dir, filename)
            pdf_url = f"{self.PDF_BASE_URL}{book_code}{chapter_id}.pdf"
            tasks.append(self.download_pdf(session, pdf_url, filepath))
            metadata["chapters"].append({
                "chapter_no": i, "title": chapter_title,
                "file": filename, "pdf_url": pdf_url,
            })

        results = await asyncio.gather(*tasks)
        successful = sum(results)
        print(f"[OK]   {book_title} — {successful}/{total_chapters} chapter PDFs")
        return metadata

    async def run(self):
        if not os.path.exists(BOOKS_JSON):
            print("[ERR] Missing ncert_books.json")
            return
        with open(BOOKS_JSON, "r", encoding="utf-8") as f:
            all_books = json.load(f)

        target_books = []
        for book in all_books:
            try:
                class_num = int(book["class"])
            except Exception:
                continue
            if not (6 <= class_num <= 12):
                continue
            title = book["book_title"].lower()
            subject = book["subject"].lower()
            if any(lang in title for lang in BLOCKED_LANGUAGES) or any(lang in subject for lang in BLOCKED_LANGUAGES):
                continue
            if not any(s in subject for s in ALLOWED_SUBJECTS):
                continue
            target_books.append(book)

        print(f"[INFO] Books selected after filter: {len(target_books)}")

        connector = aiohttp.TCPConnector(limit_per_host=3)
        async with aiohttp.ClientSession(connector=connector) as session:
            final_metadata = []
            for book in target_books:
                try:
                    metadata = await self.scrape_book(session, book)
                    final_metadata.append(metadata)
                except Exception as e:
                    logging.error(f"Book failed: {book['book_title']} | {e}")
                    print(f"[ERR] Book failed: {book['book_title']} | {e}")

        metadata_path = os.path.join(self.output_dir, "ncert_ai_metadata.json")
        from datetime import datetime, timezone
        wrapper = {
            "academic_year": "2025-26",
            "source": "ncert.nic.in (official NCERT textbook PDFs) + learncbse.in/byjus.com (chapter title cross-reference)",
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "books": final_metadata,
        }
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(wrapper, f, indent=2, ensure_ascii=False)
        print(f"[DONE] Saved: {metadata_path}")


if __name__ == "__main__":
    scraper = NCERTAIScraper()
    asyncio.run(scraper.run())
