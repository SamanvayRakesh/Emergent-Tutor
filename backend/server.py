"""AceIt AI Backend - FastAPI app entrypoint. Mounts all route modules."""
import os
import uuid
import asyncio
from datetime import datetime, timezone, timedelta
from pathlib import Path

from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware

from core import db, mongo_client, logger, FRONTEND_URL, hash_password
from routes import auth as auth_routes
from routes import chat as chat_routes
from routes import syllabus as syllabus_routes
from routes import quiz as quiz_routes
from routes import mock_exam as mock_exam_routes
from routes import study_plan as study_plan_routes
from routes import social as social_routes
from routes import curriculum as curriculum_routes
from routes import subscription as subscription_routes
from routes import question_bank as question_bank_routes
from routes import analytics as analytics_routes
from routes import admin as admin_routes
from routes import feedback as feedback_routes
from curriculum_engine import load_curriculum_from_json


app = FastAPI(title="AceIt AI API", version="1.0.0")
api_router = APIRouter(prefix="/api")

# Mount feature routers under /api
api_router.include_router(auth_routes.router)
api_router.include_router(chat_routes.router)
api_router.include_router(syllabus_routes.router)
api_router.include_router(quiz_routes.router)
api_router.include_router(mock_exam_routes.router)
api_router.include_router(study_plan_routes.router)
api_router.include_router(social_routes.router)
api_router.include_router(curriculum_routes.router)
api_router.include_router(subscription_routes.router)
api_router.include_router(question_bank_routes.router)
api_router.include_router(analytics_routes.router)
api_router.include_router(admin_routes.router)
api_router.include_router(feedback_routes.router)

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
    # ── Indexes ────────────────────────────────────────────────────────────────
    await db.users.create_index("email", unique=True)
    await db.users.create_index("user_id", unique=True)
    await db.users.create_index("verification_token", sparse=True)
    await db.users.create_index("status", sparse=True)
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
    await db.curriculum.create_index([("class_level", 1), ("subject", 1), ("academic_year", 1)])
    await db.subscriptions.create_index("user_id", unique=True)
    await db.usage_counters.create_index("user_id", unique=True)
    await db.onboarding.create_index("user_id", unique=True)
    await db.credit_analytics.create_index([("user_id", 1), ("timestamp", -1)])
    await db.student_profiles.create_index("user_id", unique=True)

    # ── Backfills ──────────────────────────────────────────────────────────────
    # Existing users without is_verified → mark as verified
    await db.users.update_many(
        {"is_verified": {"$exists": False}},
        {"$set": {"is_verified": True, "email_verified": True, "status": "active"}},
    )
    # Add status=active to all existing verified users missing it
    await db.users.update_many(
        {"is_verified": True, "status": {"$exists": False}},
        {"$set": {"status": "active", "email_verified": True}},
    )
    # Unverified without status → mark pending
    await db.users.update_many(
        {"is_verified": False, "status": {"$exists": False}},
        {"$set": {"status": "pending_verification", "email_verified": False}},
    )
    # Credits backfill
    await db.users.update_many(
        {"credits": {"$exists": False}},
        {"$set": {"credits": 100}},
    )
    # Tutorial backfill: mark all pre-existing accounts as having seen tutorial (one-time migration)
    # New accounts always get is_tutorial_seen=False set explicitly in registration
    await db.users.update_many(
        {"is_tutorial_seen": {"$exists": False}},
        {"$set": {"is_tutorial_seen": True}},
    )

    # ── Curriculum ─────────────────────────────────────────────────────────────
    try:
        await load_curriculum_from_json()
    except Exception as e:
        logger.warning(f"Curriculum load skipped: {e}")

    # ── Auto-build question bank ───────────────────────────────────────────────
    try:
        kb_count = await db.question_bank.count_documents({})
        if kb_count < 100:
            from routes.question_bank import _run_kb_build
            asyncio.create_task(_run_kb_build())
            logger.info("Question bank build started in background (KB was empty)")
    except Exception as e:
        logger.warning(f"QB auto-build skipped: {e}")

    # ── Seed admin ─────────────────────────────────────────────────────────────
    admin_email    = os.environ.get("ADMIN_EMAIL", "admin@neuralearn.ai")
    admin_password = os.environ.get("ADMIN_PASSWORD", "Admin@123456")
    existing = await db.users.find_one({"email": admin_email}, {"_id": 0})
    if not existing:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        await db.users.insert_one({
            "user_id": user_id, "email": admin_email, "name": "AceIt AI Admin",
            "password_hash": hash_password(admin_password),
            "role": "admin", "xp": 5000, "level": 11,
            "streak": 30, "longest_streak": 30, "last_active": now,
            "class_level": "12", "achievements": [],
            "created_at": now, "auth_type": "jwt",
            "credits": 9999,
            "is_verified": True,
            "email_verified": True,
            "status": "active",
            "verified_at": now,
        })
        logger.info(f"Admin seeded: {admin_email}")
    else:
        # Ensure admin is always active/verified
        await db.users.update_one(
            {"email": admin_email},
            {"$set": {"is_verified": True, "email_verified": True, "status": "active"}},
        )

    # ── Seed BNPS test student (idempotent) ───────────────────────────────────
    bnps_email = "bnps@student.edu"
    if not await db.users.find_one({"email": bnps_email}):
        import bcrypt as _bcrypt
        import uuid as _uuid
        bnps_hash = _bcrypt.hashpw(b"Test@12345", _bcrypt.gensalt()).decode()
        await db.users.insert_one({
            "user_id":      str(_uuid.uuid4()),
            "email":        bnps_email,
            "password_hash": bnps_hash,
            "name":         "BNPS Student",
            "class_level":  "8",
            "school":       "brooklyn_national",
            "status":       "active",
            "is_verified":  True,
            "email_verified": True,
            "role":         "student",
            "credits":      100,
            "auth_type":    "jwt",
            "created_at":   datetime.now(timezone.utc).isoformat(),
        })
        logger.info("BNPS test student seeded: bnps@student.edu")

    # ── Background cleanup task ─────────────────────────────────────────────
    # NOTE: Cleanup intentionally disabled — email verification is not enforced,
    # so all registered accounts should remain active regardless of is_verified flag.
    # asyncio.create_task(_cleanup_unverified_accounts())

    # ── Write test credentials ─────────────────────────────────────────────────
    creds_path = Path("/app/memory/test_credentials.md")
    creds_path.parent.mkdir(exist_ok=True)
    creds_path.write_text(f"""# AceIt AI Test Credentials

## Admin Account
- Email: {admin_email}
- Password: {admin_password}
- Role: admin
- Status: verified / active

## BNPS Test Student (Brooklyn National Public School, Grade 8)
- Email: bnps@student.edu
- Password: Test@12345
- School: brooklyn_national (Brooklyn National Public School)
- Class: 8
- Status: verified / active (auto-seeded on startup)
- Note: Sees BNPS Grade 8 chapters (not NCERT)

## Student Test Account
- Email: student@neuralearn.ai
- Password: Student@123
- Note: Register this account via /api/auth/register

## Auth Endpoints
- POST /api/auth/register
- POST /api/auth/login
- POST /api/auth/logout
- GET  /api/auth/me
- GET  /api/auth/verify-email?token=XYZ
- POST /api/auth/resend-verification
- POST /api/google-auth/session

## App URL
- Frontend: {FRONTEND_URL}
- Backend API: {FRONTEND_URL}/api
""")
    logger.info("AceIt AI backend started successfully!")


async def _cleanup_unverified_accounts():
    """Background task: delete unverified JWT accounts older than 48 hours. Runs hourly."""
    while True:
        try:
            await asyncio.sleep(3600)  # Wait 1 hour between runs
            cutoff = datetime.now(timezone.utc) - timedelta(hours=48)
            cutoff_iso = cutoff.isoformat()
            result = await db.users.delete_many({
                "is_verified": False,
                "auth_type": "jwt",
                "created_at": {"$lt": cutoff_iso},
            })
            if result.deleted_count:
                logger.info(f"Cleanup: removed {result.deleted_count} unverified accounts older than 48h")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Cleanup task error: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    mongo_client.close()
