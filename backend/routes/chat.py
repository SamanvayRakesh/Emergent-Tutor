"""Chat sessions + streaming AI tutor.
Cost-optimised stack:
  1. Category A  → curriculum DB, zero LLM cost
  2. KB hit      → rephrase stored answer, ~130 tokens (~₹0.01)
  3. KB miss     → full LLM, capped by budget tier
  4. Over budget → static fallback, zero LLM cost
"""

import uuid
import json
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from core import db, openai_client, logger, get_current_user
from curriculum_engine import build_ai_chapter_manifest, get_verified_chapters
from plan_gates import increment_usage, get_user_plan
from credits import deduct_credits, deduct_credits_for_chat, calculate_chat_credits, CHAT_WORD_LIMIT
from models import ChatSessionCreate, ChatMessageRequest
from adaptive_engine import (
    get_student_profile, build_compact_memory,
    record_token_usage, check_budget, update_topic_performance,
)
from ai_router import build_routing_decision
from knowledge_base import find_kb_answer, get_kb_stats

router = APIRouter()

# Static fallback when token cap is fully exhausted
_BUDGET_EXHAUSTED_MSG = (
    "You've reached your monthly AI limit for this plan. "
    "Your limit resets at the start of next month, or you can upgrade your plan "
    "to continue learning right now. 📚"
)


# ── Session CRUD ─────────────────────────────────────────────────────────────

@router.post("/chat/sessions")
async def create_chat_session(body: ChatSessionCreate, request: Request):
    user = await get_current_user(request)
    if body.class_level != user.get("class_level"):
        raise HTTPException(
            status_code=403,
            detail=f"You can only create chats for your active grade (Class {user.get('class_level')}). Change grade in Profile to access other classes.",
        )
    session_id = f"chat_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "session_id": session_id, "user_id": user["user_id"],
        "class_level": body.class_level, "subject": body.subject,
        "chapter": body.chapter, "chapter_id": body.chapter_id,
        "title": f"{body.subject} - {body.chapter}",
        "message_count": 0, "created_at": now, "updated_at": now,
    }
    await db.chat_sessions.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.get("/chat/sessions")
async def list_chat_sessions(request: Request):
    user = await get_current_user(request)
    return await db.chat_sessions.find(
        {"user_id": user["user_id"]}, {"_id": 0}
    ).sort("updated_at", -1).limit(20).to_list(20)


