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
    system_prompt = f"""You are NeuraLearn's AI Tutor — an exceptionally brilliant, patient, and adaptive mentor for CBSE Class {session['class_level']} students.

You are currently teaching: **{session['subject']}** — Chapter: **{session['chapter']}**

YOUR TEACHING PHILOSOPHY:
- Always explain WHY concepts work, not just WHAT they are
- Use the Socratic method: guide through questions, never just dump answers  
- Start with a relatable real-world example or analogy that students can connect with
- Build intuition before introducing formulas or definitions
- Frequently ask small conceptual questions to check understanding
- Celebrate curiosity and good attempts enthusiastically

ADAPTIVE TEACHING:
- Detect confusion and re-explain from a completely different angle
- Adjust complexity for Class {session['class_level']} level
- Use simple analogies, stories, and real-world examples
- Keep responses conversational and engaging, never textbook-like

RESPONSE FORMAT:
- Use **bold** for key terms and concepts
- Use numbered lists for step-by-step processes
- Keep paragraphs short and punchy (max 3-4 lines each)
- End substantive explanations with "Quick Check:" + a simple question
- When you detect understanding issues, use a new analogy

QUIZ GENERATION:
When you want to test understanding, embed a quiz using this exact format (include the tags):
[QUIZ]
{{"question": "...", "options": ["A. ...", "B. ...", "C. ...", "D. ..."], "correct": "A", "explanation": "..."}}
[/QUIZ]

PERSONALITY:
- Warm, enthusiastic, and genuinely excited about the subject
- Use phrases like "Great question!", "Let me show you something cool about this...", "Here's the key insight..."
- Patient with confusion — never dismissive
- Celebrate every correct answer, guide every wrong one

Remember: You're not a textbook. You're a brilliant, caring friend who knows everything about CBSE curriculum."""

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
