# AceIt AI — Product Requirements Document

## Original Problem Statement
Build "AceIt AI" (formerly NeuraLearn), a complete production-level full-stack AI-powered CBSE learning platform for Classes 6–12. Features include an interactive personalized AI tutor, gamification (XP/levels/streaks), advanced mock exams, visual learning with KaTeX math rendering, and an NCERT-verified syllabus. The platform must have production-grade security, email verification, and a credit-based AI usage system.

Enforced BNPS curriculum, KaTeX math rendering, Admin dashboard (3 hardcoded emails), no email-verification blocker on signup, password strength rules, Grades 7/8/9 only (7 & 9 = Coming Soon), forced school selection for legacy users, browser password saving on auth forms.

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

### Phase 6: Admin, Auth & Curriculum Improvements (Complete — June 2026)
- **No-verification Signup**: Users can register and log in immediately; welcome email sent via Resend
- **Password Requirements**: Min 6 chars + at least 1 special character (enforced backend + frontend)
- **Admin Accounts**: samanvayrakesh7@gmail.com and truecursemahito28@gmail.com get admin role automatically
- **Admin Dashboard** (`/admin`): Earnings (total users, MRR, plan distribution, payments), Leaderboard management (hide/show users), Grade change requests (approve/deny)
- **Admin Sidebar Link**: ShieldCheck icon appears in sidebar for admin emails only
- **Leaderboard**: Filters out `hide_from_leaderboard: true` users
- **BNPS PDF URLs**: All chapters in `school_curriculum.py` now include direct NCERT PDF URLs
- **Grade Change Tracking**: PUT /users/class creates an audit record in grade_change_requests collection
- **KaTeX Math Rendering**: Installed `remark-math` + `rehype-katex`; `ChatPage.jsx` ReactMarkdown now uses native math plugins. No more raw LaTeX strings.
- **Global KaTeX CSS**: `import 'katex/dist/katex.min.css'` added to `App.js`
- **Brooklyn National Public School (BNPS)**: Full Grade 8 curriculum integration
  - 4 subjects: Mathematics (16ch), Science (13ch), Social Studies (7ch), English (13ch)
  - School selector on AuthPage
  - BNPS subjects/chapters served from `school_curriculum.py`
  - Syllabus shows "BNPS" badge instead of "NCERT" for school students
- **BNPS PDF Download**: Script downloads NCERT 2024-25 textbooks (Ganita Prakash, Curiosity, Exploring Society, Poorvi) — 31 PDFs
- **BNPS Question Bank**: 988 Q&A pairs covering all 49 BNPS chapters (built via `/api/question-bank/build-bnps`)
- **School Context in AI**: Quiz and Mock Exam generation prompts include BNPS chapter list for school students
- **BNPS Subtopics**: All 49 BNPS chapters have curated subtopics in quiz.py
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

## Admin Endpoints (Phase 6)
- `GET  /api/admin/earnings`
- `GET  /api/admin/leaderboard/users`
- `POST /api/admin/leaderboard/hide/{user_id}`
- `GET  /api/admin/grade-requests`
- `POST /api/admin/grade-requests/{id}/resolve`
- `GET  /api/admin/users`

## Prioritized Backlog

### P1 — Next Up
- Phase 9: Friends system (send/accept/remove) + friend leaderboard + real-time rankings

### P2 — Upcoming
- Notification system (streak warnings, grade change toasts)
- Password reset flow

### Code Quality Hardening (Complete — June 2026)
- **XSS Fix**: `IntroScreen.jsx` — replaced `outerHTML` DOM injection with React state (`imgError`) for safe fallback rendering
- **Subprocess Fix**: `curriculum.py` — replaced hardcoded `"python"` with `sys.executable` for correct interpreter
- **Silent Error Logging**: Added `console.warn` to all empty `catch {}` blocks across `AuthContext.js`, `CreditsContext.jsx`, `SubscriptionContext.jsx`, `StudyPlanPage.jsx`, `ProfilePage.jsx`
- **Stable React Keys**: Replaced `key={i}` index keys with semantic stable keys:
  - `ChatPage.jsx`: `key={msg.timestamp || i}` for message list
  - `QuizArena.jsx`: `key={opt}` for options, `key={r.question?.slice(0,40) || i}` for results
  - `ProgressPage.jsx`: `key={entry.name}` for pie chart cells
  - `StudyPlanPage.jsx`: `key={tip}`, `key={week.week}`, `key={task.day-j}` for plan items
- **Dashboard UX**: Added `truncate max-w-[220px]` to greeting h1 preventing overflow on long names

- Phase 6: Quiz Arena — chapter selection, adaptive difficulty auto-set
- Phase 7: Mock exam weak-area persistence, weak-area tracker UI
- Phase 8: Study Plan personalised from quiz history + exam weak areas + time availability
- Phase 10: ProfilePage subscription management (plan, credits, upgrade, cancel)

### P3 — Future
- Email domain verification at resend.com/domains
- Redis-backed rate limiting for multi-instance
- Phase 9: Friends & Social system (send/accept/remove friends, friend leaderboard, global/weekly/monthly rankings)
- Duolingo-style Chat mastery progress (complete lessons to reach 100% mastery)
- Daily Study Reminder Email (user-configurable time, email nudge with next task)

## Completed (July 2026 — Session 2)
- [x] Fixed tutorial "Get Started" button not closing — state initialized as `shouldShowTutorial()` so close triggers re-render
- [x] First quiz FREE — checks `past_quiz_count` before deducting 15 credits; new users pay nothing for first quiz
- [x] Bonus credits on quiz completion — +1 to +5 credits awarded based on correct answers (so completing quizzes earns credits back)
- [x] Tutorial text updated to accurately reflect actual credit costs and the bonus credits system


- [x] Fixed P0 account wipe bug: Disabled `_cleanup_unverified_accounts()` background task in `server.py`
- [x] Rebuilt BNPS Question Bank: 1,385 Q&A pairs (Math: 619, Science: 518, Social Science: 248). Created `metadata.json`, cleaned up English/Social Studies entries, ran full rebuild.
- [x] 5-step New User Tutorial: Created `NewUserTutorial.jsx` — shown on first login via localStorage flag (`aceit_tutorial_seen`). Steps: Welcome → Credits → AI Tutor → Quiz Arena → Mock Exams.
- [x] AI Tutor "New Chat" button: Now clears localStorage session + resets state to show session setup. "Go Back" uses `nav(-1)`.
- [x] Explicit content filter + curriculum constraint: System prompt updated in `chat.py` to reject off-topic/explicit questions and restrict AI to selected chapter scope.

## Completed (July 2026)
- [x] Grade 8 curriculum final: Science (hecu1, 13 chs), Math (hegp1+hegp2, 16 chs, 13 PDFs), Social Science (hees1, 7 chs). English DELETED. Grade 7/9 removed from cbse_data.py.
- [x] ncert_ai_metadata.json rebuilt with correct BNPS chapter names
- [x] school_curriculum.py: "Social Studies" renamed to "Social Science", English removed
- [x] Mobile sidebar now auto-closes when any nav item is tapped
- [x] Quiz MCQ selected option now highlights cyan (not red) in InteractiveQuizModal
- [x] Intro screen subjects reduced to: Mathematics, Science, English, Social Science
- [x] Removed "Classes 6-12" / "CBSE Class 6-12" references; replaced with "BNPS Curriculum" / "exam prep tutor"
- [x] Credit costs halved: chat 1-5cr (was 2-10), quiz 8cr (was 15), mock exam 15cr (was 30)
- [x] State persistence: ChatPage, QuizArena, MockExamPage all save to localStorage and resume on navigation
