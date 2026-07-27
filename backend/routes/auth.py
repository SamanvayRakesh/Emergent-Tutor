"""Auth: JWT register/login + Google OAuth session.

Production features:
- Email quality validation (format, disposable domain, MX records)
- Cryptographically secure token hashing (SHA-256)
- In-memory rate limiting (per IP)
- Password: min 6 chars + at least one special character
- Welcome email on registration (no verification gate)
"""
import hashlib
import time
import uuid
import secrets
import re
from collections import defaultdict
from datetime import datetime, timezone, timedelta

import httpx
import jwt
from fastapi import APIRouter, HTTPException, Request, Response

from core import (
    db, logger, JWT_SECRET, JWT_ALGORITHM,
    hash_password, verify_password, create_access_token, create_refresh_token,
    get_current_user,
)
from models import UserRegister, UserLogin, GoogleSessionRequest, UpdateClassRequest
from cbse_data import get_classes
from email_service import send_welcome_email, validate_email_quality
from school_curriculum import SCHOOL_LIST, SCHOOLS

router = APIRouter()

# ── Admin email list ───────────────────────────────────────────────────────────
ADMIN_EMAILS = {
    "taniknpoojari@gmail.com",
    "truecursemahito28@gmail.com",
    "samanvayrakesh7@gmail.com",
}

@router.get("/auth/schools")
async def list_schools():
    """Public endpoint — returns all schools for the signup dropdown."""
    return {"schools": SCHOOL_LIST}

