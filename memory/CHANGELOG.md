# AceIt AI — Changelog

## June 2026

### Email Verification System (Production-Grade)
- SHA-256 token hashing; tokens cleared after use
- Email quality validation: format + 120 disposable domains + DNS MX lookup  
- Login gate: unverified JWT users blocked with exact spec messages
- 60s resend cooldown stored in DB + countdown UI
- Per-IP rate limiting (in-memory; 5/hr register, 10/hr login, 3/hr resend)
- 48h account cleanup via background asyncio task
- New DB fields: email_verified, status, verified_at, resend_cooldown_until
- Google users auto-verified; admin always verified
- Removed Emergent badge from index.html

### Phased Improvements — Phases 1–5
**Phase 1 — Critical Bug Fixes**
- AI response truncation fixed: max_tokens B=800, C=1800 (was 200/500)
- Quiz topic bug fixed: openQuizModal now uses session.chapter (not raw text)
- Quiz scoring fixed: backend is_correct normalized to correct in frontend
- Suggestions auto-send: clicking sends message immediately (no extra click)
- Leaderboard fake data removed: admin + test_*@neuralearn.ai filtered
- ChatPage: "Starting your session" → "Session Started" with icon

**Phase 2 — Subscription**
- Study Plan locked for free users: "Upgrade your plan to access Study Plans."
- StudyPlanPage uses useSubscription context; shows upgrade CTA to /pricing

**Phase 4 — UX Improvements**
- Syllabus chapters view: Back button added (data-testid=back-to-subjects-btn)

**Phase 5 — Progress System Enhanced**
- Streak cards: current streak + longest streak with fire icon
- Quiz performance history: bar chart of last 8 quizzes via /api/quiz/history
- Accuracy stat: avg quiz score shown as core metric
- Milestones section: 8 milestones tracking sessions, quizzes, streak, XP
- Weak topics section retained

### School Selection & BNPS Curriculum (June 2026)
- **New file**: `backend/school_curriculum.py` — BNPS Grade 8 chapters (Science 13, Maths 16, Social Studies 7, English 13) + SCHOOL_LIST + helpers
- **Signup**: School selector added to register tab — "Brooklyn National Public School" (active) + "National Public School" (Coming Soon, disabled) — amber warning on selection; form validates school before submit
- **Backend auth**: `GET /api/auth/schools` public endpoint; `school` field stored in users collection on register
- **Syllabus**: Subjects + chapters endpoints now school-aware — BNPS Grade 8 students see school-specific chapters instead of NCERT
- **AI tutor**: English chapters get context hint (literary analysis for stories/poems)
- **ProfilePage**: Shows school name + "To change school, contact admin" note
- **server.py**: Idempotent BNPS test student seed (`bnps@student.edu / Test@12345`) on startup
- **Duolingo mastery feature**: DECLINED — too complex for <100 Emergent credits as per user's own rule

- **MathRenderer**: Added `preprocessMath()` to convert AI's `( \frac{0}{b} )` → `$\frac{0}{b}$` before parsing; added `isLaTeXContent()` check to prevent `$10…$4` currency strings being parsed as math
- **System prompt**: Added explicit rule — NEVER write `( \formula )` pattern; NEVER use `$` for currency; always use `$...$` or Unicode
- **Sidebar**: Changed "Upgrade to Pro ₹299" → "Upgrade to Starter ₹399"
- **Starter plan features**: Reduced to 7 highlights (removed "5 mock exams/week", "Everything in Free", "Priority support")
- **Pro plan features**: Reduced to 6 clean highlights
- **Quiz Arena**: Removed free-text topic input; replaced with subtopic SELECT dropdown populated from new `GET /api/quiz/subtopics` endpoint; subtopics auto-loaded on chapter change; covers 50+ CBSE chapters across Maths/Science/9-12
- **StudyPlanPage**: Already has Starter nav fix and correct gate title from previous batch

- **AI response cutoff**: `ai_router.py` token limits increased (B: 800→2000, C: 1800→3500); removed mid-stream word-limit injection from `chat.py`; `generation_tokens` now uses max_tokens directly with no artificial cap
- **Math symbols**: System prompt updated — Unicode symbols preferred (½ ¼ π √ ²) over raw LaTeX `\frac{}{}`; LaTeX only for complex multi-line equations
- **Subscription plans (2 plans)**: Starter (500cr, ₹399) and Pro (1000cr, ₹699) — `plan_gates.py` updated with new features; `credits.py` Pro credits 1500→1000; PricingPage filters to show only Starter+Pro; subscription.py fixed to accept 'starter' plan
- **Study plan navigation**: `StudyPlanPage` nav('/pricing') → nav('/upgrade'); gate title updated to "Starter"
- **Credits toast mismatch**: `CreditsContext.jsx` ROUTE_COST quiz 5→15, mock 30 (was 10)
- **Bug caught by testing agent**: `subscription.py` create-order/subscribe/verify-payment only accepted 'pro'/'elite' — fixed to include 'starter'; bonus_credits map updated

- **Root cause**: Backend generated quiz questions without `type` field; InteractiveQuizModal only renders options when `type === 'mcq'` → no options shown
- **Backend fix**: Added `"type": "mcq"` to prompt + server-side normalization (if no type but options exist → type=mcq)
- **Frontend fix**: Added `qType` inference (`question?.type || (options?.length ? 'mcq' : 'short_answer')`) in InteractiveQuizModal; all `question?.type ===` checks now use `qType`
- **Next button fix**: `canAdvance` now correctly uses `qType` for fill_blank check → enabled after selecting MCQ option
- **AI validation in chat**: `onComplete` in ChatPage now sends quiz results as a chat message → AI responds with per-question explanations of wrong answers
- **Results modal simplified**: removed per-question breakdown from modal; shows just score + "AI Tutor is reviewing" spinner + "Back to Chat" button
- **Fallback onComplete fix**: fallback (offline scoring) now passes full `results` array to `onComplete`

- XSS fix: IntroScreen.jsx outerHTML → React imgError state
- subprocess fix: curriculum.py uses sys.executable
- Silent catch blocks replaced with console.warn in 5 files
- Stable React keys in ChatPage, QuizArena, ProgressPage, StudyPlanPage
- Dashboard greeting truncation (truncate + max-w classes)

- Fixed: `plan` declared twice (useSubscription + existingPlan?.plan)
- Renamed inner var to `studyPlan` — prevented app compilation crash

### Earlier Features (from previous sessions)
- AceIt AI global branding
- Background Question Bank Builder (PyMuPDF PDF → Q&A)  
- Adaptive Learning Engine (tracks weak/strong topics, pace, accuracy)
- Dynamic Credit System (2–10 credits scaled by word count)
- KaTeX Math Rendering (MathRenderer.jsx)
- Interactive Quiz Modal (InteractiveQuizModal.jsx)
- Analytics endpoint
- Resend email integration (onboarding@resend.dev sender)