@router.get("/chat/sessions/{session_id}")
async def get_chat_session(session_id: str, request: Request):
    user = await get_current_user(request)
    session = await db.chat_sessions.find_one(
        {"session_id": session_id, "user_id": user["user_id"]}, {"_id": 0}
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = await db.messages.find(
        {"session_id": session_id}, {"_id": 0}
    ).sort("timestamp", 1).to_list(200)
    return {"session": session, "messages": messages}


@router.delete("/chat/sessions/{session_id}")
async def delete_chat_session(session_id: str, request: Request):
    user = await get_current_user(request)
    await db.chat_sessions.delete_one(
        {"session_id": session_id, "user_id": user["user_id"]}
    )
    await db.messages.delete_many({"session_id": session_id})
    return {"message": "Session deleted"}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _retrieve_chapter_context(class_level: str, subject: str, chapter: str) -> str:
    chapters = get_verified_chapters(class_level, subject) or []
    match = next(
        (c for c in chapters if c.get("name") and chapter.lower() in c["name"].lower()),
        None,
    )
    if not match:
        return ""
    parts = [f"Chapter: {match['name']}"]
    if match.get("pdf_url"):
        parts.append(f"Official PDF: {match['pdf_url']}")
    return "\n".join(parts)


def _age_guidance(class_num: int) -> str:
    if class_num <= 7:
        return "Student is 10-12 yrs. Use playful, simple language. Make concepts feel exciting."
    if class_num <= 9:
        return "Student is 13-14 yrs. Balance fun with substance. Use relatable examples."
    return "Student is 15-18 yrs. Be precise, conceptually deep, board-exam focused."


def _build_system_prompt(session: dict, memory: dict, category: str, chapter_context: str, max_tokens: int) -> str:
    cls = session["class_level"]
    class_num = int(cls) if cls.isdigit() else 9
    subject = session["subject"]
    chapter = session["chapter"]
    difficulty = memory.get("difficulty", "medium")
    style     = memory.get("style", "balanced")
    weak      = ", ".join(memory.get("weak_topics", [])) or "none"
    strong    = ", ".join(memory.get("strong_topics", [])) or "none"
    recent_quiz = memory.get("recent_quiz_avg")

    if max_tokens <= 150:
        return (
            f"You are a CBSE tutor. Class {cls} | {subject} | {chapter}. "
            f"Answer in 2-3 sentences max. Be accurate and friendly. "
            f"Student difficulty: {difficulty}."
        )

    board_note = "🎯 BOARD EXAM FOCUS — mention exam patterns and marking schemes." if cls in ("10","12") else ""

    style_guide = {
        "step-by-step": "Break every concept into numbered steps. More guidance, check understanding.",
        "examples":     "Lead with 2-3 real-world examples before theory. Student needs concrete context.",
        "brief":        "Student grasps fast. Be concise, skip basics, focus on depth.",
        "visual":       "Use diagrams described in text, flowcharts, and analogies.",
        "balanced":     "Balance theory and examples.",
    }.get(style, "Balance theory and examples.")

    quiz_note = f"Recent quiz avg: {recent_quiz}% — " + (
        "student is struggling, use simpler explanations." if recent_quiz < 50 else
        "student is improving, push slightly harder." if recent_quiz < 75 else
        "student is excelling, challenge them."
    ) if recent_quiz is not None else ""

    return f"""You are AceIt AI Tutor — expert CBSE educator.

LESSON: Class {cls} | {subject} | {chapter}
STUDENT: {_age_guidance(class_num)} | difficulty={difficulty} | style={style}
MEMORY: weak=[{weak}] | strong=[{strong}]
{f"PERFORMANCE: {quiz_note}" if quiz_note else ""}
{board_note}
{f"CONTEXT:{chr(10)}{chapter_context}" if chapter_context else ""}

STYLE GUIDE: {style_guide}

MATH FORMAT (mandatory):
• Simple fractions: use Unicode symbols → ½ ¼ ¾ ⅓ ⅔ ⅕ ⅖ ⅗ ⅘ ⅙ ⅚ ⅛ ⅜ ⅝ ⅞
• Powers and subscripts: write x² y³ H₂O CO₂ (not x^2 or H_2O)
• Common symbols: π √ ∞ ≈ ≠ ≤ ≥ ± ∈ ∑ ∫ ∆ ∝ °C →
• For multi-step or complex equations: wrap in $...$ for inline, $$...$$ for block
• NEVER output raw LaTeX like \\frac{{}}{{}} — use ½ or (a/b) format for simple fractions
• Example: "The slope is ½" not "The slope is \\frac{{1}}{{2}}"

RULES:
• Build intuition before formulas. Short paragraphs (3 lines max).
• End every response with ONE of: ⚡ Challenge | 🎯 Quick Check | 📝 Exam Tip
• Always complete every sentence and explanation fully — never truncate mid-thought.
• Never truncate mathematical derivations or multi-step solutions."""


# ── Main message handler ──────────────────────────────────────────────────────

@router.post("/chat/sessions/{session_id}/message")
async def send_message(session_id: str, body: ChatMessageRequest, request: Request):
    user = await get_current_user(request)

    session = await db.chat_sessions.find_one(
        {"session_id": session_id, "user_id": user["user_id"]}, {"_id": 0}
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.get("class_level") != user.get("class_level"):
        raise HTTPException(
            status_code=403,
            detail="This chapter is outside your active grade. Change your grade in Profile.",
        )

    # Daily message limit check — REMOVED: no limit for AI tutor

    # Budget check — determines model + token ceiling
    plan_info = await get_user_plan(user["user_id"])
    plan_id   = plan_info["id"]
    budget    = await check_budget(user["user_id"], plan_id)

    # Hard block — token cap exhausted
    if budget["over_budget"]:
        now = datetime.now(timezone.utc).isoformat()
        await db.messages.insert_many([
            {"session_id": session_id, "role": "user",      "content": body.content,           "timestamp": now},
            {"session_id": session_id, "role": "assistant", "content": _BUDGET_EXHAUSTED_MSG,  "timestamp": now},
        ])
        await db.chat_sessions.update_one(
            {"session_id": session_id},
            {"$set": {"updated_at": now}, "$inc": {"message_count": 2}},
        )
        return StreamingResponse(
            iter([
                f"data: {json.dumps({'type':'chunk','content':_BUDGET_EXHAUSTED_MSG})}\n\n",
                f"data: {json.dumps({'type':'done'})}\n\n",
            ]),
            media_type="text/event-stream",
            headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"},
        )

    # Route request
    routing = build_routing_decision(
        body.content, plan_id,
        near_budget=budget["near_budget"],
        critical=budget["critical"],
        over_budget=False,
    )
    category   = routing["category"]
    ai_model   = routing["model"]
    max_tokens = routing["max_tokens"]

    # ── Category A: curriculum lookup, no LLM ────────────────────────────────
    if category == "A":
        chapters = get_verified_chapters(session["class_level"], session["subject"]) or []
        names = [c["name"] for c in chapters if c.get("name")]
        answer = (
            f"Here are the chapters for Class {session['class_level']} {session['subject']}:\n"
            + "\n".join(f"{i+1}. {n}" for i, n in enumerate(names))
        ) if names else "Chapter list is still being verified from NCERT."

        now = datetime.now(timezone.utc).isoformat()
        await db.messages.insert_many([
            {"session_id": session_id, "role": "user",      "content": body.content, "timestamp": now},
            {"session_id": session_id, "role": "assistant", "content": answer,        "timestamp": now},
        ])
        await db.chat_sessions.update_one(
            {"session_id": session_id},
            {"$set": {"updated_at": now}, "$inc": {"message_count": 2}},
        )
        return StreamingResponse(
            iter([
                f"data: {json.dumps({'type':'chunk','content':answer})}\n\n",
                f"data: {json.dumps({'type':'done'})}\n\n",
            ]),
            media_type="text/event-stream",
            headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"},
        )

    # ── KB lookup (runs before any LLM call) ─────────────────────────────────
    ch_no = None
    for c in (get_verified_chapters(session["class_level"], session["subject"]) or []):
        if c.get("name") and session["chapter"].lower() in c["name"].lower():
            ch_no = c.get("chapter_no")
            break

    kb_match = await find_kb_answer(
        body.content, session["class_level"], session["subject"], chapter_no=ch_no,
    )

    # Adaptive memory
    profile = await get_student_profile(user["user_id"])
    memory  = build_compact_memory(profile)

    # Persist user message
    now = datetime.now(timezone.utc).isoformat()
    await db.messages.insert_one(
        {"session_id": session_id, "role": "user", "content": body.content, "timestamp": now}
    )

    # Build AI messages
    if kb_match:
        # KB HIT — ultra-cheap rephrase: ~130 tokens total
        ai_messages = [
            {
                "role": "system",
                "content": (
                    f"You are a friendly CBSE tutor for Class {session['class_level']} "
                    f"{session['subject']}. Rephrase the answer below in 2-3 clear sentences. "
                    f"Keep it factually accurate. Add one encouraging line.\n\n"
                    f"ANSWER:\n{kb_match['answer']}"
                ),
            },
            {"role": "user", "content": body.content},
        ]
        ai_model   = "gpt-4o-mini"
        max_tokens = 180
    else:
        # KB MISS — full generation, token-capped by budget tier
        chapter_context = _retrieve_chapter_context(
            session["class_level"], session["subject"], session["chapter"]
        )
        system_prompt = _build_system_prompt(session, memory, category, chapter_context, max_tokens)
        history = await db.messages.find(
            {"session_id": session_id}, {"_id": 0}
        ).sort("timestamp", -1).limit(6).to_list(6)
        history.reverse()
        ai_messages = [{"role": "system", "content": system_prompt}]
        for msg in history[:-1]:
            ai_messages.append({"role": msg["role"], "content": msg["content"]})
        ai_messages.append({"role": "user", "content": body.content})

    # ── Stream response ───────────────────────────────────────────────────────
    async def generate():
        full_content = ""
        word_count = 0
        input_tokens_est = int(sum(len(m["content"].split()) * 1.3 for m in ai_messages))

        # Reserve generous headroom so the model can always finish its response
        generation_tokens = max_tokens  # no artificial cap — trust the router limits

        try:
            stream = await openai_client.chat.completions.create(
                model=ai_model,
                messages=ai_messages,
                stream=True,
                max_tokens=generation_tokens,
                temperature=0.75,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    full_content += delta
                    word_count = len(full_content.split())
                    yield f"data: {json.dumps({'type':'chunk','content':delta})}\n\n"
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            fallback = "Sorry, I encountered an issue. Please try again in a moment."
            yield f"data: {json.dumps({'type':'chunk','content':fallback})}\n\n"
            full_content = fallback

        ts = datetime.now(timezone.utc).isoformat()
        await db.messages.insert_one(
            {"session_id": session_id, "role": "assistant", "content": full_content, "timestamp": ts}
        )
        await db.chat_sessions.update_one(
            {"session_id": session_id},
            {"$set": {"updated_at": ts}, "$inc": {"message_count": 2}},
        )

        # XP
        await db.users.update_one(
            {"user_id": user["user_id"]},
            {"$inc": {"xp": 5}, "$set": {"last_active": ts}},
        )
        updated = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0})
        if updated:
            new_level = max(1, updated.get("xp", 0) // 500 + 1)
            if new_level > updated.get("level", 1):
                await db.users.update_one(
                    {"user_id": user["user_id"]}, {"$set": {"level": new_level}}
                )

        # Variable credit deduction based on word count
        final_word_count = len(full_content.split())
        credit_result = await deduct_credits_for_chat(user["user_id"], final_word_count)

        # Usage + token tracking
        await increment_usage(user["user_id"], "ai_messages", 1)
        output_tokens_est = int(len(full_content.split()) * 1.3)
        await record_token_usage(user["user_id"], ai_model, input_tokens_est, output_tokens_est)

        credits_used = calculate_chat_credits(final_word_count)
        yield f"data: {json.dumps({'type':'done','word_count':final_word_count,'credits_used':credits_used,'balance':credit_result.get('balance',0)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"},
    )


