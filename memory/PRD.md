# NeuraLearn - AI-Powered CBSE Learning Platform

## Overview
Production-level full-stack AI-powered CBSE learning platform: ChatGPT-style intelligence, Duolingo-style gamification, Pixar-level cinematic UI. Dark theme, neon glows, glassmorphism, Framer Motion driven.

## Architecture
- **Frontend**: React 18 + TailwindCSS + Framer Motion + Three.js + GSAP + Recharts + Redux Toolkit
- **Backend**: FastAPI (modular routers) + Motor (MongoDB async)
- **AI**: OpenAI GPT-4o (user's own key) via streaming SSE
- **DB**: MongoDB (test_database)
- **Auth**: JWT (email/password) + Emergent Google OAuth

### Backend Module Layout (Feb 2026 refactor)
```
backend/
├── server.py             # Thin FastAPI entrypoint (~110 lines), mounts routers
├── core.py               # Config, DB client, OpenAI client, get_current_user, hash helpers
├── models.py             # All Pydantic request models
├── cbse_data.py          # Static CBSE syllabus
└── routes/
    ├── auth.py           # JWT register/login + Google OAuth + /users/class
    ├── chat.py           # Streaming GPT-4o tutor
    ├── syllabus.py       # Syllabus + progress
    ├── quiz.py           # Quiz generate/submit + gamification stats
    ├── mock_exam.py      # Mock exam + adaptive follow-up quiz
    ├── study_plan.py     # AI exam-date study plan
    └── social.py         # Leaderboard + recommendations + referrals
```

## Implemented

### Phase 1
- JWT + Google OAuth auth flows
- Cinematic IntroScreen (Three.js + GSAP)
- Dashboard, AI Chat (streaming GPT-4o, [QUIZ]/[YOUTUBE] tag parsing), Syllabus, Progress, QuizArena, Profile
- Full CBSE syllabus (classes 6–12) with mastery tracking
- Gamification: XP, levels, streaks, achievements

### Phase 2 (Feb 2026)
- **Leaderboard / Rankings** — Global / Class-level / Friends scopes via `?scope=` query. Friends = bidirectional referral graph + self. 3-tab toggle UI on Rankings page.
- **Mock Exam** — AI-generated CBSE-pattern paper with 3 sections, timer, scoring, weak-topic detection
- **Adaptive Follow-up Quiz** — `POST /api/mock-exam/{exam_id}/followup-quiz` generates a 5-Q MCQ laser-focused on the user's weak topics; inline UI on the result screen, full submission flow with XP
- **Study Plan** — exam-date input → AI weekly plan with daily tasks, exam-week strategy, tips
- **Referrals & Rewards** — referral code + apply flow (rejects self/duplicate), XP bonus for both sides
- **AI Chat: YouTube Visual Boost + Next Step** — system prompt emits `[YOUTUBE]…[/YOUTUBE]` tags and a mandatory Next-Step marker (⚡/🎯/🚀/🎬/📝). Frontend renders an inline YouTube embed card.
- **Dashboard: Today's Missions widget** — personalized recommendation cards from `/api/recommendations` (resume / revise / practice / mock exam / explore)
- **Streak Reminder** — `GET /api/streak-reminder` returns streak state with at_risk/broken flags + AI-personalized message (only when at-risk). Sticky banner on Dashboard with daily dismiss + native Browser Notification API opt-in.
- **Signup with class selection** — `POST /api/auth/register` now accepts `class_level` field (default "9")

### Testing
- **30/31 pytest backend tests pass** across `test_phase2.py`, `test_followup_quiz.py`, `test_leaderboard_scopes.py`, `test_streak_reminder.py` (1 occasional skip due to OpenAI generation variability)
- Full Playwright walkthrough on Dashboard + Mock Exam end-to-end

## Prioritized Backlog

### P1 (Next)
- Real YouTube Data API v3 integration (thumbnails + verified videos vs current no-API search embed)
- Cosmetic unlocks tied to referral milestones (avatar borders, profile themes)
- Email/push reminders (needs RESEND_API_KEY or SENDGRID_API_KEY — backend hook + service worker for true off-session delivery)
- Class selector dropdown on signup form (backend already accepts class_level)

### P2 (Future)
- Multi-language (Hindi medium)
- Parent / Teacher / School admin dashboards
- Voice input for chat (Whisper)
- PWA / offline mode
- Further cinematic intro polish

## Tech Debt / Refactor
- ✅ Split monolithic `server.py` (1148 → ~110 lines) into `routes/` modules + `core.py`/`models.py`
- ✅ Wrap GPT-4o calls in mock-exam/study-plan/quiz with try/except → return clean 502
- ✅ Replace `body: dict` in `/api/referral/apply` with `ReferralApplyRequest`
- Pending: Migrate native `<select>` in MockExamPage to shadcn Select for design consistency

## Environment
- `OPENAI_API_KEY`: User-provided GPT-4o key (backend/.env)
- `JWT_SECRET`, `MONGO_URL`, `DB_NAME`, `FRONTEND_URL`: backend/.env
- `REACT_APP_BACKEND_URL`: frontend/.env
