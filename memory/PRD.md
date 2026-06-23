# AceIt AI — Product Requirements Document

## Original Problem Statement
Build "AceIt AI" (formerly NeuraLearn), a production-level full-stack AI-powered CBSE learning platform. Personalized AI tutor, gamification (streaks, leaderboards), advanced mock exams, visual learning (YouTube), study plans, NCERT-verified syllabus.

Hidden full form: "Always Crush Exams" — never to be displayed in the UI.

## Tech Stack
- **Frontend**: React 18, TailwindCSS, Framer Motion, KaTeX (math), Recharts, Lucide React
- **Backend**: FastAPI (Python), MongoDB (Motor async), JWT auth
- **AI**: OpenAI GPT-4o / GPT-4o-mini
- **Auth**: JWT + Emergent-managed Google OAuth + Email Verification (Resend)
- **Payments**: Razorpay (backend mocked gracefully if no key)
- **Email**: Resend (configured, sandbox mode — verify domain at resend.com/domains for production)

## Color Scheme
Royal Red/Blue/Gold — #dc2626 (red), #2563eb (blue), #fbbf24 (gold)

## What's Been Implemented

### Phase 1 — Core Platform
- [x] React frontend + FastAPI backend + MongoDB
- [x] JWT authentication + Emergent Google Auth
- [x] AI Chat with streaming (OpenAI GPT-4o)
- [x] NCERT verified syllabus scraper (curriculum_engine.py)
- [x] Quiz generation (15 credits)
- [x] Mock exam system (30 credits)
- [x] Study plans, Leaderboards, Streak system
- [x] Gamification: XP, levels, achievements

### Phase 2 — Gamification & UX
- [x] 5-step Onboarding flow
- [x] Grade Access Control (class-level locking)
- [x] Credit System (auto-deduction)
- [x] Subscription plans (Free, Starter, Pro, Elite)
- [x] Pricing/Upgrade page
- [x] Razorpay backend mock fallback

### Phase 3 — AceIt AI Rebrand + Question Bank (2026-06-13)
- [x] App renamed to "AceIt AI" everywhere
- [x] Question Bank: Auto-builds Q&A pairs from NCERT PDFs (gpt-4o-mini)
  - 20 Q&A pairs per chapter, stored in MongoDB question_bank collection
  - Semantic KB lookup on every chat message (cheap rephrase vs full generation)
- [x] Variable credit cost for chat (1 credit per 100 words, min 1)
- [x] No daily message limit for AI tutor
- [x] Quiz: 15 credits, Mock exam: 30 credits
- [x] Chapter names only (no chapter numbers in UI)
- [x] CBSE data fallback for generic chapter names
- [x] Remove gradient blur on app names
- [x] Fixed duplicate "starter" plan in subscription API
- [x] Fixed critical login loop (undefined ensure_indexes)

### Phase 4 — 10 Major Features (2026-06-14)
- [x] **Global Branding**: AceIt AI everywhere (all components, all pages)
- [x] **Email Verification**: Full system with Resend, 24-hour expiry, resend option
  - POST /api/auth/register → requires_verification=True
  - GET /api/auth/verify-email?token=... → verify token
  - POST /api/auth/resend-verification → resend link
  - POST /api/auth/admin/verify-user → admin manual verify
  - Google OAuth users auto-verified
  - Existing users backfilled as verified on startup
  - NOTE: Resend in sandbox mode — verify domain at resend.com/domains for production
- [x] **NCERT Title Fix**: _is_corrupt_title() detects all corrupt patterns
  - "Question Answer in Hindi" → replaced with cbse_data.py correct names
  - Class 6/7/8 Science now shows correct chapter titles
  - No "Chapter N" placeholders shown
- [x] **Credit System Redesign**: Dynamic 2-10 credits (word-count tiers)
  - 0-250 words: 2 credits | 251-500: 4 | 501-800: 6 | 801-1200: 8 | 1201+: 10
  - Real-time balance shown in toast with actual word count
  - credit_analytics collection tracks all deductions
- [x] **Response Length**: 1500 words max, never truncated mid-sentence
  - 2200 tokens = ~1500 words + completion buffer
  - Soft cap warning injected, stream continues to finish sentence
- [x] **KaTeX Math Rendering**: MathRenderer.jsx component
  - Inline math: $formula$, Block math: $$formula$$
  - Integrated into ChatPage MessageBubble, QuizModal
- [x] **Adaptive Learning Engine**: Comprehensive expansion
  - Topic mastery (EMA), quiz history (50 entries), concept-level tracking
  - Difficulty auto-adjustment (easy/medium/hard)
  - Learning pace (slow/normal/fast), preferred style (step-by-step/examples/brief/visual)
  - Persists in student_profiles MongoDB collection
  - Quiz results feed into adaptive engine
