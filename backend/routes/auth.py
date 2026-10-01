"""Auth: JWT register/login + Google OAuth session."""
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
    db,
    logger,
    JWT_SECRET,
    JWT_ALGORITHM,
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    get_current_user,
)
from models import (
    UserRegister,
    UserLogin,
    GoogleSessionRequest,
    UpdateClassRequest,
)
from cbse_data import get_classes
from email_service import send_welcome_email, validate_email_quality
from school_curriculum import SCHOOL_LIST, SCHOOLS

router = APIRouter()

ADMIN_EMAILS = {
    "taniknpoojari@gmail.com",
    "truecursemahito28@gmail.com",
    "samanvayrakesh7@gmail.com",
}


@router.get("/auth/schools")
async def list_schools():
    return {"schools": SCHOOL_LIST}


SPECIAL_CHARS = r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?`~]"


def validate_password(password: str) -> tuple[bool, str]:
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."

    if not re.search(SPECIAL_CHARS, password):
        return (
            False,
            "Password must contain at least one special character "
            "(e.g. @, #, !, $).",
        )

    return True, ""


_rate_store: dict = defaultdict(list)


def _check_rate_limit(
    key: str,
    max_calls: int,
    window_seconds: int,
) -> bool:
    now = time.monotonic()
    cutoff = now - window_seconds

    _rate_store[key] = [
        timestamp
        for timestamp in _rate_store[key]
        if timestamp > cutoff
    ]

    if len(_rate_store[key]) >= max_calls:
        return False

    _rate_store[key].append(now)
    return True


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")

    if forwarded:
        return forwarded.split(",")[0].strip()

    return request.client.host if request.client else "unknown"


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _set_auth_cookies(
    response: Response,
    user_id: str,
    email: str,
):
    response.set_cookie(
        "access_token",
        create_access_token(user_id, email),
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=3600,
        path="/",
    )

    response.set_cookie(
        "refresh_token",
        create_refresh_token(user_id),
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=604800,
        path="/",
    )


def _strip_sensitive(user: dict) -> dict:
    for key in (
        "password_hash",
        "_id",
        "verification_token",
        "verification_token_hash",
        "resend_cooldown_until",
    ):
        user.pop(key, None)

    return user


def get_signup_school_fields(school_id, class_level=None):
    """Shared school-saving logic for email signup and the existing modal."""
    if not school_id:
        return {
            "school": None,
            "class_level": class_level,
        }

    school = SCHOOLS.get(school_id)

    if not school:
        raise HTTPException(
            status_code=400,
            detail="Invalid school selection",
        )

    grades = school.get("available_grades", [])

    selected_level = (
        str(grades[0])
        if len(grades) == 1
        else str(class_level or "")
    )

    if selected_level not in school.get("curriculum", {}):
        raise HTTPException(
            status_code=400,
            detail="This school's curriculum is not available yet",
        )

    return {
        "school": school_id,
        "class_level": selected_level,
    }


@router.post("/auth/register")
async def register(
    body: UserRegister,
    request: Request,
    response: Response,
):
    client_ip = _get_client_ip(request)
    email = body.email.lower().strip()

    is_valid, reason = await validate_email_quality(email)

    if not is_valid:
        raise HTTPException(status_code=422, detail=reason)

    pw_ok, pw_reason = validate_password(body.password)

    if not pw_ok:
        raise HTTPException(status_code=422, detail=pw_reason)

    if not _check_rate_limit(f"register:{client_ip}", 5, 3600):
        raise HTTPException(
            status_code=429,
            detail=(
                "Too many registration attempts from this IP. "
                "Please try again later."
            ),
        )

    existing = await db.users.find_one(
        {"email": email},
        {"_id": 0, "user_id": 1},
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="An account with this email already exists.",
        )

    user_id = f"user_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    role = "admin" if email in ADMIN_EMAILS else "student"

    school_fields = get_signup_school_fields(
        body.school,
        body.class_level or "9",
    )

    user_doc = {
        "user_id": user_id,
        "email": email,
        "name": body.name,
        "password_hash": hash_password(body.password),
        "role": role,
        "avatar": None,
        "xp": 0,
        "level": 1,
        "streak": 0,
        "longest_streak": 0,
        "last_active": now.isoformat(),
        **school_fields,
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

    import asyncio

    asyncio.create_task(send_welcome_email(email, body.name))

    _set_auth_cookies(response, user_id, email)
    user_doc = _strip_sensitive(user_doc)

    return {
        **user_doc,
        "message": "Account created successfully! Welcome to AceIt AI.",
    }


@router.post("/auth/login")
async def login(
    body: UserLogin,
    request: Request,
    response: Response,
):
    client_ip = _get_client_ip(request)

    if not _check_rate_limit(f"login:{client_ip}", 10, 3600):
        raise HTTPException(
            status_code=429,
            detail="Too many login attempts. Please try again later.",
        )

    email = body.email.lower().strip()

    user = await db.users.find_one(
        {"email": email},
        {"_id": 0},
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    if (
        not user.get("password_hash")
        and user.get("auth_type") == "google"
    ):
        raise HTTPException(
            status_code=401,
            detail=(
                "This account was created with Google Sign-In. "
                "Please use the 'Continue with Google' button to log in."
            ),
        )

    if (
        not user.get("password_hash")
        or not verify_password(
            body.password,
            user["password_hash"],
        )
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    if email in ADMIN_EMAILS and user.get("role") != "admin":
        await db.users.update_one(
            {"user_id": user["user_id"]},
            {"$set": {"role": "admin"}},
        )
        user["role"] = "admin"

    if email in ADMIN_EMAILS:
        far_future = (
            datetime.now(timezone.utc) + timedelta(days=36500)
        ).isoformat()

        await db.subscriptions.update_one(
            {"user_id": user["user_id"]},
            {
                "$set": {
                    "plan": "pro",
                    "status": "active",
                    "billing_cycle": "lifetime",
                    "expires_at": far_future,
                    "started_at": datetime.now(timezone.utc).isoformat(),
                    "user_id": user["user_id"],
                }
            },
            upsert=True,
        )

    now = datetime.now(timezone.utc)
    streak = user.get("streak", 0)
    last_active_str = user.get("last_active", "")

    if last_active_str:
        try:
            last_active = datetime.fromisoformat(last_active_str)

            if last_active.tzinfo is None:
                last_active = last_active.replace(tzinfo=timezone.utc)

            difference = (now.date() - last_active.date()).days

            streak = (
                streak + 1
                if difference == 1
                else 1
                if difference > 1
                else streak
            )
        except Exception:
            streak = 1

    await db.users.update_one(
        {"user_id": user["user_id"]},
        {
            "$set": {
                "last_active": now.isoformat(),
                "streak": streak,
                "longest_streak": max(
                    streak,
                    user.get("longest_streak", 0),
                ),
                "is_verified": True,
                "status": "active",
            }
        },
    )

    if user.get("school") == "nios":
        if str(user.get("class_level")) != "10":
            await db.users.update_one(
                {"user_id": user["user_id"]},
                {"$set": {"class_level": "10"}},
            )
            user["class_level"] = "10"

    _set_auth_cookies(response, user["user_id"], email)
    user = _strip_sensitive(user)
    user["streak"] = streak

    return user


@router.get("/auth/verify-email")
async def verify_email(token: str):
    return {
        "success": True,
        "message": "Account is active. Please log in.",
    }


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
async def refresh_token(
    request: Request,
    response: Response,
):
    token = request.cookies.get("refresh_token")

    if not token:
        raise HTTPException(
            status_code=401,
            detail="No refresh token",
        )

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=401,
                detail="Invalid token type",
            )

        user = await db.users.find_one(
            {"user_id": payload["sub"]},
            {"_id": 0},
        )

        if not user:
            raise HTTPException(
                status_code=401,
                detail="User not found",
            )

        response.set_cookie(
            "access_token",
            create_access_token(payload["sub"], user["email"]),
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=3600,
            path="/",
        )

        return {"message": "Token refreshed"}

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Refresh token expired",
        )


@router.post("/google-auth/session")
async def google_session(
    body: GoogleSessionRequest,
    response: Response,
):
    async with httpx.AsyncClient() as client:
        result = await client.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": body.session_id},
        )

        if result.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail="Invalid session",
            )

        data = result.json()

    email = data.get("email", "").lower().strip()

    existing = await db.users.find_one(
        {"email": email},
        {"_id": 0},
    )

    role = "admin" if email in ADMIN_EMAILS else "student"

    if existing:
        user_id = existing["user_id"]
        now = datetime.now(timezone.utc)
        streak = existing.get("streak", 0)
        last_active_str = existing.get("last_active", "")

        if last_active_str:
            try:
                last_active = datetime.fromisoformat(last_active_str)

                if last_active.tzinfo is None:
                    last_active = last_active.replace(tzinfo=timezone.utc)

                difference = (now.date() - last_active.date()).days

                streak = (
                    streak + 1
                    if difference == 1
                    else 1
                    if difference > 1
                    else streak
                )
            except Exception:
                pass

        update_data = {
            "name": data.get("name", existing.get("name", email)),
            "avatar": data.get("picture"),
            "last_active": now.isoformat(),
            "streak": streak,
            "is_verified": True,
            "email_verified": True,
            "status": "active",
            "role": role,
        }

        if existing.get("school"):
            update_data.update(
                get_signup_school_fields(
                    existing["school"],
                    existing.get("class_level"),
                )
            )

        await db.users.update_one(
            {"user_id": user_id},
            {"$set": update_data},
        )

    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(timezone.utc).isoformat()

        # The existing school modal completes school selection.
        await db.users.insert_one(
            {
                "user_id": user_id,
                "email": email,
                "name": data.get("name", email),
                "avatar": data.get("picture"),
                "role": role,
                "xp": 0,
                "level": 1,
                "streak": 1,
                "longest_streak": 1,
                "last_active": now_iso,
                "class_level": None,
                "school": None,
                "is_onboarded": False,
                "achievements": [],
                "created_at": now_iso,
                "auth_type": "google",
                "credits": 100,
                "is_verified": True,
                "email_verified": True,
                "status": "active",
                "verified_at": now_iso,
                "is_tutorial_seen": False,
            }
        )

    session_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    await db.user_sessions.insert_one(
        {
            "user_id": user_id,
            "session_token": session_token,
            "expires_at": expires_at.isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )

    response.set_cookie(
        "session_token",
        session_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=604800,
        path="/",
    )

    user = await db.users.find_one(
        {"user_id": user_id},
        {"_id": 0},
    )

    return _strip_sensitive(user)


@router.post("/google-auth/logout")
async def google_logout(
    request: Request,
    response: Response,
):
    session_token = request.cookies.get("session_token")

    if session_token:
        await db.user_sessions.delete_one(
            {"session_token": session_token}
        )

    response.delete_cookie("session_token")
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return {"message": "Logged out"}


@router.put("/users/class")
async def update_class(
    body: UpdateClassRequest,
    request: Request,
):
    user = await get_current_user(request)

    if body.class_level not in get_classes():
        raise HTTPException(
            status_code=400,
            detail="Invalid class level",
        )

    await db.grade_change_requests.insert_one(
        {
            "request_id": f"gcr_{uuid.uuid4().hex[:10]}",
            "user_id": user["user_id"],
            "user_name": user.get("name", ""),
            "user_email": user.get("email", ""),
            "old_class": user.get("class_level", ""),
            "new_class": body.class_level,
            "status": "approved",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )

    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {"class_level": body.class_level}},
    )

    return {
        "message": "Class updated",
        "class_level": body.class_level,
    }


@router.put("/users/school")
async def update_school(
    request: Request,
    body: dict,
):
    user = await get_current_user(request)
    school_id = str(body.get("school") or "").strip()

    if not school_id:
        raise HTTPException(
            status_code=400,
            detail="School is required",
        )

    school_fields = get_signup_school_fields(
        school_id,
        user.get("class_level"),
    )

    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": school_fields},
    )

    return {
        "message": "School and curriculum updated",
        **school_fields,
    }


@router.patch("/auth/tutorial/seen")
async def mark_tutorial_seen(request: Request):
    user = await get_current_user(request)

    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {"is_tutorial_seen": True}},
    )

    return {"success": True}


@router.put("/auth/update-name")
async def update_display_name(request: Request):
    user = await get_current_user(request)
    body = await request.json()
    new_name = (body.get("name") or "").strip()

    if not new_name or len(new_name) < 2:
        raise HTTPException(
            status_code=400,
            detail="Name must be at least 2 characters.",
        )

    if len(new_name) > 40:
        raise HTTPException(
            status_code=400,
            detail="Name must be 40 characters or fewer.",
        )

    document = await db.users.find_one(
        {"user_id": user["user_id"]},
        {"name_changed_at": 1, "_id": 0},
    )

    if document and document.get("name_changed_at"):
        try:
            last_change = datetime.fromisoformat(
                document["name_changed_at"]
            )

            if last_change.tzinfo is None:
                last_change = last_change.replace(tzinfo=timezone.utc)

            difference = datetime.now(timezone.utc) - last_change

            if difference.days < 7:
                days_left = 7 - difference.days

                raise HTTPException(
                    status_code=429,
                    detail=(
                        f"You can change your name again in {days_left} "
                        f"day{'s' if days_left != 1 else ''}."
                    ),
                )

        except HTTPException:
            raise
        except Exception:
            pass

    await db.users.update_one(
        {"user_id": user["user_id"]},
        {
            "$set": {
                "name": new_name,
                "name_changed_at": datetime.now(timezone.utc).isoformat(),
            }
        },
    )

    return {
        "success": True,
        "name": new_name,
    }