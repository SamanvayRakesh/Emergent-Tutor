# Ace-it update log

## upd 6.1 — Stable rollback baseline

Restored the Stop button snapshot. User confirmed the app worked after restoring syllabus.py. Previous upd 7 work was reverted.

## upd 6.2 — NIOS profile course labels

Date: 2026-10-07. One runtime file: frontend/src/components/ProfilePage.jsx. NIOS profile uses Course change, Secondary Course as current, Senior Secondary disabled and labelled Coming soon. NIOS does not fetch grade status/appeal endpoints or render grade controls and legacy appeal banners. Includes full NIOS school name. Brooklyn grade behavior preserved. No auth, backend, curriculum, or mastery change.

Validation: JSX parses; rendered NIOS profiles with legacy stored class levels 8, 9, 10 contain only course labels and a disabled Senior Secondary option; Brooklyn renders the original grade controls. Preview testing pending.

Progress rebuild: paused before any code changes. First intended step remains reliable completed quiz result saving.


## upd 8 — Visualize, step 1: Mind Map

Date: 2026-10-07. One independently testable format only. Adds Visualize beside the tutor prompt; Mind Map is available, other formats marked Coming soon. Existing chapter/school tutor context supplies structured JSON; the app draws an SVG, supports branch details and SVG download. No image generation, new npm packages, or new route imports. Existing credits, auth, streaming, stop, and message persistence paths remain. Map-specific response instructions bypass short KB rephrasing while honoring plan token ceilings; insufficient response budget returns a clear limit message.

Runtime files: frontend/src/components/ChatPage.jsx, frontend/src/components/MindMapCard.jsx (new), backend/routes/chat.py. Backup: pre-change ChatPage and backend chat route, plus baseline commit e9b2f10ad2682886edf9bfa7fd884add9bb0e23f. Undo restores those two existing files and deletes MindMapCard.jsx.

Validation: JSX/Python parsing; full frontend import graph build; renderer DOM tests for valid/invalid schema, branch interaction, SVG download and escaped unsafe text. Mounted FastAPI tests with disposable DB and mocked Google/AI providers for NIOS and Brooklyn: startup, signup/login, syllabus, mind-map SSE and persisted content, plan token budget refusal, normal tutor short KB path. No live AI/provider or deployed preview verification.

Source limitation: reuses existing tutor grounding. NIOS can retrieve PDF excerpts; other curricula may use metadata/hints. Whole-PDF extraction, shared source-version cache, PDF notes/cheat sheets, flowcharts, and numeric graphs are future steps. Progress rebuild remains paused. Await user test before next Visualize format.


## upd 8.1 — Flowcharts and improved mind maps

Date: 2026-10-08. Adds ordered process/timeline/worked-method Flowcharts with connected arrows, step explanations and SVG download. Mind maps retain the existing panel while adding summaries, relationship labels, key-fact previews and mouse/keyboard topic selection. Existing saved maps without new fields remain supported. Generation prompts prioritize requested focus, precise facts, distinct concepts and source-supported examples. Visual NIOS retrieval excludes format instructions from the search query and caches separate focuses separately. Existing plan limits, auth, normal tutoring and Stop path remain.

Runtime files: frontend/src/components/ChatPage.jsx, frontend/src/components/MindMapCard.jsx, frontend/src/components/FlowchartCard.jsx (new), backend/routes/chat.py. No npm dependencies or database migration. Backup baseline e976a76005a4f59f26d44e296a06514f81f30c84; restore three original runtime files and delete FlowchartCard.jsx to undo.

Validation: Python/JSX parsing and frontend import graph build; DOM tests for schema rejection, old mind-map support, relationship/detail rendering, diagram selection and SVG downloads. Mounted FastAPI tests with disposable DB and mocked Google/AI providers for NIOS/Brooklyn: both format instructions, streaming, saved response, insufficient budget guard and unchanged normal KB tutor path. No live AI generation or preview deployment verification. User should test factual relevance against actual PDFs. Flowcharts currently show ordered sequences, not branching decisions. Whole-PDF extraction, numeric graphs and PDF formats remain future steps. Await preview tests before next update.


## upd 8.2 — Tutor/Visualize expired-session recovery