# ── Password validation ────────────────────────────────────────────────────────
SPECIAL_CHARS = r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?`~]"

def validate_password(password: str) -> tuple[bool, str]:
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
    if not re.search(SPECIAL_CHARS, password):
        return False, "Password must contain at least one special character (e.g. @, #, !, $)."
    return True, ""

# ── In-memory rate limiter ─────────────────────────────────────────────────────

_rate_store: dict = defaultdict(list)


def _check_rate_limit(key: str, max_calls: int, window_seconds: int) -> bool:
    now = time.monotonic()
    cutoff = now - window_seconds
    _rate_store[key] = [t for t in _rate_store[key] if t > cutoff]
    if len(_rate_store[key]) >= max_calls:
        return False
    _rate_store[key].append(now)
    return True


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# ── Token helpers ─────────────────────────────────────────────────────────────

def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# ── Cookie / user helpers ─────────────────────────────────────────────────────

def _set_auth_cookies(response: Response, user_id: str, email: str):
    response.set_cookie("access_token",  create_access_token(user_id, email),
                        httponly=True, secure=False, samesite="lax", max_age=3600,   path="/")
    response.set_cookie("refresh_token", create_refresh_token(user_id),
                        httponly=True, secure=False, samesite="lax", max_age=604800, path="/")


def _strip_sensitive(user: dict) -> dict:
    for key in ("password_hash", "_id", "verification_token",
                "verification_token_hash", "resend_cooldown_until"):
        user.pop(key, None)
    return user


# ── Register ──────────────────────────────────────────────────────────────────

@router.post("/auth/register")
async def register(body: UserRegister, request: Request, response: Response):
    client_ip = _get_client_ip(request)
    email = body.email.lower().strip()

    # Email quality validation
    is_valid, reason = await validate_email_quality(email)
    if not is_valid:
        raise HTTPException(status_code=422, detail=reason)

    # Password strength check
    pw_ok, pw_reason = validate_password(body.password)
    if not pw_ok:
        raise HTTPException(status_code=422, detail=pw_reason)

    # Rate limit: 5 valid registration attempts per hour per IP
    if not _check_rate_limit(f"register:{client_ip}", 5, 3600):
        raise HTTPException(
            status_code=429,
            detail="Too many registration attempts from this IP. Please try again later.",
        )

    # Duplicate check
    existing = await db.users.find_one({"email": email}, {"_id": 0, "user_id": 1})
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    user_id = f"user_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    role = "admin" if email in ADMIN_EMAILS else "student"

    user_doc = {
        "user_id": user_id,
        "email": email,
        "name": body.name,
        "password_hash": hash_password(body.password),
        "role": role,
        "avatar": None,
        "xp": 0, "level": 1, "streak": 0, "longest_streak": 0,
        "last_active": now.isoformat(),
        "class_level": body.class_level or "9",
        "school": body.school or None,
        "achievements": [],
        "created_at": now.isoformat(),
        "auth_type": "jwt",
        "credits": 100,
        "is_verified": True,
        "email_verified": True,
        "status": "active",
        "verified_at": now.isoformat(),
        "is_tutorial_seen": False,
    }
    await db.users.insert_one(user_doc)

    # Send welcome email (non-blocking)
    import asyncio
    asyncio.create_task(send_welcome_email(email, body.name))

    _set_auth_cookies(response, user_id, email)
    user_doc = _strip_sensitive(user_doc)
    return {**user_doc, "message": "Account created successfully! Welcome to AceIt AI."}


# ── Login ─────────────────────────────────────────────────────────────────────

@router.post("/auth/login")
async def login(body: UserLogin, request: Request, response: Response):
    client_ip = _get_client_ip(request)

    if not _check_rate_limit(f"login:{client_ip}", 10, 3600):
        raise HTTPException(
            status_code=429,
            detail="Too many login attempts. Please try again later.",
        )

    email = body.email.lower().strip()
    user  = await db.users.find_one({"email": email}, {"_id": 0})

    if not user or not user.get("password_hash") or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Ensure admin status is up-to-date
    if email in ADMIN_EMAILS and user.get("role") != "admin":
        await db.users.update_one({"user_id": user["user_id"]}, {"$set": {"role": "admin"}})
        user["role"] = "admin"

    now    = datetime.now(timezone.utc)
    streak = user.get("streak", 0)
    last_active_str = user.get("last_active", "")
    if last_active_str:
        try:
            la = datetime.fromisoformat(last_active_str)
            if la.tzinfo is None:
                la = la.replace(tzinfo=timezone.utc)
            diff = (now.date() - la.date()).days
            streak = streak + 1 if diff == 1 else (1 if diff > 1 else streak)
        except Exception:
            streak = 1

    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {"last_active": now.isoformat(), "streak": streak,
                  "longest_streak": max(streak, user.get("longest_streak", 0)),
                  "is_verified": True, "status": "active"}},
    )

    _set_auth_cookies(response, user["user_id"], email)
    user = _strip_sensitive(user)
    user["streak"] = streak
    return user


# ── Verify email (kept for backward compat / existing links) ──────────────────

@router.get("/auth/verify-email")
async def verify_email(token: str):
    """Legacy endpoint — kept so old verification links don't 404."""
    return {"success": True, "message": "Account is active. Please log in."}


# ── Standard auth ─────────────────────────────────────────────────────────────

@router.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    response.delete_cookie("session_token")
    return {"message": "Logged out successfully"}


@router.get("/auth/me")
async def get_me(request: Request):
    return await get_current_user(request)


@router.post("/auth/refresh")
async def refresh_token(request: Request, response: Response):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="No refresh token")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await db.users.find_one({"user_id": payload["sub"]}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        response.set_cookie(
            "access_token", create_access_token(payload["sub"], user["email"]),
            httponly=True, secure=False, samesite="lax", max_age=3600, path="/",
        )
        return {"message": "Token refreshed"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")


# ── Google OAuth ──────────────────────────────────────────────────────────────

@router.post("/google-auth/session")
async def google_session(body: GoogleSessionRequest, response: Response):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": body.session_id},
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Invalid session")
        data = resp.json()

    email = data.get("email", "").lower().strip()
    existing = await db.users.find_one({"email": email}, {"_id": 0})
    role = "admin" if email in ADMIN_EMAILS else "student"

    if existing:
        user_id = existing["user_id"]
        now = datetime.now(timezone.utc)
        streak = existing.get("streak", 0)
        last_active_str = existing.get("last_active", "")
        if last_active_str:
            try:
                la = datetime.fromisoformat(last_active_str)
                if la.tzinfo is None:
                    la = la.replace(tzinfo=timezone.utc)
                diff = (now.date() - la.date()).days
                streak = streak + 1 if diff == 1 else (1 if diff > 1 else streak)
            except Exception:
                pass
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {
                "name": data.get("name", existing["name"]),
                "avatar": data.get("picture"),
                "last_active": now.isoformat(),
                "streak": streak,
                "is_verified": True,
                "email_verified": True,
                "status": "active",
                "role": role,
            }},
        )
    else:
        user_id  = f"user_{uuid.uuid4().hex[:12]}"
        now_iso  = datetime.now(timezone.utc).isoformat()
        await db.users.insert_one({
            "user_id": user_id, "email": email,
            "name": data.get("name", email), "avatar": data.get("picture"),
            "role": role, "xp": 0, "level": 1, "streak": 1, "longest_streak": 1,
            "last_active": now_iso, "class_level": "9", "achievements": [],
            "created_at": now_iso, "auth_type": "google", "credits": 100,
            "is_verified": True, "email_verified": True,
            "status": "active", "verified_at": now_iso,
        })

    session_token = secrets.token_urlsafe(32)
    expires_at    = datetime.now(timezone.utc) + timedelta(days=7)
    await db.user_sessions.insert_one({
        "user_id": user_id, "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    response.set_cookie("session_token", session_token, httponly=True, secure=True,
                        samesite="none", max_age=604800, path="/")
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    return _strip_sensitive(user)


@router.post("/google-auth/logout")
async def google_logout(request: Request, response: Response):
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    response.delete_cookie("session_token")
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out"}


@router.put("/users/class")
async def update_class(body: UpdateClassRequest, request: Request):
    user = await get_current_user(request)
    if body.class_level not in get_classes():
        raise HTTPException(status_code=400, detail="Invalid class level")
    # Create a grade change request for admin notification
    await db.grade_change_requests.insert_one({
        "request_id": f"gcr_{uuid.uuid4().hex[:10]}",
        "user_id": user["user_id"],
        "user_name": user.get("name", ""),
        "user_email": user.get("email", ""),
        "old_class": user.get("class_level", ""),
        "new_class": body.class_level,
        "status": "approved",  # auto-approved; admin can review
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    await db.users.update_one({"user_id": user["user_id"]}, {"$set": {"class_level": body.class_level}})
    return {"message": "Class updated", "class_level": body.class_level}


@router.put("/users/school")
async def update_school(request: Request, body: dict):
    """Set or update the school for a user (used by the onboarding modal)."""
    user = await get_current_user(request)
    school_id = (body.get("school") or "").strip()
    if not school_id:
        raise HTTPException(status_code=400, detail="School is required")
    from school_curriculum import SCHOOLS
    if school_id not in SCHOOLS:
        raise HTTPException(status_code=400, detail="Invalid school selection")
    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {"school": school_id}}
    )
    return {"message": "School updated", "school": school_id}




@router.patch("/auth/tutorial/seen")
async def mark_tutorial_seen(request: Request):
    """Mark tutorial as seen in DB — call when user dismisses or completes tutorial."""
    user = await get_current_user(request)
    await db.users.update_one({"user_id": user["user_id"]}, {"$set": {"is_tutorial_seen": True}})
    return {"success": True}
