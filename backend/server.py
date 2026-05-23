"""NeuraLearn Backend - AI-Powered CBSE Learning Platform"""

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from openai import AsyncOpenAI
import bcrypt
import jwt
import httpx
import uuid
import json
import os
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Any
import secrets

from cbse_data import CBSE_SYLLABUS, get_classes, get_subjects, get_chapters, get_subject_meta

# --- Config ---
MONGO_URL = os.environ['MONGO_URL']
DB_NAME = os.environ['DB_NAME']
JWT_SECRET = os.environ.get('JWT_SECRET', 'neuralearn-secret-key-change-in-prod')
JWT_ALGORITHM = "HS256"
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')

# --- Clients ---
mongo_client = AsyncIOMotorClient(MONGO_URL)
db = mongo_client[DB_NAME]
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# --- FastAPI App ---
app = FastAPI(title="NeuraLearn API", version="1.0.0")
api_router = APIRouter(prefix="/api")

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ==================== MODELS ====================

class UserRegister(BaseModel):
    email: str
    password: str
    name: str

class UserLogin(BaseModel):
    email: str
    password: str

class GoogleSessionRequest(BaseModel):
    session_id: str

class ChatSessionCreate(BaseModel):
    class_level: str
    subject: str
    chapter: str
    chapter_id: str

class ChatMessageRequest(BaseModel):
    content: str

class QuizGenerateRequest(BaseModel):
    class_level: str
    subject: str
    topic: str
    difficulty: str = "medium"
    num_questions: int = 5

class QuizSubmitRequest(BaseModel):
    quiz_id: str
    answers: dict

class ProgressUpdate(BaseModel):
    class_level: str
    subject: str
    chapter_id: str
    chapter_name: str
    mastery_delta: int = 10

class XPUpdateRequest(BaseModel):
    amount: int
    reason: str = ""


# ==================== AUTH UTILITIES ====================

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=60),
        "type": "access"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "type": "refresh"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(request: Request) -> dict:
    # Try JWT access token
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if token:
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            if payload.get("type") == "access":
                user = await db.users.find_one({"user_id": payload["sub"]}, {"_id": 0})
                if user:
                    user.pop("password_hash", None)
                    return user
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            pass

    # Try Google session token
    session_token = request.cookies.get("session_token")
    if session_token:
        session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
        if session:
            expires_at = session.get("expires_at")
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)
            if expires_at and expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at and expires_at > datetime.now(timezone.utc):
                user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
                if user:
                    user.pop("password_hash", None)
                    return user

    raise HTTPException(status_code=401, detail="Not authenticated")


# ==================== AUTH ENDPOINTS ====================

@api_router.post("/auth/register")
async def register(body: UserRegister, response: __import__('fastapi').Response):
    email = body.email.lower().strip()
    existing = await db.users.find_one({"email": email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = f"user_{uuid.uuid4().hex[:12]}"
    hashed = hash_password(body.password)
    now = datetime.now(timezone.utc).isoformat()

    user_doc = {
        "user_id": user_id,
        "email": email,
        "name": body.name,
        "password_hash": hashed,
        "role": "student",
        "avatar": None,
        "xp": 0,
        "level": 1,
        "streak": 0,
        "longest_streak": 0,
        "last_active": now,
        "class_level": "9",
        "achievements": [],
        "created_at": now,
        "auth_type": "jwt"
    }
    await db.users.insert_one(user_doc)

    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id)

    response.set_cookie("access_token", access_token, httponly=True, secure=False, samesite="lax", max_age=3600, path="/")
    response.set_cookie("refresh_token", refresh_token, httponly=True, secure=False, samesite="lax", max_age=604800, path="/")

    user_doc.pop("password_hash", None)
    user_doc.pop("_id", None)
    return user_doc

@api_router.post("/auth/login")
async def login(body: UserLogin, response: __import__('fastapi').Response):
    email = body.email.lower().strip()
    user = await db.users.find_one({"email": email}, {"_id": 0})

    if not user or not user.get("password_hash") or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Update last active and streak
    now = datetime.now(timezone.utc)
    last_active_str = user.get("last_active", "")
    streak = user.get("streak", 0)
    if last_active_str:
        try:
            last_active = datetime.fromisoformat(last_active_str)
            if last_active.tzinfo is None:
                last_active = last_active.replace(tzinfo=timezone.utc)
            diff_days = (now.date() - last_active.date()).days
            if diff_days == 1:
                streak += 1
            elif diff_days > 1:
                streak = 1
        except Exception:
            streak = 1

    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {"last_active": now.isoformat(), "streak": streak, "longest_streak": max(streak, user.get("longest_streak", 0))}}
    )

    access_token = create_access_token(user["user_id"], email)
    refresh_token = create_refresh_token(user["user_id"])

    response.set_cookie("access_token", access_token, httponly=True, secure=False, samesite="lax", max_age=3600, path="/")
    response.set_cookie("refresh_token", refresh_token, httponly=True, secure=False, samesite="lax", max_age=604800, path="/")

    user.pop("password_hash", None)
    user["streak"] = streak
    return user

