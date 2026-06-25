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

### Bug Fix: StudyPlanPage Variable Collision
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
