"""Knowledge Base — fast retrieval layer that sits in front of the LLM.

At chat time:
  1. Try MongoDB text search against question_bank
  2. If match score is good enough → return stored answer (no LLM generation needed)
  3. If no match → return None → caller falls back to LLM

This is what kills 80-90% of per-question LLM costs.
"""

import re
from typing import Optional
from core import db, logger

# Minimum score to consider a KB match trustworthy
MIN_MATCH_SCORE = 0.45

# How many KB candidates to fetch and re-rank
CANDIDATE_LIMIT = 5


def _keyword_score(query: str, doc: dict) -> float:
    """Simple keyword overlap score — fast, no ML needed."""
    query_words = set(re.findall(r"\b\w{3,}\b", query.lower()))
    # Score against question + keywords + topic
    searchable = " ".join([
        doc.get("question", ""),
        " ".join(doc.get("variants", [])),
        " ".join(doc.get("keywords", [])),
        doc.get("topic", ""),
    ]).lower()
    doc_words = set(re.findall(r"\b\w{3,}\b", searchable))
    if not query_words or not doc_words:
        return 0.0
    intersection = query_words & doc_words
    # Jaccard similarity
    union = query_words | doc_words
    return len(intersection) / len(union)


async def find_kb_answer(
    query: str,
    class_level: str,
    subject: str,
    chapter_no: Optional[int] = None,
) -> Optional[dict]:
    """Search the question bank for a matching answer.

    Returns:
        {answer, question, topic, difficulty, score, source: 'kb'} if found
        None if no good match
    """
    if not query or len(query.strip()) < 5:
        return None

    try:
        # Build filter — always scope to class + subject
        base_filter: dict = {
            "class_level": str(class_level),
            "subject": {"$regex": subject, "$options": "i"},
        }
        if chapter_no:
            base_filter["chapter_no"] = chapter_no

        # MongoDB full-text search
        text_filter = {**base_filter, "$text": {"$search": query}}
        candidates = await db.question_bank.find(
            text_filter,
            {"score": {"$meta": "textScore"}, "_id": 0},
        ).sort([("score", {"$meta": "textScore"})]).limit(CANDIDATE_LIMIT).to_list(CANDIDATE_LIMIT)

        # If text search got nothing, fall back to a regex scan on keywords
        if not candidates:
            # Extract significant words from query
            words = re.findall(r"\b\w{4,}\b", query.lower())
            if not words:
                return None
            regex_filter = {
                **base_filter,
                "$or": [
                    {"keywords": {"$in": words}},
                    {"topic": {"$regex": "|".join(words[:3]), "$options": "i"}},
                ],
            }
            candidates = await db.question_bank.find(
                regex_filter, {"_id": 0}
            ).limit(CANDIDATE_LIMIT).to_list(CANDIDATE_LIMIT)

        if not candidates:
            return None

        # Re-rank by keyword overlap score
        scored = []
        for doc in candidates:
            ks = _keyword_score(query, doc)
            mongo_score = doc.get("score", 0)
            # Weighted blend: keyword overlap matters more for NCERT concepts
            combined = (ks * 0.65) + (min(mongo_score, 5) / 5 * 0.35)
            scored.append((combined, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        best_score, best_doc = scored[0]

        if best_score < MIN_MATCH_SCORE:
            logger.debug(f"KB miss (score {best_score:.2f}): {query[:60]}")
            return None

        # Increment hit counter (async fire-and-forget)
        await db.question_bank.update_one(
            {"question": best_doc["question"]},
            {"$inc": {"hit_count": 1}},
        )

        logger.info(f"KB hit (score {best_score:.2f}): {query[:60]}")
        return {
            "answer": best_doc["answer"],
            "question": best_doc["question"],
            "topic": best_doc.get("topic", ""),
            "difficulty": best_doc.get("difficulty", "medium"),
            "chapter_title": best_doc.get("chapter_title", ""),
            "score": round(best_score, 3),
            "source": "kb",
        }

    except Exception as e:
        logger.warning(f"KB search error: {e}")
        return None


async def get_kb_stats() -> dict:
    """Quick stats for the analytics dashboard."""
    try:
        total = await db.question_bank.count_documents({})
        top_hits = await db.question_bank.find(
            {}, {"_id": 0, "question": 1, "hit_count": 1, "chapter_title": 1}
        ).sort("hit_count", -1).limit(10).to_list(10)
        return {"total_qa_pairs": total, "top_questions": top_hits}
    except Exception:
        return {"total_qa_pairs": 0, "top_questions": []}
