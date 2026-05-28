# NeuraLearn - AI-Powered CBSE Learning Platform

## Overview
Production-level AI-powered CBSE learning platform with **verified NCERT curriculum engine**, **subscription + plan gating system**, **personalised onboarding**, royal-palette UI (red/blue/gold).

## Architecture
- **Frontend**: React 18 + TailwindCSS + Framer Motion + Three.js + Recharts + Redux Toolkit
- **Backend**: FastAPI (modular routers) + Motor (MongoDB async)
- **AI**: OpenAI GPT-4o (Pro/Elite) / GPT-4o-mini (Free) via streaming SSE
- **Curriculum**: NCERT-verified manifest engine (25 books, 4 subjects, classes 6–12)
- **DB**: MongoDB collections — `users, chat_sessions, messages, progress, quizzes, mock_exams, study_plans, leaderboard, referrals, curriculum, subscriptions, usage_counters, onboarding`
- **Auth**: JWT + Emergent Google OAuth
- **Payments**: Razorpay-ready architecture (currently mocked)

### Backend Module Layout
```
backend/
├── server.py                   # FastAPI entrypoint
├── core.py                     # Config, DB, OpenAI client, auth
├── models.py                   # Pydantic request models
├── plan_gates.py               # Plans catalog + check_limit + has_feature + usage tracking
├── curriculum_engine.py        # NCERT manifest loader + AI grounding
├── routes/
│   ├── auth.py, chat.py, syllabus.py, quiz.py, mock_exam.py,
│   ├── study_plan.py, social.py, curriculum.py
│   └── subscription.py         # NEW — plans, subscribe, onboarding, grade update
├── scripts/
│   ├── ncert_scraper.py
│   └── enrich_titles.py
└── curriculum_data/
    ├── ncert_books.json
    └── ncert_ai_ready/ncert_ai_metadata.json + PDFs
```

## Phase 4 — Subscription & Onboarding (Feb 2026)

### Onboarding (5-step modal — blocks app access until completed)
1. Name
2. Grade (Classes 6–12) — **locks user's syllabus to this grade**
3. Exam goal (Boards / JEE / NEET / Improve / Exploring)
4. Weak subjects (multi-select)
5. Learning style (visual / quizzes / explanations / interactive / balanced)

Grade can be changed later in Profile → re-locks syllabus.

### Plans
| Plan | Price | Key Limits |
|------|-------|------------|
| **Free** | ₹0/mo | 10 AI msgs/day · 1 mock/week · 3 quizzes/day · GPT-4o-mini · top-10 leaderboard · basic analytics |
| **Pro** ★ Most Popular | ₹299/mo (or ₹2,870/yr) | Unlimited chat · 5 mocks/week · Adaptive quizzes · GPT-4o · Full leaderboard · Deep analytics · AI memory |
| **Elite** ☆ Premium | ₹799/mo (or ₹7,670/yr) | Everything in Pro + Unlimited mocks · Exam countdown · Priority queue · Performance prediction |

Yearly billing = **20% off**.

### Backend Gates (all server-enforced — frontend can't bypass)
- `chat.py` — daily AI message limit + grade-lock on session create + model swap (Free→4o-mini, Pro/Elite→4o)
- `mock_exam.py` — weekly mock limit + grade-lock + `adaptive_quizzes` feature gate on `/followup-quiz`
- `quiz.py` — daily quiz limit + grade-lock
- `social.py` — leaderboard truncated to top 10 for Free users
- Returns HTTP 429 (limit) or 402 (premium feature) with structured `detail` payload for frontend modal

### Usage Tracking
- `db.usage_counters` per user with `ai_messages_by_day`, `quizzes_by_day`, `mocks_by_week` (counter dicts auto-rotating by date)
- Live counters returned from `GET /api/subscription/me`

### New API Endpoints
- `GET /api/subscription/plans` — public plan catalog
- `GET /api/subscription/me` — current plan + limits + live usage
- `POST /api/subscription/subscribe` — **mocked Razorpay** (architecture ready)
- `POST /api/subscription/cancel`
- `GET /api/onboarding/status`
- `POST /api/onboarding/submit`
- `PUT /api/users/grade` — change grade (re-locks syllabus)

### Frontend Components
- `SubscriptionContext` — `plan`, `usage`, `hasFeature()`, `triggerUpgrade()` — wraps the app
- `OnboardingModal` — 5-step gradient modal, blocks unauthed app access
- `PricingPage` (`/upgrade`) — 3 plan cards with gradient glows, badge animations, monthly/yearly toggle with "SAVE 20%" sticker, celebratory upgrade success overlay
- `UpgradePromptModal` — appears on 429/402 errors, deep links to pricing
- `Sidebar` — animated **"Upgrade to Pro ₹299"** CTA for free users, **"Pro Active"** crown for paid users
- `SyllabusPage` — class selector removed; locked to `user.class_level`
- `ChatPage` — handles 429 limit → triggers upgrade modal, refreshes usage on send

## Phase 3 — NCERT Curriculum Engine
- 25 NCERT books scraped (classes 6–12, English-medium)
- 216/294 chapters with **real verified titles** (Class 10 Math: "Real Numbers", "Polynomials"... — exact NCERT names)
- "NCERT ✓" verification badge on syllabus UI
- AI tutor receives chapter manifest in system prompt → grounded against hallucination
- PDFs kept server-side only for AI reference (not exposed to users)

## Phase 1+2 — Earlier
JWT/Google auth, IntroScreen, Dashboard, AI Chat (streaming, [YOUTUBE] + [QUIZ] + Next-Step tags), QuizArena, Profile, Leaderboard (Global/Class/Friends scopes), Mock Exams + Adaptive follow-up, Study Plan, Referrals, Daily Missions, Streak Reminders.

## Testing
- **30/31 pytest backend tests pass** (regression intact post-Phase 4)
- Fixtures updated to register with class_level + auto-onboard + auto-upgrade to Pro for tests that need premium features
- 1 failing test (streak admin) is pre-existing, unrelated to Phase 4

## Prioritized Backlog

### P1 (Next)
- Real Razorpay integration (drop-in replacement for mocked `/subscribe` endpoint)
- Replace last 78 generic "Chapter N" titles by parsing each chapter PDF's page 1
- RAG: vector-index NCERT PDFs and cite real textbook passages
- Add Class 11/12 Science (Physics/Chemistry/Biology) + Computer Science to `ncert_books.json`
- Real YouTube Data API v3 integration

### P2
- Hindi-medium support, parent/teacher dashboards, Whisper voice input, PWA offline mode

## Environment
- `OPENAI_API_KEY`, `JWT_SECRET`, `MONGO_URL`, `DB_NAME`, `FRONTEND_URL` in `backend/.env`
- `REACT_APP_BACKEND_URL` in `frontend/.env`
