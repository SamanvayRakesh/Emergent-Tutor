# AceIt AI — Product Requirements Document

## Original Problem Statement
Build "AceIt AI" (formerly NeuraLearn), a complete production-level full-stack AI-powered CBSE learning platform. The product is a highly interactive, personalized AI tutor with gamification (streaks, leaderboards), advanced mock exams, visual learning (YouTube), study plans, and an NCERT-verified syllabus.

## Hidden Full Form
"Always Crush Exams" — never to be mentioned anywhere in the UI.

## Tech Stack
- **Frontend**: React 18, TailwindCSS, Framer Motion, Recharts, Lucide React
- **Backend**: FastAPI (Python), MongoDB (Motor async), JWT auth
- **AI**: OpenAI GPT-4o / GPT-4o-mini (emergentintegrations)
- **Auth**: JWT + Emergent-managed Google OAuth
- **Payments**: Razorpay (backend mocked gracefully if no key)

## Color Scheme
Royal Red/Blue/Gold — #dc2626 (red), #2563eb (blue), #fbbf24 (gold)

## What's Been Implemented (Completed Features)

### Phase 1 — Core Platform
- [x] React frontend + FastAPI backend + MongoDB
- [x] JWT authentication + Emergent Google Auth
- [x] AI Chat with streaming (OpenAI GPT-4o)
- [x] NCERT verified syllabus scraper (curriculum_engine.py)
- [x] Adaptive learning engine (student profiles, memory)
- [x] Quiz generation (15 credits)
- [x] Mock exam system (30 credits)
- [x] Study plans
- [x] Leaderboards & social features
- [x] Streak system

### Phase 2 — Gamification & UX
- [x] 5-step Onboarding flow
- [x] Grade Access Control (class-level locking)
- [x] Credit System (CreditBadge.jsx, auto-deduction)
- [x] Subscription plans (Free, Starter, Pro, Elite)
- [x] Pricing/Upgrade page
- [x] Profile page
- [x] Razorpay backend mock fallback

### Phase 3 — AceIt AI Rebrand + Question Bank (2026-06-13)
- [x] App renamed to "AceIt AI" everywhere (frontend + backend)
- [x] Question Bank: Auto-builds Q&A pairs from NCERT PDFs
  - 20 Q&A pairs per chapter via LLM (gpt-4o-mini)
  - Stored in MongoDB question_bank collection
  - knowledge_base.py does semantic lookup on user questions
  - On KB hit: ultra-cheap rephrase (~130 tokens)
  - On KB miss: full generation with adaptive context
- [x] Variable credit cost for chat (1 credit per 100 words, min 1)
- [x] 1000-word soft cap on AI responses (warning injected)
- [x] No daily message limit for AI tutor
- [x] Quiz cost: 15 credits (was 8)
- [x] Mock exam cost: 30 credits (was 25)
- [x] Chapter names only — no "Chapter N" numbers shown anywhere in UI
- [x] cbse_data.py fallback for generic "Chapter N" NCERT titles
- [x] Remove gradient blur on app name in IntroScreen, Sidebar, AuthPage
- [x] "top performer" text in PricingPage is now solid gold (no gradient)
- [x] Fixed duplicate "starter" plan in subscription API
- [x] Fixed critical login loop (undefined ensure_indexes() removed from server.py)

## Architecture

```
/app/
├── backend/
│   ├── server.py              # FastAPI entrypoint (mounts all routers)
│   ├── core.py                # DB, logger, JWT helpers
│   ├── models.py              # Pydantic models
│   ├── plan_gates.py          # Subscription gating logic
│   ├── credits.py             # Credit system (variable chat cost)
│   ├── curriculum_engine.py   # NCERT verified syllabus (with cbse_data fallback)
│   ├── knowledge_base.py      # Question bank semantic lookup
│   ├── cbse_data.py           # Static CBSE chapter names (fallback)
│   ├── adaptive_engine.py     # Student profiling
│   ├── scripts/
│   │   ├── ncert_scraper.py   # PDF downloader
│   │   └── build_question_bank.py
│   └── routes/
│       ├── auth.py
│       ├── chat.py            # AI chat with KB lookup + variable credits
│       ├── quiz.py            # 15 credits
│       ├── mock_exam.py       # 30 credits
│       ├── syllabus.py        # Chapter names API (no numbers)
│       ├── question_bank.py   # /api/question-bank/* endpoints
│       ├── social.py          # Leaderboards
│       ├── study_plan.py
│       ├── subscription.py    # Pricing + Razorpay
│       └── curriculum.py
├── frontend/
│   └── src/
│       ├── App.js
│       ├── contexts/
│       │   ├── AuthContext.js
│       │   ├── SubscriptionContext.jsx
│       │   └── CreditsContext.jsx
│       └── components/
│           ├── IntroScreen.jsx
│           ├── Sidebar.jsx
│           ├── AuthPage.jsx
│           ├── ChatPage.jsx
│           ├── SyllabusPage.jsx     # Chapter names only (no numbers)
│           ├── PricingPage.jsx      # top performer in gold
│           ├── ProfilePage.jsx
│           ├── OnboardingModal.jsx
│           ├── LeaderboardPage.jsx
│           ├── QuizPage.jsx
│           ├── MockExamPage.jsx
│           ├── StudyPlanPage.jsx
│           ├── GradeAccessGuard.jsx
│           └── CreditBadge.jsx
└── memory/
    ├── test_credentials.md
    └── PRD.md
```

## Key DB Schema
- `users`: `{user_id, email, password_hash, name, class_level, xp, credits, plan, is_onboarded, grade_last_changed}`
- `subscriptions`: `{user_id, plan, billing_cycle, expires_at}`
- `chat_sessions`: `{session_id, user_id, class_level, subject, chapter, messages}`
- `question_bank`: `{class_level, subject, chapter_no, chapter_title, question, answer, topic, difficulty, hit_count, created_at}`
- `curriculum`: `{class_level, subject, chapters[{id, name, order, chapter_no, book_title}]}`

## Key API Endpoints
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/auth/register`
- `GET /api/syllabus/{class_id}/{subject}/chapters`
- `POST /api/chat/{session_id}/message` — streaming chat
- `POST /api/quiz/generate` — 15 credits
- `POST /api/mock-exam/generate` — 30 credits
- `GET /api/question-bank/stats`
- `POST /api/question-bank/build` — admin only
- `GET /api/subscription/plans`
- `GET /api/credits`

## Credit System
- AI Chat: 1 credit per 100 words generated (min 1, soft cap 1000 words)
- Quiz Generation: 15 credits
- Mock Exam: 30 credits
- Free plan: 100 credits on signup

## Backlog / Future Tasks
- P1: Notification system (sonner toasts for streak, grade change, quiz done)
- P1: Razorpay frontend payment flow (resume when user requests)
- P2: Subscription Management Profile UI (view/upgrade plan from profile)
- P2: AI cost optimization (chapter summary caching)
- P2: Class 11/12 Science (Physics/Chem/Bio) + CS chapter expansion
- P2: Question bank search UI (show students related Q&A from bank)
