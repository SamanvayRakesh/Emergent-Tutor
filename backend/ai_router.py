"""AI Request Router — category + model + token selection.

Category A → no LLM (curriculum lookups)
Category B → gpt-4o-mini (definitions, flashcards, short answers)
Category C → gpt-4o-mini normally; gpt-4o only for elite plan + normal budget

Max tokens:
  normal   budget: A=0, B=200, C=500
  near     budget: B=120, C=200  (70-90% cap used)
  critical budget: all=120       (90-100%)
  over     budget: BLOCK
"""

import re
from typing import Literal

Category = Literal["A", "B", "C"]

_CATEGORY_A = re.compile(
    r"\b(list chapters?|show chapters?|what chapters?|syllabus|topics? in|"
    r"curriculum|which chapters?|how many chapters?|next chapter|previous chapter)\b",
    re.IGNORECASE,
)

_CATEGORY_C = re.compile(
    r"\b(derive|derivation|proof|prove|integrate|differentiation|"
    r"multi.?step|analyze|analyse|compare and contrast|evaluate|"
    r"implications|why does|how does.*work|explain in depth|explain thoroughly|"
    r"step by step|step-by-step|solve this problem|work out|"
    r"electromagnetism|thermodynamics|quantum|organic chemistry|"
    r"genetics?|heredity|photosynthesis mechanism|"
    r"trigonometric identity|logarithm|coordinate geometry)\b",
    re.IGNORECASE,
)

_CATEGORY_B_KW = {
    "define","definition","what is","what are","meaning of",
    "flashcard","quiz me","give me a quiz","example of","revision",
    "revise","notes on","summarize","summary","difference between",
    "types of","list","name",
}

# Response length limits per budget tier (tokens)
# Category C normal = 1800 tokens ≈ 1350 words (supports 1500-word limit)
_MAX_TOKENS = {
    #              normal  near  critical
    "A":          (0,      0,    0),
    "B":          (800,    300,  150),
    "C":          (1800,   600,  200),
}


def classify_request(text: str, word_count: int) -> Category:
    if _CATEGORY_A.search(text):
        return "A"
    if word_count > 50 or _CATEGORY_C.search(text):
        return "C"
    lower = text.lower()
    if any(kw in lower for kw in _CATEGORY_B_KW) or word_count <= 12:
        return "B"
    return "C"


def build_routing_decision(
    text: str,
    plan_id: str,
    near_budget: bool = False,
    critical: bool = False,
    over_budget: bool = False,
) -> dict:
    wc = len(text.strip().split())
    category = classify_request(text, wc)

    if over_budget:
        return {
            "category": category, "model": None,
            "max_tokens": 0, "word_count": wc,
            "blocked": True,
            "block_reason": "monthly_token_cap_reached",
        }

    # Model selection
    if critical or near_budget:
        model = "gpt-4o-mini"
    elif category == "C" and plan_id == "elite":
        model = "gpt-4o"
    else:
        model = "gpt-4o-mini"

    # Token budget
    tier = 2 if critical else (1 if near_budget else 0)
    max_tokens = _MAX_TOKENS[category][tier]
    if category == "A":
        max_tokens = 0   # no LLM call

    return {
        "category": category,
        "model": model,
        "max_tokens": max_tokens,
        "word_count": wc,
        "blocked": False,
        "block_reason": None,
    }