Date: 2026-10-08. Screenshot showed Not authenticated for both visual formats. One runtime file: frontend/src/components/ChatPage.jsx. A tutor POST returning 401 now attempts the existing cookie refresh endpoint once and retries the identical request once. Requests that start generation/streaming or return other statuses are never automatically replayed. Credentials and Stop/abort signal are preserved. A fully expired session asks the user to sign in again; refresh-service failures report retry rather than falsely claiming sign-out. Failed expired-session optimistic messages are removed to avoid accumulating unsent requests.

Validation: isolated request tests for 401→refresh→200, refresh rejection, second 401, network/service failure and no retries for 200/402/429/500; frontend import graph build. Full mounted backend with disposable DB/mocked provider confirms expired access cookie returns 401 before any AI call, valid refresh cookie renews access, and a repeated visual request invokes AI once. No live preview or real Google-account verification. No backend auth/cookie changes. Backup baseline ae45559ac972fcf05452b1454414daf86f0d8279. Await preview test; do not add another format.


## upd 8.3 — Study flowcharts and connected mind maps (2026-10-08)

- Flowcharts now organize a chapter into a study path: main idea, concepts, examples/applications, and recap. Descriptive chapters are supported; arrows mean learning order, not invented causation.
- Visual requests use a dedicated source-grounded prompt instead of the normal tutor's refusal/Quick Check instructions. Active school and chapter sources remain scoped.
- Mind maps show grouped branches and visible subtopic cards with curved connectors. Existing map data, selection details, and SVG downloads remain supported.
- Runtime files: backend/routes/chat.py, frontend/src/components/MindMapCard.jsx, frontend/src/components/FlowchartCard.jsx. ChatPage.jsx stays at upd 8.2, including its session-refresh fix. No new packages, database changes, or backend modules.
- Validation: Python compile, JSX parsing, frontend import build, component/schema/download tests, rendered SVG inspection, and mocked-provider FastAPI checks for NIOS/Brooklyn passed. Live AI relevance remains a preview test; mocked tests do not prove generated facts.
- Backup baseline: 70b053d39bbbf24c05f9d515019f711d09193949. Test this update before adding another feature.


## upd 8.4 — Remaining Visualize formats (2026-10-08)

- Enabled Graph, PDF Cheat Sheet, Revision Notes, Key Points and Quick Revision in the existing tutor composer. Mind Map and Study Flowchart remain unchanged.
- New StudyVisualCard renders validated bar/line/scatter data with units, exact-values table, negative/zero handling and SVG download. Source data versus illustrative formula examples are labelled; descriptive topics without meaningful numeric data return an explanation instead of arbitrary graphs.
- Source-grounded structured notes cards include one-click multi-page A4 PDF downloads with Unicode symbols. PDF pages use browser canvas JPEGs (visible text is rasterized, not selectable); no new packages, AI calls or backend PDF endpoint.
- Existing school/source scope, authentication refresh, credit checks, streaming and Stop paths retained. New formats use the existing 1200-token visual budget cap and incomplete/malformed replies get readable fallbacks.
- Files: backend/routes/chat.py; frontend/src/components/ChatPage.jsx; new frontend/src/components/StudyVisualCard.jsx. No database or dependency changes.
- Checks: Python/JSX parse, frontend import graph build, component/schema/parser checks, unchanged session-refresh tests, mocked-provider mounted API checks for NIOS/Brooklyn, and real canvas four-page PDF generation plus rendered page inspection passed. Live model relevance/data accuracy requires preview testing.
- Backup baseline: f834db0196a680e2e31a36f44e144835ef34c229 (working upd 8.3). Restore backed-up runtime files and remove the new unreferenced card to roll back.



## upd 8.5 — Distinct study formats and complete chapter PDF sources (2026-10-08)