@api_router.post("/auth/logout")
async def logout(response: __import__('fastapi').Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    response.delete_cookie("session_token")
    return {"message": "Logged out successfully"}

@api_router.get("/auth/me")
async def get_me(request: Request):
    user = await get_current_user(request)
    return user

@api_router.post("/auth/refresh")
async def refresh_token(request: Request, response: __import__('fastapi').Response):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="No refresh token")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user_id = payload["sub"]
        user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        new_access = create_access_token(user_id, user["email"])
        response.set_cookie("access_token", new_access, httponly=True, secure=False, samesite="lax", max_age=3600, path="/")
        return {"message": "Token refreshed"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")


# ==================== GOOGLE AUTH ====================

@api_router.post("/google-auth/session")
async def google_session(body: GoogleSessionRequest, response: __import__('fastapi').Response):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": body.session_id}
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Invalid session")
        data = resp.json()

    email = data.get("email", "").lower().strip()
    existing = await db.users.find_one({"email": email}, {"_id": 0})

    if existing:
        user_id = existing["user_id"]
        # Update info
        now = datetime.now(timezone.utc)
        streak = existing.get("streak", 0)
        last_active_str = existing.get("last_active", "")
        if last_active_str:
            try:
                last_active = datetime.fromisoformat(last_active_str)
                if last_active.tzinfo is None:
                    last_active = last_active.replace(tzinfo=timezone.utc)
                diff_days = (now.date() - last_active.date()).days
                if diff_days == 1:
                    streak += 1
                elif diff_days > 1:
                    streak = 1
            except Exception:
                pass
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"name": data.get("name", existing["name"]), "avatar": data.get("picture"), "last_active": now.isoformat(), "streak": streak}}
        )
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        user_doc = {
            "user_id": user_id,
            "email": email,
            "name": data.get("name", email),
            "avatar": data.get("picture"),
            "role": "student",
            "xp": 0,
            "level": 1,
            "streak": 1,
            "longest_streak": 1,
            "last_active": now,
            "class_level": "9",
            "achievements": [],
            "created_at": now,
            "auth_type": "google"
        }
        await db.users.insert_one(user_doc)

    # Create session
    session_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })

    # REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS
    response.set_cookie("session_token", session_token, httponly=True, secure=True, samesite="none", max_age=604800, path="/")

    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    user.pop("password_hash", None)
    return user

@api_router.post("/google-auth/logout")
async def google_logout(request: Request, response: __import__('fastapi').Response):
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    response.delete_cookie("session_token")
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out"}


# ==================== USER PROFILE ====================

@api_router.put("/users/class")
async def update_class(request: Request, body: dict):
    user = await get_current_user(request)
    class_level = body.get("class_level")
    if class_level not in get_classes():
        raise HTTPException(status_code=400, detail="Invalid class level")
    await db.users.update_one({"user_id": user["user_id"]}, {"$set": {"class_level": class_level}})
    return {"message": "Class updated", "class_level": class_level}


# ==================== CHAT SESSIONS ====================

@api_router.post("/chat/sessions")
async def create_chat_session(body: ChatSessionCreate, request: Request):
    user = await get_current_user(request)
    session_id = f"chat_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()

    session_doc = {
        "session_id": session_id,
        "user_id": user["user_id"],
        "class_level": body.class_level,
        "subject": body.subject,
        "chapter": body.chapter,
        "chapter_id": body.chapter_id,
        "title": f"{body.subject} - {body.chapter}",
        "message_count": 0,
        "created_at": now,
        "updated_at": now
    }
    await db.chat_sessions.insert_one(session_doc)
    session_doc.pop("_id", None)
    return session_doc

@api_router.get("/chat/sessions")
async def list_chat_sessions(request: Request):
    user = await get_current_user(request)
    sessions = await db.chat_sessions.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("updated_at", -1).limit(20).to_list(20)
    return sessions

