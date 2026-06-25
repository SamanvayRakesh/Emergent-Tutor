# AceIt AI — Product Requirements Document

## Original Problem Statement
Build "AceIt AI" (formerly NeuraLearn), a complete production-level full-stack AI-powered CBSE learning platform for Classes 6–12. Features include an interactive personalized AI tutor, gamification (XP/levels/streaks), advanced mock exams, visual learning with KaTeX math rendering, and an NCERT-verified syllabus. The platform must have production-grade security, email verification, and a credit-based AI usage system.

## Target Users
- CBSE students Classes 6–12
- Students preparing for JEE, NEET, Board exams

## Tech Stack
- **Frontend**: React 18, TailwindCSS, Framer Motion, KaTeX, Lucide Icons
- **Backend**: FastAPI (Python), MongoDB (Motor async), JWT Auth
- **Integrations**: OpenAI GPT-4o, Resend (email), Emergent Google Auth, Razorpay (payment)
- **Libraries**: PyMuPDF (PDF extraction), dnspython (MX lookup), bcrypt, slowapi

## Core Architecture
```
/app/
├── backend/
│   ├── server.py              # FastAPI app, startup, cleanup task
│   ├── core.py                # DB, JWT, bcrypt helpers
│   ├── models.py              # Pydantic request/response models
│   ├── email_service.py       # Resend integration + email validation
│   ├── adaptive_engine.py     # Adaptive learning engine
│   ├── credits.py             # Dynamic credit math (2-10 credits/response)
│   ├── curriculum_engine.py   # NCERT curriculum loading
│   ├── scripts/
│   │   └── build_question_bank.py  # PDF → Q&A extraction
│   └── routes/
│       ├── auth.py            # JWT + Google auth, email verification
│       ├── chat.py            # AI streaming chat
│       ├── analytics.py       # Learning analytics
│       ├── quiz.py            # Interactive quiz system
│       ├── mock_exam.py       # Full mock exams
│       ├── study_plan.py      # AI study planner
│       ├── social.py          # Leaderboard, referrals
│       ├── curriculum.py      # NCERT syllabus
│       ├── subscription.py    # Plans & Razorpay
│       └── question_bank.py   # Q&A bank management
├── frontend/
│   └── src/
│       ├── App.js
│       ├── contexts/
│       │   ├── AuthContext.js
│       │   ├── CreditsContext.jsx
│       │   └── SubscriptionContext.jsx
│       └── components/
│           ├── AuthPage.jsx               # Login/Register with email validation
│           ├── EmailVerificationPage.jsx  # Verification flow UI
│           ├── Dashboard.jsx
│           ├── ChatPage.jsx
│           ├── MathRenderer.jsx           # KaTeX integration
│           ├── InteractiveQuizModal.jsx   # Quiz system
│           ├── OnboardingModal.jsx
│           ├── PricingPage.jsx
│           └── ...other pages
└── memory/
    ├── PRD.md
    ├── test_credentials.md
    └── CHANGELOG.md
```

## What Has Been Implemented

### Phase 1: Core Platform (Complete)
- React + FastAPI + MongoDB full-stack app
- JWT authentication + Emergent Google OAuth
- CBSE curriculum engine (Classes 6–12, all subjects)
- AI Chat with OpenAI GPT-4o streaming
- XP/levels/streaks gamification
- Onboarding flow (5 steps)
- Subscription system with Razorpay (mock fallback active)

### Phase 2: Learning Features (Complete)
- Interactive Quiz Modal (5 questions, MCQ format)
- Mock Exam system (full timed exams)
- Study Plan generator
- Progress tracking
- Leaderboard (social)
- Analytics endpoint