- [x] **Interactive Quiz Modal**: InteractiveQuizModal.jsx
  - Auto-triggers when user says "quiz me", "test me", "give me a quiz", etc.
  - Supports: MCQ, True/False, Fill-in-blank, Short answer
  - Scores automatically, shows per-question explanations
  - Results feed into adaptive engine
- [x] **Analytics**: credit_analytics collection tracks all credit events
- [x] Fixed duplicate starter plan in subscription API
- [x] Fixed QuizSubmitRequest model (quiz_id removed from body, path param only)
- [x] QuizGenerateRequest topic/chapter made optional

## Architecture

```
/app/
├── backend/
│   ├── server.py              # FastAPI entrypoint
│   ├── core.py                # DB, logger, JWT helpers
│   ├── models.py              # Pydantic models
│   ├── plan_gates.py          # Subscription gating logic
│   ├── credits.py             # Dynamic credit system (2-10 tiers)
│   ├── curriculum_engine.py   # NCERT syllabus + corrupt title fix
│   ├── adaptive_engine.py     # Student profiling + mastery tracking
│   ├── knowledge_base.py      # Question bank semantic lookup
│   ├── email_service.py       # Resend transactional emails
│   ├── cbse_data.py           # Static CBSE chapter names fallback
│   └── routes/
│       ├── auth.py            # JWT + Google + Email verification
│       ├── chat.py            # AI chat (KB lookup, 1500w, adaptive)
│       ├── quiz.py            # 15 credits + adaptive engine feed
│       ├── mock_exam.py       # 30 credits
│       ├── syllabus.py        # Chapter names API
│       ├── question_bank.py   # /api/question-bank/* endpoints
│       ├── social.py          # Leaderboards
│       ├── subscription.py    # Pricing + Razorpay
│       └── study_plan.py
├── frontend/
│   └── src/
│       ├── App.js             # + /verify-email route
│       ├── contexts/
│       │   ├── AuthContext.js
│       │   ├── SubscriptionContext.jsx
│       │   └── CreditsContext.jsx
│       └── components/
│           ├── IntroScreen.jsx
│           ├── Sidebar.jsx
│           ├── AuthPage.jsx          # Email verification pending state
│           ├── EmailVerificationPage.jsx  # NEW
│           ├── ChatPage.jsx          # KaTeX, QuizModal, adaptive credits
│           ├── SyllabusPage.jsx      # Chapter names only
│           ├── PricingPage.jsx       # top performer in gold
│           ├── MathRenderer.jsx      # NEW - KaTeX
│           ├── InteractiveQuizModal.jsx   # NEW - quiz UI
│           ├── ProfilePage.jsx
│           ├── OnboardingModal.jsx
│           ├── LeaderboardPage.jsx
│           ├── QuizArena.jsx
│           ├── MockExamPage.jsx
│           ├── StudyPlanPage.jsx
│           ├── GradeAccessGuard.jsx
│           └── CreditBadge.jsx
└── memory/
    ├── test_credentials.md
    └── PRD.md
```

## Credit System
- AI Chat: Dynamic 2-10 credits (tiers by word count)
- Quiz Generation: 15 credits
- Mock Exam: 30 credits
- Tracked in credit_analytics collection

## Key API Endpoints
- `POST /api/auth/register` → returns requires_verification:true
- `GET /api/auth/verify-email?token=...` → verify email
- `POST /api/auth/resend-verification` → resend link
- `POST /api/auth/admin/verify-user` → admin manual verify
- `GET /api/auth/me`
- `GET /api/syllabus/{class_id}/{subject}/chapters`
- `POST /api/chat/{session_id}/message` — streaming, adaptive, KB-assisted
- `POST /api/quiz/generate` — 15 credits
- `POST /api/quiz/{quiz_id}/submit` — updates adaptive engine
- `POST /api/mock-exam/generate` — 30 credits
- `GET /api/question-bank/stats`
- `POST /api/question-bank/build` — admin only
- `GET /api/subscription/plans`
- `GET /api/credits`

## DB Collections
- `users`: auth, credits, plan, class_level, is_verified, verification_token
- `subscriptions`: plan, billing_cycle, expires_at
- `chat_sessions`, `messages`
- `question_bank`: Q&A pairs from NCERT PDFs
- `student_profiles`: adaptive learning data (mastery, difficulty, style, quiz_history)
- `credit_analytics`: per-credit-event tracking
- `curriculum`: NCERT verified chapters

## Known Limitations / Next Steps
- Resend sandbox mode: verify domain at resend.com/domains for full email delivery
- P1: Notification system (sonner toasts)
- P1: Resume Razorpay frontend payment flow
- P2: Admin analytics dashboard
- P2: Subscription Management UI in Profile
- P2: More NCERT content (Class 11/12 Science, CS)