- Cheat sheets now request all important concepts from a complete chapter PDF and render as a cream two-column chapter reference, with a matching downloadable two-column A4 PDF.
- Revision notes explain ideas in expandable sequential sections; key points use prioritized numbered takeaways; quick revision asks recall questions with answers hidden until revealed. Existing data/schema and graph SVG exports remain compatible.
- The new study formats read local chapter PDFs directly instead of relying on a single 600-character search hit. NIOS uses only nios_syllabus/<subject>; BNPS uses only its grade/subject chapter PDFs. Bookmark/heading boundaries, target-title checks, and modification-time caching keep sources scoped. Complete indexed chapters can be used when explicitly tagged.
- Missing, scanned/unreadable, unmatched, or oversized chapter sources return CHAPTER_SOURCE_UNAVAILABLE before message persistence, AI calls or credit deductions; no source-status placeholder cards. The composer preserves the user's focus on this error.
- Fixed ordinary tutor retrieval so a missing full-text index still runs its regex fallback. Normal auth, Stop, credits, mind maps and study flowcharts retained; visual generation no longer reuses earlier failed assistant replies.
- Cheat sheets/notes have a maximum 2400 output tokens, still bounded by the plan's routing budget. Other visual caps remain 1200. Chapter extraction supports up to 80000 text characters; scanned documents require readable/OCR text rather than invented replacement content.
- Files: backend/routes/chat.py; backend/requirements.txt (PyMuPDF==1.26.6); frontend/src/components/StudyVisualCard.jsx; frontend/src/components/ChatPage.jsx. No new backend module or database migration.
- Checks: Python parse, complete frontend build, distinct component/schema/parser tests, real multipage PDF exports and rendered inspection, real PDF chapter extraction/boundary/final-page/school-isolation tests, missing-index fallback, session-refresh regressions, and mocked-provider NIOS/BNPS mounted API checks passed. Missing-source route verified no provider call, stored message or user credit change. Actual deployed source files/model quality remain a preview check.
- Backup baseline: d38616c7f7d890dd4d208419d13d02264c2d2432 (upd 8.4). The current GitHub NIOS Mathematics PDF is missing: this code can read it when supplied in the correct school folder but cannot create textbook source content.



## upd 8.6 — Verified NIOS Mathematics topic-to-PDF mapping (2026-10-08)

- Mapped all 14 existing NIOS Maths app topics to the actual uploaded 663-page Mathematics-All Chapters.pdf. Existing labels, syllabus/account data, schools and other subjects are unchanged.
- Applications of Trigonometry now reads section 23.5 Application of Trigonometry within Trigonometric Ratios of Some Special Angles. Linear equations in two variables and circle areas also use the relevant numbered sections; broad topics such as Statistics combine their applicable lessons.
- All NIOS Maths Visualize formats receive the mapped text directly, bypassing the old subject-search snippet. Textbook explanations, worked examples and recap are retained; repeated terminal exercises/answer banks are omitted. Prior failed assistant replies are not supplied as source history for these requests.
- Mapping is locked to the SHA256 of the verified uploaded book; a different/recompressed edition must be verified/remapped rather than silently reusing page ranges. The source file is never changed. Whole-book parsing and per-topic excerpts are cached by file modification time/size; first real-file read about 8 seconds, cached topic reads milliseconds in local tests.
- Missing/unreadable/unmatched sources fail before message persistence, AI calls or credit deductions. Backend startup does not eagerly import/open the PDF. Requirements record PyMuPDF==1.26.6.
- Mapped NIOS Maths cheat sheets/notes receive up to 2400 output tokens, still capped by the plan routing budget; other visual caps remain 1200. Maths cheat sheets request complete concept/formula/example coverage, and quick revision uses question headings for answer reveal.
- Replacements: backend/routes/chat.py and backend/requirements.txt. No frontend change, new backend module or database migration. Current uploaded GitHub baseline contains the earlier tutor backend, so this replacement includes the direct Maths reader itself. Other previous UI updates are not reapplied by this focused patch.
- Tests: all 14 mappings passed against the ACTUAL uploaded PDF, including section boundaries, late example, unknown/wrong-book rejection and cache reuse. Python compile and mocked-provider mounted FastAPI regressions passed for NIOS/BNPS. Source-unavailable route checked no provider call, stored message or credit change; BNPS never invokes the NIOS Maths reader. No live AI provider call was made; preview response accuracy remains a user test.
- Baseline backup: df1697dff406a1928e641888dc76738d72bea64b. UPDATE_LOG.md was absent from that uploaded baseline; prior local update history is preserved here.
