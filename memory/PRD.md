# NeuraLearn - AI-Powered CBSE Learning Platform

## Overview
A production-level full-stack AI-powered CBSE learning platform combining ChatGPT + Duolingo + Khan Academy aesthetics with immersive educational AI tutoring.

## Architecture
- **Frontend**: React 18 + TailwindCSS + Framer Motion + Three.js + GSAP
- **Backend**: FastAPI + Motor (MongoDB async)
- **AI**: OpenAI GPT-4o (user's own key) via streaming SSE
- **DB**: MongoDB (test_database)
- **Auth**: JWT (email/password) + Emergent Google OAuth

## What's Been Implemented (May 2026)

### Backend (server.py + cbse_data.py)
- JWT auth: register, login, logout, me, refresh
- Google OAuth: session exchange, logout
- AI Chat: session CRUD + streaming GPT-4o responses (SSE)
- CBSE Syllabus API: Classes 6-12, all subjects, full chapter lists
- Progress tracking: per-chapter mastery tracking
- Quiz system: AI-generated MCQs, submission + scoring
- Gamification: XP, levels, streaks, achievements, daily challenge
- Admin seeding on startup

### Frontend Components
- **IntroScreen**: Three.js particle system + GSAP timeline + Framer Motion
- **AuthPage**: JWT login/register + Google OAuth button
- **AuthCallback**: Emergent OAuth session exchange
- **Layout + Sidebar**: Animated navigation with XP bar, streak
- **Dashboard**: Stats cards, daily challenge, recent sessions
- **ChatPage**: Streaming AI chat, quiz card parsing, markdown rendering
- **SyllabusPage**: Class → Subject → Chapter browser
- **ProgressPage**: Mastery bars + Recharts pie chart
- **QuizArena**: AI quiz generation + MCQ interface + results
- **ProfilePage**: User profile, class selector, achievements

### CBSE Syllabus Coverage
- Classes 6, 7, 8: Math, Science, English, Social Science
- Classes 9, 10: Math, Science, English, Social Science, Computer Science
- Classes 11, 12: Physics, Chemistry, Biology, Mathematics, Computer Science
- Each subject has 10-16 chapters with lesson subtopics

## Prioritized Backlog

### P0 (Next immediate)
- [ ] Fix ChatPage: Handle state from SyllabusPage navigation (pre-fill chapter)
- [ ] Progress auto-update after each chat session
- [ ] Flashcard mode for chapters

### P1 (Next phase)
- [ ] Revision mode (AI-generated revision summaries)
- [ ] Weak topics detection from chat analysis
- [ ] Daily streak email reminders
- [ ] Social sharing of achievements

### P2 (Future)
- [ ] Multi-language support (Hindi medium)
- [ ] Parent dashboard
- [ ] School/teacher admin panel
- [ ] Offline mode / PWA
- [ ] Voice input for chat

## Environment
- OPENAI_API_KEY: User-provided GPT-4o key
- JWT_SECRET: Set in backend/.env
- DB_NAME: test_database (MongoDB)
