"""NeuraLearn Backend - FastAPI app entrypoint. Mounts all route modules."""
import os
import uuid
from datetime import datetime, timezone
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
from curriculum_engine import load_curriculum_from_json


app = FastAPI(title="NeuraLearn API", version="1.0.0")
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
    await db.curriculum.create_index([("class_level", 1), ("subject", 1), ("academic_year", 1)])
    await db.subscriptions.create_index("user_id", unique=True)
    await db.usage_counters.create_index("user_id", unique=True)
    await db.onboarding.create_index("user_id", unique=True)

    # One-time credits backfill: any user without a credits field gets the 100 starter
    await db.users.update_many(
        {"credits": {"$exists": False}},
        {"$set": {"credits": 100}},
    )

    # Load verified curriculum from scraper output (idempotent — safe to call on every restart)
    try:
        await load_curriculum_from_json()
    except Exception as e:
        logger.warning(f"Curriculum load skipped: {e}")

    # Seed admin
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@neuralearn.ai")
    admin_password = os.environ.get("ADMIN_PASSWORD", "Admin@123456")
    existing = await db.users.find_one({"email": admin_email}, {"_id": 0})
    if not existing:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        await db.users.insert_one({
            "user_id": user_id, "email": admin_email, "name": "NeuraLearn Admin",
            "password_hash": hash_password(admin_password),
            "role": "admin", "xp": 5000, "level": 11,
            "streak": 30, "longest_streak": 30, "last_active": now,
            "class_level": "12", "achievements": [],
            "created_at": now, "auth_type": "jwt",
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
