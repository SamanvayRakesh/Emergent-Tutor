"""Auth: JWT register/login + Google OAuth session."""
import uuid
import secrets
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

router = APIRouter()


@router.post("/auth/register")
async def register(body: UserRegister, response: Response):
    email = body.email.lower().strip()
    if await db.users.find_one({"email": email}, {"_id": 0}):
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = f"user_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    user_doc = {
        "user_id": user_id, "email": email, "name": body.name,
        "password_hash": hash_password(body.password),
        "role": "student", "avatar": None,
        "xp": 0, "level": 1, "streak": 0, "longest_streak": 0,
        "last_active": now, "class_level": "9",
        "achievements": [], "created_at": now, "auth_type": "jwt",
    }
    await db.users.insert_one(user_doc)

    response.set_cookie("access_token", create_access_token(user_id, email), httponly=True, secure=False, samesite="lax", max_age=3600, path="/")
    response.set_cookie("refresh_token", create_refresh_token(user_id), httponly=True, secure=False, samesite="lax", max_age=604800, path="/")

    user_doc.pop("password_hash", None)
    user_doc.pop("_id", None)
    return user_doc


@router.post("/auth/login")
async def login(body: UserLogin, response: Response):
    email = body.email.lower().strip()
    user = await db.users.find_one({"email": email}, {"_id": 0})
    if not user or not user.get("password_hash") or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # streak update
    now = datetime.now(timezone.utc)
    streak = user.get("streak", 0)
    last_active_str = user.get("last_active", "")
    if last_active_str:
        try:
            la = datetime.fromisoformat(last_active_str)
            if la.tzinfo is None:
                la = la.replace(tzinfo=timezone.utc)
            diff = (now.date() - la.date()).days
            if diff == 1:
                streak += 1
            elif diff > 1:
                streak = 1
        except Exception:
            streak = 1
    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {"last_active": now.isoformat(), "streak": streak,
                  "longest_streak": max(streak, user.get("longest_streak", 0))}},
    )

    response.set_cookie("access_token", create_access_token(user["user_id"], email), httponly=True, secure=False, samesite="lax", max_age=3600, path="/")
    response.set_cookie("refresh_token", create_refresh_token(user["user_id"]), httponly=True, secure=False, samesite="lax", max_age=604800, path="/")

    user.pop("password_hash", None)
    user["streak"] = streak
    return user


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
        response.set_cookie("access_token", create_access_token(payload["sub"], user["email"]), httponly=True, secure=False, samesite="lax", max_age=3600, path="/")
        return {"message": "Token refreshed"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")


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
                if diff == 1:
                    streak += 1
                elif diff > 1:
                    streak = 1
            except Exception:
                pass
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"name": data.get("name", existing["name"]), "avatar": data.get("picture"),
                      "last_active": now.isoformat(), "streak": streak}},
        )
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        await db.users.insert_one({
            "user_id": user_id, "email": email,
            "name": data.get("name", email), "avatar": data.get("picture"),
            "role": "student", "xp": 0, "level": 1, "streak": 1, "longest_streak": 1,
            "last_active": now_iso, "class_level": "9", "achievements": [],
            "created_at": now_iso, "auth_type": "google",
        })

    session_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    await db.user_sessions.insert_one({
        "user_id": user_id, "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    response.set_cookie("session_token", session_token, httponly=True, secure=True, samesite="none", max_age=604800, path="/")

    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    user.pop("password_hash", None)
    return user


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
    await db.users.update_one({"user_id": user["user_id"]}, {"$set": {"class_level": body.class_level}})
    return {"message": "Class updated", "class_level": body.class_level}