@api_router.get("/chat/sessions/{session_id}")
async def get_chat_session(session_id: str, request: Request):
    user = await get_current_user(request)
    session = await db.chat_sessions.find_one({"session_id": session_id, "user_id": user["user_id"]}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = await db.messages.find({"session_id": session_id}, {"_id": 0}).sort("timestamp", 1).to_list(200)
    return {"session": session, "messages": messages}

@api_router.delete("/chat/sessions/{session_id}")
async def delete_chat_session(session_id: str, request: Request):
    user = await get_current_user(request)
    await db.chat_sessions.delete_one({"session_id": session_id, "user_id": user["user_id"]})
    await db.messages.delete_many({"session_id": session_id})
    return {"message": "Session deleted"}

@api_router.post("/chat/sessions/{session_id}/message")
async def send_message(session_id: str, body: ChatMessageRequest, request: Request):
    user = await get_current_user(request)
    session = await db.chat_sessions.find_one({"session_id": session_id, "user_id": user["user_id"]}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Save user message
    now = datetime.now(timezone.utc).isoformat()
    user_msg = {
        "session_id": session_id,
        "role": "user",
        "content": body.content,
        "timestamp": now
    }
    await db.messages.insert_one(user_msg)

    # Get conversation history (last 12 messages)
    history = await db.messages.find({"session_id": session_id}, {"_id": 0}).sort("timestamp", -1).limit(12).to_list(12)
    history.reverse()

    # Build AI messages
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
    for msg in history[:-1]:  # exclude the user message we just saved
        ai_messages.append({"role": msg["role"], "content": msg["content"]})
    ai_messages.append({"role": "user", "content": body.content})

    async def generate():
        full_content = ""
        try:
            stream = await openai_client.chat.completions.create(
                model="gpt-4o",
                messages=ai_messages,
                stream=True,
                max_tokens=1500,
                temperature=0.85
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

        # Save AI message
        ai_msg = {
            "session_id": session_id,
            "role": "assistant",
            "content": full_content,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await db.messages.insert_one(ai_msg)

        # Update session
        await db.chat_sessions.update_one(
            {"session_id": session_id},
            {"$set": {"updated_at": datetime.now(timezone.utc).isoformat()}, "$inc": {"message_count": 2}}
        )

        # Award XP
        await db.users.update_one(
            {"user_id": user["user_id"]},
            {"$inc": {"xp": 5}, "$set": {"last_active": datetime.now(timezone.utc).isoformat()}}
        )

        # Check level up
        updated_user = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0})
        if updated_user:
            new_level = max(1, updated_user["xp"] // 500 + 1)
            if new_level > updated_user.get("level", 1):
                await db.users.update_one({"user_id": user["user_id"]}, {"$set": {"level": new_level}})

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


# ==================== SYLLABUS ====================

@api_router.get("/syllabus/classes")
async def get_all_classes():
    classes = get_classes()
    return [{"id": c, "name": f"Class {c}"} for c in classes]

@api_router.get("/syllabus/{class_id}/subjects")
async def get_class_subjects(class_id: str):
    subjects = get_subjects(class_id)
    if not subjects:
        raise HTTPException(status_code=404, detail="Class not found")
    result = []
    for s in subjects:
        meta = get_subject_meta(class_id, s)
        chapters = get_chapters(class_id, s)
        result.append({
            "name": s,
            "icon": meta["icon"],
            "color": meta["color"],
            "chapter_count": len(chapters)
        })
    return result

@api_router.get("/syllabus/{class_id}/{subject}/chapters")
async def get_subject_chapters(class_id: str, subject: str):
    from urllib.parse import unquote
    subject = unquote(subject)
    chapters = get_chapters(class_id, subject)
    if chapters is None:
        raise HTTPException(status_code=404, detail="Subject not found")
    return chapters


# ==================== PROGRESS ====================

@api_router.get("/progress")
async def get_progress(request: Request):
    user = await get_current_user(request)
    progress_records = await db.progress.find({"user_id": user["user_id"]}, {"_id": 0}).to_list(200)

    # Aggregate by subject
    subject_progress = {}
    for rec in progress_records:
        subj = rec.get("subject", "")
        if subj not in subject_progress:
            subject_progress[subj] = {"chapters": 0, "total_mastery": 0, "weak_topics": []}
        subject_progress[subj]["chapters"] += 1
        subject_progress[subj]["total_mastery"] += rec.get("mastery", 0)
        if rec.get("mastery", 0) < 40:
            subject_progress[subj]["weak_topics"].append(rec.get("chapter_name", ""))

    for subj in subject_progress:
        subject_progress[subj]["avg_mastery"] = (
            subject_progress[subj]["total_mastery"] // subject_progress[subj]["chapters"]
            if subject_progress[subj]["chapters"] > 0 else 0
        )

    total_mastery = sum(r.get("mastery", 0) for r in progress_records)
    avg_overall = total_mastery // len(progress_records) if progress_records else 0

    return {
        "overall_mastery": avg_overall,
        "total_chapters_studied": len(progress_records),
        "subject_progress": subject_progress,
        "recent_progress": progress_records[-10:] if progress_records else []
    }

@api_router.post("/progress/update")
async def update_progress(body: ProgressUpdate, request: Request):
    user = await get_current_user(request)
    existing = await db.progress.find_one(
        {"user_id": user["user_id"], "chapter_id": body.chapter_id},
        {"_id": 0}
    )

    now = datetime.now(timezone.utc).isoformat()
    if existing:
        new_mastery = min(100, existing.get("mastery", 0) + body.mastery_delta)
        await db.progress.update_one(
            {"user_id": user["user_id"], "chapter_id": body.chapter_id},
            {"$set": {"mastery": new_mastery, "updated_at": now}}
        )
    else:
        await db.progress.insert_one({
            "user_id": user["user_id"],
            "class_level": body.class_level,
            "subject": body.subject,
            "chapter_id": body.chapter_id,
            "chapter_name": body.chapter_name,
            "mastery": min(100, body.mastery_delta),
            "created_at": now,
            "updated_at": now
        })
    return {"message": "Progress updated"}


# ==================== QUIZ ====================

@api_router.post("/quiz/generate")
async def generate_quiz(body: QuizGenerateRequest, request: Request):
    user = await get_current_user(request)

    prompt = f"""Generate exactly {body.num_questions} multiple-choice questions for CBSE Class {body.class_level} {body.subject} on the topic: "{body.topic}".

Difficulty level: {body.difficulty}

Return ONLY a JSON object with this structure:
{{
  "title": "Quiz: {body.topic}",
  "subject": "{body.subject}",
  "class_level": "{body.class_level}",
  "questions": [
    {{
      "question": "...",
      "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
      "correct": "A",
      "explanation": "Brief explanation why the answer is correct"
    }}
  ]
}}

Make questions test conceptual understanding, not just memorization. Include a brief explanation for each answer."""

    response = await openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an expert CBSE question paper setter. Generate clear, educational MCQ questions."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.7,
        max_tokens=2000
    )

    quiz_data = json.loads(response.choices[0].message.content)
    quiz_id = f"quiz_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()

    quiz_doc = {
        "quiz_id": quiz_id,
        "user_id": user["user_id"],
        "class_level": body.class_level,
        "subject": body.subject,
        "topic": body.topic,
        "difficulty": body.difficulty,
        "questions": quiz_data.get("questions", []),
        "title": quiz_data.get("title", f"Quiz: {body.topic}"),
        "completed": False,
        "score": None,
        "created_at": now
    }
    await db.quizzes.insert_one(quiz_doc)
    quiz_doc.pop("_id", None)
    return quiz_doc

@api_router.get("/quiz/history")
async def get_quiz_history(request: Request):
    user = await get_current_user(request)
    quizzes = await db.quizzes.find({"user_id": user["user_id"]}, {"_id": 0}).sort("created_at", -1).limit(20).to_list(20)
    return quizzes

@api_router.post("/quiz/{quiz_id}/submit")
async def submit_quiz(quiz_id: str, body: QuizSubmitRequest, request: Request):
    user = await get_current_user(request)
    quiz = await db.quizzes.find_one({"quiz_id": quiz_id, "user_id": user["user_id"]}, {"_id": 0})
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    questions = quiz.get("questions", [])
    correct_count = 0
    results = []

    for i, q in enumerate(questions):
        user_answer = body.answers.get(str(i))
        is_correct = user_answer == q.get("correct")
        if is_correct:
            correct_count += 1
        results.append({
            "question": q["question"],
            "user_answer": user_answer,
            "correct_answer": q.get("correct"),
            "is_correct": is_correct,
            "explanation": q.get("explanation", "")
        })

    total = len(questions)
    score_pct = int((correct_count / total * 100)) if total > 0 else 0
    xp_earned = correct_count * 20

    await db.quizzes.update_one(
        {"quiz_id": quiz_id},
        {"$set": {"completed": True, "score": score_pct, "correct_count": correct_count, "total_questions": total, "completed_at": datetime.now(timezone.utc).isoformat()}}
    )

    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$inc": {"xp": xp_earned}}
    )

    return {
        "score": score_pct,
        "correct_count": correct_count,
        "total_questions": total,
        "xp_earned": xp_earned,
        "results": results
    }


# ==================== GAMIFICATION ====================

@api_router.get("/gamification/stats")
async def get_gamification_stats(request: Request):
    user = await get_current_user(request)
    
    xp = user.get("xp", 0)
    level = max(1, xp // 500 + 1)
    xp_in_level = xp % 500
    xp_to_next = 500 - xp_in_level

    # Count sessions and quizzes
    session_count = await db.chat_sessions.count_documents({"user_id": user["user_id"]})
    quiz_count = await db.quizzes.count_documents({"user_id": user["user_id"], "completed": True})
    chapters_studied = await db.progress.count_documents({"user_id": user["user_id"]})

    # Achievements
    achievements = []
    if session_count >= 1:
        achievements.append({"id": "first_chat", "name": "First Steps", "description": "Started your first AI chat", "icon": "star", "color": "#22d3ee"})
    if session_count >= 10:
        achievements.append({"id": "chat_10", "name": "Curious Mind", "description": "Completed 10 AI chat sessions", "icon": "brain", "color": "#8b5cf6"})
    if quiz_count >= 1:
        achievements.append({"id": "first_quiz", "name": "Quiz Starter", "description": "Completed your first quiz", "icon": "target", "color": "#10b981"})
    if quiz_count >= 5:
        achievements.append({"id": "quiz_5", "name": "Quiz Master", "description": "Completed 5 quizzes", "icon": "trophy", "color": "#f59e0b"})
    if xp >= 100:
        achievements.append({"id": "xp_100", "name": "Rising Star", "description": "Earned 100 XP", "icon": "zap", "color": "#d946ef"})
    if user.get("streak", 0) >= 3:
        achievements.append({"id": "streak_3", "name": "On Fire!", "description": "3-day learning streak", "icon": "flame", "color": "#ef4444"})

    # Daily challenge
    daily_topics = ["Photosynthesis", "Newton's Laws", "Quadratic Equations", "Periodic Table", "French Revolution", "Python Lists"]
    import random
    random.seed(datetime.now().date().toordinal())
    daily_topic = random.choice(daily_topics)

    return {
        "xp": xp,
        "level": level,
        "xp_in_level": xp_in_level,
        "xp_to_next": xp_to_next,
        "streak": user.get("streak", 0),
        "longest_streak": user.get("longest_streak", 0),
        "achievements": achievements,
        "session_count": session_count,
        "quiz_count": quiz_count,
        "chapters_studied": chapters_studied,
        "daily_challenge": {
            "topic": daily_topic,
            "subject": "Mixed",
            "xp_reward": 50
        }
    }


# ==================== LEADERBOARD ====================

@api_router.get("/leaderboard")
async def get_leaderboard(request: Request):
    users = await db.users.find({}, {"_id": 0, "user_id": 1, "name": 1, "xp": 1, "streak": 1, "class_level": 1}).sort("xp", -1).limit(50).to_list(50)
    leaderboard = []
    for i, u in enumerate(users):
        xp = u.get("xp", 0)
        leaderboard.append({
            "rank": i + 1,
            "user_id": u["user_id"],
            "name": u.get("name", "Anonymous"),
            "xp": xp,
            "level": max(1, xp // 500 + 1),
            "streak": u.get("streak", 0),
            "class_level": u.get("class_level", "?"),
            "badge": "gold" if i == 0 else "silver" if i == 1 else "bronze" if i == 2 else None
        })
    user_rank = None
    current_user_entry = None
    try:
        user = await get_current_user(request)
        for entry in leaderboard:
            if entry["user_id"] == user["user_id"]:
                user_rank = entry["rank"]
                current_user_entry = entry
                break
    except Exception:
        pass
    return {"leaderboard": leaderboard[:20], "user_rank": user_rank, "current_user": current_user_entry, "total_users": len(users)}


# ==================== MOCK EXAM ====================

class MockExamRequest(BaseModel):
    class_level: str
    subject: str
    duration_minutes: int = 60
    num_questions: int = 20

@api_router.post("/mock-exam/generate")
async def generate_mock_exam(body: MockExamRequest, request: Request):
    user = await get_current_user(request)
    is_board = body.class_level in ["10", "12"]
    sec_a = max(4, body.num_questions // 2)
    sec_b = max(3, body.num_questions // 4)
    sec_c = body.num_questions - sec_a - sec_b

    prompt = f"""Generate a CBSE Class {body.class_level} {body.subject} mock exam paper with {body.num_questions} questions total.
Structure: Section A ({sec_a} MCQs, 1 mark each), Section B ({sec_b} questions, 2 marks each), Section C ({sec_c} questions, 3 marks each).
{"Focus on board exam patterns with HOTS questions." if is_board else "Cover fundamental concepts suitable for internal assessments."}

Return ONLY valid JSON:
{{
  "title": "Class {body.class_level} {body.subject} Mock Examination",
  "duration_minutes": {body.duration_minutes},
  "sections": [
    {{
      "section": "A", "title": "Multiple Choice Questions", "marks_per_question": 1,
      "questions": [{{"id":"A1","question":"...","options":["A. ...","B. ...","C. ...","D. ..."],"correct":"A","marks":1,"difficulty":"easy","topic":"...","explanation":"..."}}]
    }},
    {{
      "section": "B", "title": "Short Answer (MCQ Format)", "marks_per_question": 2,
      "questions": [{{"id":"B1","question":"...","options":["A. ...","B. ...","C. ...","D. ..."],"correct":"A","marks":2,"difficulty":"medium","topic":"...","explanation":"..."}}]
    }},
    {{
      "section": "C", "title": "Application Based Questions", "marks_per_question": 3,
      "questions": [{{"id":"C1","question":"...","options":["A. ...","B. ...","C. ...","D. ..."],"correct":"A","marks":3,"difficulty":"hard","topic":"...","explanation":"..."}}]
    }}
  ]
}}
Generate EXACTLY {sec_a} questions in Section A, {sec_b} in Section B, {sec_c} in Section C. Cover different chapters."""

    response = await openai_client.chat.completions.create(
        model="gpt-4o", messages=[{"role": "system", "content": "Expert CBSE question paper setter."}, {"role": "user", "content": prompt}],
        response_format={"type": "json_object"}, temperature=0.7, max_tokens=4000
    )
    exam_data = json.loads(response.choices[0].message.content)
    exam_id = f"exam_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    exam_doc = {
        "exam_id": exam_id, "user_id": user["user_id"], "class_level": body.class_level,
        "subject": body.subject, "duration_minutes": body.duration_minutes,
        "title": exam_data.get("title", f"Class {body.class_level} {body.subject} Mock Exam"),
        "sections": exam_data.get("sections", []), "completed": False, "score": None, "created_at": now
    }
    await db.mock_exams.insert_one(exam_doc)
    exam_doc.pop("_id", None)
    return exam_doc

@api_router.get("/mock-exam/history")
async def get_mock_exam_history(request: Request):
    user = await get_current_user(request)
    exams = await db.mock_exams.find({"user_id": user["user_id"]}, {"_id": 0, "sections": 0}).sort("created_at", -1).limit(10).to_list(10)
    return exams

@api_router.post("/mock-exam/{exam_id}/submit")
async def submit_mock_exam(exam_id: str, body: QuizSubmitRequest, request: Request):
    user = await get_current_user(request)
    exam = await db.mock_exams.find_one({"exam_id": exam_id, "user_id": user["user_id"]}, {"_id": 0})
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    total_marks = earned_marks = 0
    section_results = []
    weak_topics = []
    for section in exam.get("sections", []):
        s_earned = s_total = 0
        s_correct = s_questions = 0
        for q in section.get("questions", []):
            marks = q.get("marks", 1)
            s_total += marks; total_marks += marks; s_questions += 1
            if body.answers.get(q["id"]) == q.get("correct"):
                s_earned += marks; earned_marks += marks; s_correct += 1
            else:
                if q.get("topic"): weak_topics.append(q["topic"])
        section_results.append({"section": section["section"], "title": section.get("title", ""), "correct": s_correct, "total": s_questions, "marks_earned": s_earned, "marks_total": s_total, "percentage": int(s_earned / s_total * 100) if s_total > 0 else 0})
    score_pct = int(earned_marks / total_marks * 100) if total_marks > 0 else 0
    xp_earned = int(score_pct * 1.5)
    await db.mock_exams.update_one({"exam_id": exam_id}, {"$set": {"completed": True, "score": score_pct, "earned_marks": earned_marks, "total_marks": total_marks, "section_results": section_results, "weak_topics": list(set(weak_topics))[:5], "completed_at": datetime.now(timezone.utc).isoformat()}})
    await db.users.update_one({"user_id": user["user_id"]}, {"$inc": {"xp": xp_earned}})
    return {"score": score_pct, "earned_marks": earned_marks, "total_marks": total_marks, "xp_earned": xp_earned, "section_results": section_results, "weak_topics": list(set(weak_topics))[:5]}


# ==================== STUDY PLAN ====================

class StudyPlanRequest(BaseModel):
    exam_date: str
    target_score: int = 90
    daily_hours: float = 2.0
    class_level: str
    subjects: List[str] = []

@api_router.post("/study-plan")
async def create_study_plan(body: StudyPlanRequest, request: Request):
    user = await get_current_user(request)
    try:
        exam_dt = datetime.fromisoformat(body.exam_date.replace("Z", "+00:00"))
        days_until = max(1, (exam_dt.replace(tzinfo=None) - datetime.now()).days)
    except Exception:
        days_until = 30
    weeks = max(1, days_until // 7)
    subjects_str = ', '.join(body.subjects) if body.subjects else 'All subjects'
    prompt = f"""Create a CBSE exam study plan. Class {body.class_level}, {days_until} days left, target {body.target_score}%, {body.daily_hours}h/day, subjects: {subjects_str}.
Return JSON only:
{{"overview":"2-line strategy","weeks":[{{"week":1,"theme":"Foundation","focus":["topic1"],"daily_tasks":[{{"day":"Mon","subject":"...","topic":"...","hours":2,"type":"learn"}}],"goal":"..."}}],"exam_week":"strategy","tips":["tip1","tip2","tip3"]}}
Max {weeks} weeks. Prioritize high-weightage topics. Be specific and actionable."""
    response = await openai_client.chat.completions.create(
        model="gpt-4o", messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}, temperature=0.7, max_tokens=2500
    )
    plan_data = json.loads(response.choices[0].message.content)
    now = datetime.now(timezone.utc).isoformat()
    await db.study_plans.update_one({"user_id": user["user_id"]}, {"$set": {"user_id": user["user_id"], "exam_date": body.exam_date, "target_score": body.target_score, "daily_hours": body.daily_hours, "class_level": body.class_level, "subjects": body.subjects, "plan": plan_data, "updated_at": now}}, upsert=True)
    await db.users.update_one({"user_id": user["user_id"]}, {"$set": {"exam_date": body.exam_date, "target_score": body.target_score}})
    return {"plan": plan_data, "days_until_exam": days_until, "exam_date": body.exam_date}

@api_router.get("/study-plan")
async def get_study_plan(request: Request):
    user = await get_current_user(request)
    plan = await db.study_plans.find_one({"user_id": user["user_id"]}, {"_id": 0})
    if not plan:
        return {"plan": None}
    if plan.get("exam_date"):
        try:
            exam_dt = datetime.fromisoformat(plan["exam_date"].replace("Z", "+00:00"))
            plan["days_remaining"] = max(0, (exam_dt.replace(tzinfo=None) - datetime.now()).days)
        except Exception:
            pass
    return plan


# ==================== RECOMMENDATIONS ====================

@api_router.get("/recommendations")
async def get_recommendations(request: Request):
    user = await get_current_user(request)
    progress = await db.progress.find({"user_id": user["user_id"]}, {"_id": 0}).to_list(50)
    recent_sessions = await db.chat_sessions.find({"user_id": user["user_id"]}, {"_id": 0}).sort("updated_at", -1).limit(3).to_list(3)
    quiz_results = await db.quizzes.find({"user_id": user["user_id"], "completed": True}, {"_id": 0}).sort("created_at", -1).limit(3).to_list(3)
    recs = []
    if recent_sessions:
        s = recent_sessions[0]
        recs.append({"type": "resume", "icon": "play", "title": f"Continue: {s['chapter']}", "description": f"Pick up where you left off in {s['subject']}", "action": "chat", "data": {"session_id": s["session_id"]}})
    weak = [p for p in progress if p.get("mastery", 100) < 50]
    if weak:
        w = weak[0]
        recs.append({"type": "revision", "icon": "refresh", "title": f"Revise: {w['chapter_name']}", "description": f"Only {w.get('mastery',0)}% mastery — quick revision will boost your confidence!", "action": "chat", "data": {"subject": w.get("subject"), "chapter_id": w.get("chapter_id"), "chapter": w.get("chapter_name"), "class_level": w.get("class_level")}})
    low_quiz = [q for q in quiz_results if q.get("score", 100) < 70]
    if low_quiz:
        q = low_quiz[0]
        recs.append({"type": "practice", "icon": "target", "title": f"Practice: {q.get('topic','Quiz topic')}", "description": f"Scored {q.get('score',0)}% — let's improve it with focused practice!", "action": "quiz"})
    recs.append({"type": "mock_exam", "icon": "trophy", "title": "Take a Mock Exam", "description": "Challenge yourself with a CBSE-pattern timed examination", "action": "mock_exam"})
    recs.append({"type": "explore", "icon": "book", "title": "Explore New Chapter", "description": "Browse the full CBSE syllabus and start something new", "action": "syllabus"})
    return {"recommendations": recs[:4]}


# ==================== REFERRAL ====================

@api_router.get("/referral/code")
async def get_referral_code(request: Request):
    user = await get_current_user(request)
    code = user.get("referral_code")
    if not code:
        code = user["user_id"][-6:].upper()
        await db.users.update_one({"user_id": user["user_id"]}, {"$set": {"referral_code": code}})
    count = await db.referrals.count_documents({"referrer_id": user["user_id"]})
    return {"code": code, "referral_count": count, "xp_per_referral": 150, "referred_xp": 100}

@api_router.post("/referral/apply")
async def apply_referral(body: dict, request: Request):
    user = await get_current_user(request)
    code = body.get("code", "").upper().strip()
    if await db.referrals.find_one({"referred_id": user["user_id"]}):
        raise HTTPException(status_code=400, detail="You've already used a referral code")
    referrer = await db.users.find_one({"referral_code": code}, {"_id": 0})
    if not referrer:
        raise HTTPException(status_code=404, detail="Invalid referral code")
    if referrer["user_id"] == user["user_id"]:
        raise HTTPException(status_code=400, detail="Can't use your own code")
    await db.users.update_one({"user_id": user["user_id"]}, {"$inc": {"xp": 100}})
    await db.users.update_one({"user_id": referrer["user_id"]}, {"$inc": {"xp": 150}})
    await db.referrals.insert_one({"referrer_id": referrer["user_id"], "referred_id": user["user_id"], "applied_at": datetime.now(timezone.utc).isoformat()})
    return {"message": "Referral applied! You earned 100 XP!", "xp_earned": 100}


# ==================== MIDDLEWARE + APP SETUP ====================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.on_event("startup")
async def startup_event():
    # Indexes
    await db.users.create_index("email", unique=True)
    await db.users.create_index("user_id", unique=True)
    await db.user_sessions.create_index("session_token")
    await db.user_sessions.create_index("user_id")
    await db.chat_sessions.create_index("user_id")
    await db.messages.create_index("session_id")
    await db.progress.create_index([("user_id", 1), ("chapter_id", 1)])
    await db.quizzes.create_index("user_id")

    await db.mock_exams.create_index("user_id")
    await db.study_plans.create_index("user_id", unique=True)
    await db.referrals.create_index("referred_id")
    await db.referrals.create_index("referrer_id")
    # Seed admin
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@neuralearn.ai")
    admin_password = os.environ.get("ADMIN_PASSWORD", "Admin@123456")
    existing = await db.users.find_one({"email": admin_email}, {"_id": 0})
    if not existing:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        await db.users.insert_one({
            "user_id": user_id,
            "email": admin_email,
            "name": "NeuraLearn Admin",
            "password_hash": hash_password(admin_password),
            "role": "admin",
            "xp": 5000,
            "level": 11,
            "streak": 30,
            "longest_streak": 30,
            "last_active": now,
            "class_level": "12",
            "achievements": [],
            "created_at": now,
            "auth_type": "jwt"
        })
        logger.info(f"Admin seeded: {admin_email}")

    # Write test credentials
    creds_path = Path("/app/memory/test_credentials.md")
    creds_path.parent.mkdir(exist_ok=True)
    creds_path.write_text(f"""# NeuraLearn Test Credentials

## Admin Account
- Email: {admin_email}
- Password: {admin_password}
- Role: admin

## Student Test Account
- Email: student@neuralearn.ai
- Password: Student@123
- Note: Register this account via /api/auth/register

## Auth Endpoints
- POST /api/auth/register
- POST /api/auth/login
- POST /api/auth/logout
- GET /api/auth/me
- POST /api/google-auth/session

## App URL
- Frontend: {FRONTEND_URL}
- Backend API: {FRONTEND_URL}/api
""")

    logger.info("NeuraLearn backend started successfully!")


@app.on_event("shutdown")
async def shutdown_event():
    mongo_client.close()