# ── Analytics ─────────────────────────────────────────────────────────────────

@router.get("/chat/analytics/me")
async def my_ai_analytics(request: Request):
    user = await get_current_user(request)
    uid  = user["user_id"]
    plan_info = await get_user_plan(uid)
    budget    = await check_budget(uid, plan_info["id"])
    profile   = await get_student_profile(uid)
    memory    = build_compact_memory(profile)

    month = _month_key()
    budget_doc  = await db.token_budgets.find_one({"user_id": uid}, {"_id": 0}) or {}
    month_data  = (budget_doc.get("months") or {}).get(month, {})

    from credits import get_credits
    credits_left = await get_credits(uid)

    return {
        "plan":   plan_info["id"],
        "month":  month,
        "credits_remaining": credits_left,
        "tokens_used":  budget["used"],
        "tokens_cap":   budget["cap"],
        "pct_used":     budget["pct_used"],
        "cost_inr":     round(month_data.get("cost_inr", 0.0), 2),
        "requests":     month_data.get("requests", 0),
        "budget_status": (
            "over"     if budget["over_budget"] else
            "critical" if budget["critical"]    else
            "near"     if budget["near_budget"] else
            "normal"
        ),
        "adaptive_profile": {
            "difficulty":     profile.get("difficulty", "medium"),
            "weak_topics":    memory["weak_topics"],
            "strong_topics":  memory["strong_topics"],
            "topics_tracked": len(profile.get("topics", {})),
        },
        "knowledge_base": await get_kb_stats(),
    }


def _month_key() -> str:
    n = datetime.now(timezone.utc)
    return f"{n.year}-{n.month:02d}"