### Phase 3: Production Features (Complete — June 2026)
- **Global rebranding to "AceIt AI"**
- **Background Question Bank Builder** (PyMuPDF PDF → Q&A)
- **Mandatory Email Verification** (Resend API integration)
- **Adaptive Learning Engine** (tracks weak/strong topics, pace, accuracy)
- **Dynamic Credit System** (2–10 credits scaled by response word count)
- **AI Response Limit** (1500 words, no mid-sentence truncation)
- **KaTeX Math Rendering** (MathRenderer.jsx across all text)
- **Removed Emergent badge** from index.html

### Phase 4: Production-Grade Email Verification System (Complete — June 2026)
- **Email Quality Validation**: format regex + disposable domain blocklist (120+ domains) + DNS MX record lookup
- **Cryptographic Token Security**: SHA-256 hashed tokens stored in DB
- **24-hour Token Expiry**: tokens expire and can be resent
- **Login Gate**: unverified JWT users cannot login
- **60-second Resend Cooldown**: per-user cooldown stored in DB + countdown UI
- **Rate Limiting**: in-memory per-IP (5 register/hr, 10 login/hr, 3 resend/hr)
- **Account Cleanup**: background task deletes unverified accounts after 48 hours
- **New User Fields**: `email_verified`, `status` (pending_verification/active/suspended), `verified_at`
- **Google Users**: always auto-verified with `status=active`
- **Exact spec messages**: 3 specific UX messages implemented
- **Cooldown Timer UI**: countdown visible in both AuthPage and EmailVerificationPage

## Key DB Schema

### users
```json
{
  "_id": ObjectId,
  "user_id": "user_abc123",
  "email": "user@example.com",
  "name": "Student Name",
  "password_hash": "bcrypt_hash",
  "role": "student|admin",
  "auth_type": "jwt|google",
  "is_verified": true,
  "email_verified": true,
  "status": "pending_verification|active|suspended",
  "verification_token": "sha256_hash",
  "verification_expires": "ISO_datetime",
  "verified_at": "ISO_datetime",
  "resend_cooldown_until": "ISO_datetime",
  "xp": 0, "level": 1, "streak": 0,
  "credits": 100,
  "class_level": "10",
  "plan": "free|pro|elite",
  "created_at": "ISO_datetime"
}
```

### adaptive_profiles
```json
{
  "user_id": "user_abc123",
  "learning_pace": "normal",
  "accuracy": 0.75,
  "weak_topics": ["trigonometry"],
  "strong_topics": ["algebra"],
  "preferred_style": "visual"
}
```

### question_bank
```json
{
  "class_level": "10",
  "subject": "mathematics",
  "chapter": "real_numbers",
  "question": "...",
  "answer": "...",
  "source_file": "filename.pdf"
}
```

## Key API Endpoints
- `GET  /api/auth/me`
- `POST /api/auth/register` — validates email quality (format+disposable+MX), hashes token
- `POST /api/auth/login` — blocks unverified users
- `GET  /api/auth/verify-email?token=X` — SHA-256 hash lookup
- `POST /api/auth/resend-verification` — 60s cooldown, rate limited
- `POST /api/auth/admin/verify-user` — manual admin verify
- `POST /api/chat/stream` — AI streaming chat
- `POST /api/chat/quiz/submit`
- `GET  /api/analytics`
- `POST /api/admin/question-bank/build`

## Prioritized Backlog

### P1 — Next Up
- Phase 8: Personalized Study Plan using quiz/exam history + weak areas
- Phase 9: Friends system + real-time global/friend rankings

### P2 — Upcoming
- Notification system (streak warnings, grade change toasts)
- Password reset flow
- Dashboard greeting truncation fix (first 2 words)

### Completed Phases 6/7/10 (June 2026)
- Phase 6: Quiz Arena — subject→chapter→topic selection, adaptive difficulty auto-set
- Phase 7: Mock exam weak-area persistence to student_profiles, weak-area tracker UI
- Phase 10: ProfilePage subscription management (plan, credits, upgrade, cancel)

### P3 — Future
- Email domain verification at resend.com/domains
- Redis-backed rate limiting for multi-instance
- Admin dashboard
- Account suspension management
