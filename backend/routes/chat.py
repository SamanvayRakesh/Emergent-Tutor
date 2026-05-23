"""Chat sessions + streaming GPT-4o tutor."""
import uuid
import json
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from core import db, openai_client, logger, get_current_user
from models import ChatSessionCreate, ChatMessageRequest

router = APIRouter()


@router.post("/chat/sessions")
async def create_chat_session(body: ChatSessionCreate, request: Request):
    user = await get_current_user(request)
    session_id = f"chat_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    session_doc = {
        "session_id": session_id, "user_id": user["user_id"],
        "class_level": body.class_level, "subject": body.subject,
        "chapter": body.chapter, "chapter_id": body.chapter_id,
        "title": f"{body.subject} - {body.chapter}",
        "message_count": 0, "created_at": now, "updated_at": now,
    }
    await db.chat_sessions.insert_one(session_doc)
    session_doc.pop("_id", None)
    return session_doc


@router.get("/chat/sessions")
async def list_chat_sessions(request: Request):
    user = await get_current_user(request)
    return await db.chat_sessions.find(
        {"user_id": user["user_id"]}, {"_id": 0}
    ).sort("updated_at", -1).limit(20).to_list(20)


@router.get("/chat/sessions/{session_id}")
async def get_chat_session(session_id: str, request: Request):
    user = await get_current_user(request)
    session = await db.chat_sessions.find_one({"session_id": session_id, "user_id": user["user_id"]}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = await db.messages.find({"session_id": session_id}, {"_id": 0}).sort("timestamp", 1).to_list(200)
    return {"session": session, "messages": messages}


@router.delete("/chat/sessions/{session_id}")
async def delete_chat_session(session_id: str, request: Request):
    user = await get_current_user(request)
    await db.chat_sessions.delete_one({"session_id": session_id, "user_id": user["user_id"]})
    await db.messages.delete_many({"session_id": session_id})
    return {"message": "Session deleted"}


@router.post("/chat/sessions/{session_id}/message")
async def send_message(session_id: str, body: ChatMessageRequest, request: Request):
    user = await get_current_user(request)
    session = await db.chat_sessions.find_one({"session_id": session_id, "user_id": user["user_id"]}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    now = datetime.now(timezone.utc).isoformat()
    await db.messages.insert_one({
        "session_id": session_id, "role": "user", "content": body.content, "timestamp": now,
    })

    history = await db.messages.find({"session_id": session_id}, {"_id": 0}).sort("timestamp", -1).limit(12).to_list(12)
    history.reverse()

    class_num = int(session['class_level']) if session['class_level'].isdigit() else 9
    age_guidance = (
        "Student is 10-12 years old. Use playful energy, games, stories, and magic. Make concepts feel like exciting discoveries."
        if class_num <= 7 else
        "Student is 13-14 years old. Mix fun with substance. Use pop culture, sports, space, tech references. Build exam awareness naturally."
        if class_num <= 9 else
        "Student is 15-18 years old. Respect their intelligence. Deep conceptual insights, problem-solving strategies, board exam excellence. Be precise but engaging."
    )
    exam_focus = "🎯 BOARD EXAM FOCUS — This topic has high exam weightage! Mention exam patterns when relevant." if session['class_level'] in ['10', '12'] else "Build strong conceptual foundations."

    system_prompt = f"""You are NeuraLearn's Elite AI Tutor — a world-class educator who makes every student fall in love with learning.

CURRENT LESSON: Class {session['class_level']} | {session['subject']} | {session['chapter']}
STUDENT PROFILE: {age_guidance}
EXAM CONTEXT: {exam_focus}

═══════ YOUR TEACHING IDENTITY ═══════
You have the intellectual brilliance of Feynman, the storytelling of Neil deGrasse Tyson, the patience of a saint, and the energy of the best TED speaker you've ever seen. You're not a textbook — you're the coolest, smartest mentor a student could have.

═══════ CORE TEACHING RULES ═══════
• NEVER start two consecutive responses the same way — vary your openings constantly
• ALWAYS build intuition BEFORE introducing formulas or definitions
• Use the Socratic method — ask questions that make students DISCOVER answers
• Vary your style: storytelling → analogy → thought experiment → visual description → challenge
• Detect confusion instantly and pivot to a COMPLETELY different explanation angle

═══════ GLOBAL EXAMPLES (MANDATORY) ═══════
Draw examples from DIVERSE global contexts — NOT just Indian examples:
• Sports: NBA finals, Formula 1 physics, soccer aerodynamics, Olympic swimming
• Technology: SpaceX launches, iPhone engineering, Minecraft physics, video game mechanics
• Movies/Shows: Marvel science, Inception dreams, Interstellar black holes, Avatar biology
• Nature: Amazon rainforest, Arctic ice, ocean depths, volcanic eruptions, space
• History: Ancient Rome engineering, Wright Brothers, Marie Curie, Tesla vs Edison
• Daily Life: Coffee cooling, music speakers, bike riding, cooking chemistry
Rotate through these — never default to only local examples.

═══════ RESPONSE ENERGY ═══════
• Use phrases like: "Here's where it gets mind-blowing...", "Plot twist:", "The wild part is...", "Think about this:", "Here's a secret the textbook won't tell you:"
• Celebrate understanding: "YES! That's exactly it!", "You're thinking like a scientist now!"
• Handle confusion warmly: "Great attempt! Let me show you a trick...", "You're SO close!"

═══════ FORMAT RULES ═══════
• **Bold** key terms on first use
• Short punchy paragraphs (3 lines max)
• Numbered lists for processes
• Always keep energy HIGH

═══════ QUIZ FORMAT (embed when testing understanding) ═══════
[QUIZ]
{{"question": "...", "options": ["A. ...", "B. ...", "C. ...", "D. ..."], "correct": "A", "explanation": "Short, satisfying explanation why..."}}
[/QUIZ]

═══════ YOUTUBE VISUAL FORMAT (use when concept benefits from visuals) ═══════
[YOUTUBE]best search query for educational video on this exact concept[/YOUTUBE]
Use this for: complex diagrams, scientific phenomena, mathematical animations, historical events, anything 3D or visual.

═══════ MANDATORY NEXT STEP (end EVERY response with exactly one) ═══════
Choose the most natural continuation:
⚡ **Challenge:** [one slightly harder question to test application]
OR 🎯 **Quick Check:** [fast conceptual question]
OR 🚀 **Coming Up:** [what's the exciting next concept to explore]
OR 🎬 **Visual Boost:** [suggest specific thing to visualize or look up]
OR 📝 **Exam Tip:** [a real pattern that appears in CBSE exams on this topic]

Remember: Your goal is not just to teach — it's to create a moment where the student thinks "wait, that's actually AMAZING." Make every response unforgettable."""

    ai_messages = [{"role": "system", "content": system_prompt}]
    for msg in history[:-1]:
        ai_messages.append({"role": msg["role"], "content": msg["content"]})
    ai_messages.append({"role": "user", "content": body.content})

    async def generate():
        full_content = ""
        try:
            stream = await openai_client.chat.completions.create(
                model="gpt-4o", messages=ai_messages,
                stream=True, max_tokens=1500, temperature=0.85,
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    text = chunk.choices[0].delta.content
                    full_content += text
                    yield f"data: {json.dumps({'type': 'chunk', 'content': text})}\n\n"
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            return

        await db.messages.insert_one({
            "session_id": session_id, "role": "assistant",
            "content": full_content, "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        await db.chat_sessions.update_one(
            {"session_id": session_id},
            {"$set": {"updated_at": datetime.now(timezone.utc).isoformat()}, "$inc": {"message_count": 2}},
        )
        await db.users.update_one(
            {"user_id": user["user_id"]},
            {"$inc": {"xp": 5}, "$set": {"last_active": datetime.now(timezone.utc).isoformat()}},
        )
        updated_user = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0})
        if updated_user:
            new_level = max(1, updated_user["xp"] // 500 + 1)
            if new_level > updated_user.get("level", 1):
                await db.users.update_one({"user_id": user["user_id"]}, {"$set": {"level": new_level}})

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        generate(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
