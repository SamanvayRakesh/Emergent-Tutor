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
- **Leaderboard / Rankings** — global ranking, podium, current user position
- **Mock Exam** — AI-generated CBSE-pattern paper with 3 sections, timer, scoring, weak-topic detection
- **Adaptive Follow-up Quiz** — `POST /api/mock-exam/{exam_id}/followup-quiz` generates a 5-Q MCQ laser-focused on the user's weak topics; inline UI on the result screen, full submission flow with XP
- **Study Plan** — exam-date input → AI weekly plan with daily tasks, exam-week strategy, tips
- **Referrals & Rewards** — referral code + apply flow (rejects self/duplicate), XP bonus for both sides
- **AI Chat: YouTube Visual Boost + Next Step** — system prompt emits `[YOUTUBE]…[/YOUTUBE]` tags and a mandatory Next-Step marker (⚡/🎯/🚀/🎬/📝). Frontend renders an inline YouTube embed card.
- **Dashboard: Today's Missions widget** — personalized recommendation cards from `/api/recommendations` (resume / revise / practice / mock exam / explore), each clickable to the right route

### Testing
- **19/19 pytest backend tests pass** — `/app/backend/tests/test_phase2.py` (13) + `/app/backend/tests/test_followup_quiz.py` (6)
- Full Playwright walkthrough on Dashboard + Mock Exam end-to-end (generate → take → submit → weak-areas → follow-up quiz → submit)

## Prioritized Backlog

### P1 (Next)
- Real YouTube Data API v3 integration (thumbnails + verified videos vs current no-API search embed)
- Daily streak email/push reminders
- Class-level + Friends leaderboards (currently global only)
- Cosmetic unlocks tied to referral milestones (avatar borders, profile themes)

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
