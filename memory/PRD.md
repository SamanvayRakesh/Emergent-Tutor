# NeuraLearn - AI-Powered CBSE Learning Platform

## Overview
Production-level full-stack AI-powered CBSE learning platform: ChatGPT-style intelligence, Duolingo-style gamification, Pixar-level cinematic UI. Dark theme, neon glows, glassmorphism, Framer Motion driven.

## Architecture
- **Frontend**: React 18 + TailwindCSS + Framer Motion + Three.js + GSAP + Recharts + Redux Toolkit
- **Backend**: FastAPI + Motor (MongoDB async)
- **AI**: OpenAI GPT-4o (user's own key) via streaming SSE
- **DB**: MongoDB (test_database)
- **Auth**: JWT (email/password) + Emergent Google OAuth

## Implemented

### Phase 1 (Complete)
- JWT + Google OAuth auth flows
- Cinematic IntroScreen (Three.js + GSAP)
- Dashboard, AI Chat (streaming GPT-4o with quiz tag parsing), Syllabus, Progress, QuizArena, Profile
- Full CBSE syllabus (classes 6–12) with mastery tracking
- Gamification: XP, levels, streaks, achievements

### Phase 2 (Complete — Feb 2026)
- **Backend (server.py)**:
  - `GET /api/leaderboard` — global ranking, current-user position, podium data
  - `POST /api/mock-exam/generate` — AI-generated CBSE-pattern paper (3 sections)
  - `GET /api/mock-exam/history` — user exam history
  - `POST /api/mock-exam/{exam_id}/submit` — scoring, section breakdown, weak topics, XP
  - `POST /api/study-plan` / `GET /api/study-plan` — AI exam-date-based study plan
  - `GET /api/recommendations` — personalized next actions
  - `GET /api/referral/code` / `POST /api/referral/apply` — referral system with XP bonuses
  - AI chat system prompt upgraded: emits `[YOUTUBE]query[/YOUTUBE]` for visual concepts, ends every reply with a mandatory Next-Step marker (⚡/🎯/🚀/🎬/📝)
- **Frontend**:
  - `LeaderboardPage` — podium + ranked list with current-user highlight
  - `MockExamPage` — configure → timed exam → results with section breakdown + weak topics
  - `StudyPlanPage` — exam-date input → AI-generated weekly plan + referral panel
  - `ChatPage` now parses `[YOUTUBE]…[/YOUTUBE]` and renders an inline embeddable YouTube search card
  - Sidebar nav extended: Mock Exams, Study Plan, Rankings
  - Routes wired in `App.js`

### Testing
- 13/13 pytest backend tests pass — `/app/backend/tests/test_phase2.py`
- Frontend Playwright smoke verified all Phase 2 pages render and complete user flows

## Prioritized Backlog

### P1 (Next)
- Visual-only mode for YouTube (use YouTube Data API v3 for real video previews + thumbnails)
- Adaptive mock-exam analysis → auto-generate weak-area follow-up quizzes
- Daily AI recommendations widget on Dashboard
- Cosmetic unlocks tied to referral milestones

### P2 (Future)
- Multi-language (Hindi medium)
- Parent / Teacher / School admin dashboards
- Voice input for chat (Whisper)
- PWA / offline mode
- Further cinematic intro polish

## Tech Debt / Refactor
- `server.py` is 1148 lines — split into `routes/{auth,chat,mock_exam,study_plan,leaderboard,referral}.py` (per >700-line guideline)
- Replace `body: dict` in `/api/referral/apply` with a Pydantic model
- Wrap GPT-4o calls in mock-exam/study-plan with try/except → friendly 502 on JSON parse failure
- Migrate native `<select>` in MockExamPage to shadcn Select for design consistency

## Environment
- `OPENAI_API_KEY`: User-provided GPT-4o key (backend/.env)
- `JWT_SECRET`, `MONGO_URL`, `DB_NAME`: backend/.env
- `REACT_APP_BACKEND_URL`: frontend/.env
