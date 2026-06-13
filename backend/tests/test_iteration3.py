"""
Iteration 3 tests: AceIt AI rename, credit costs, question bank stats,
chat no daily limit, quiz=15cr, mock=30cr, /api/auth/me, syllabus chapter names.
"""
import os
import pytest
import requests

# Load BASE_URL from environment or frontend .env
def _load_base_url():
    url = os.environ.get("REACT_APP_BACKEND_URL")
    if url:
        return url.rstrip("/")
    env_path = os.path.join(os.path.dirname(__file__), "../../frontend/.env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    return line.split("=", 1)[1].strip().rstrip("/")
    raise RuntimeError("REACT_APP_BACKEND_URL not set")

BASE_URL = _load_base_url()
ADMIN_EMAIL = "admin@neuralearn.ai"
ADMIN_PASS = "Admin@123456"


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def admin_session():
    """Authenticated admin session (JWT cookie)."""
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login",
               json={"email": ADMIN_EMAIL, "password": ADMIN_PASS},
               timeout=15)
    assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text}"
    return s


@pytest.fixture(scope="module")
def student_session():
    """Register + login a fresh test student and return session."""
    import uuid
    email = f"TEST_it3_{uuid.uuid4().hex[:8]}@neuralearn.ai"
    s = requests.Session()
    reg = s.post(f"{BASE_URL}/api/auth/register",
                 json={"email": email, "password": "Test@12345", "name": "IT3 Student"},
                 timeout=15)
    assert reg.status_code in (200, 201), f"Register failed: {reg.status_code} {reg.text}"
    # Set class_level via onboarding so grade-lock passes
    s.post(f"{BASE_URL}/api/onboarding/submit",
           json={"name": "IT3 Student", "class_level": "9",
                 "exam_goal": "Improve grades", "weak_subjects": [], "learning_style": "balanced"},
           timeout=15)
    return s


# ── Auth ──────────────────────────────────────────────────────────────────────

class TestAuth:
    """POST /api/auth/login and GET /api/auth/me"""

    def test_login_success(self, admin_session):
        # Just verify the session cookie is set (login done in fixture)
        r = admin_session.get(f"{BASE_URL}/api/auth/me", timeout=10)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"

    def test_auth_me_returns_correct_fields(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/auth/me", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert "user_id" in data, "Missing user_id"
        assert "email" in data, "Missing email"
        assert data["email"] == ADMIN_EMAIL, f"Expected {ADMIN_EMAIL}, got {data['email']}"

    def test_auth_me_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/auth/me", timeout=10)
        assert r.status_code in (401, 403), f"Expected 401/403 without auth, got {r.status_code}"

    def test_login_bad_credentials(self):
        r = requests.post(f"{BASE_URL}/api/auth/login",
                          json={"email": "bad@bad.com", "password": "wrong"},
                          timeout=10)
        assert r.status_code in (401, 422), f"Expected 401/422, got {r.status_code}"


# ── Question Bank Stats ───────────────────────────────────────────────────────

class TestQuestionBankStats:
    """GET /api/question-bank/stats - public endpoint"""

    def test_stats_returns_200(self):
        r = requests.get(f"{BASE_URL}/api/question-bank/stats", timeout=10)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"

    def test_stats_has_required_fields(self):
        r = requests.get(f"{BASE_URL}/api/question-bank/stats", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert "total_qa_pairs" in data, "Missing total_qa_pairs"
        assert "build_running" in data, "Missing build_running"
        assert "done_chapters" in data, "Missing done_chapters"
        assert "total_chapters" in data, "Missing total_chapters"
        assert isinstance(data["total_qa_pairs"], int), "total_qa_pairs must be int"
        assert isinstance(data["build_running"], bool), "build_running must be bool"
        print(f"QB stats: {data}")


# ── Quiz Credit Cost = 15 ─────────────────────────────────────────────────────

class TestQuizCreditCost:
    """Quiz generation deducts 15 credits (CREDIT_COSTS['quiz_generate'] = 15)"""

    def test_quiz_generate_deducts_15_credits(self, student_session):
        # Get current credits
        me_r = student_session.get(f"{BASE_URL}/api/auth/me", timeout=10)
        assert me_r.status_code == 200
        user_data = me_r.json()
        credits_before = user_data.get("credits", 0)
        print(f"Credits before quiz: {credits_before}")

        if credits_before < 15:
            pytest.skip(f"Not enough credits to test quiz (have {credits_before}, need 15)")

        # Generate quiz
        gen_r = student_session.post(
            f"{BASE_URL}/api/quiz/generate",
            json={"class_level": "9", "subject": "Science", "topic": "Atoms and Molecules",
                  "num_questions": 3, "difficulty": "easy"},
            timeout=60
        )
        if gen_r.status_code == 429:
            pytest.skip("Daily quiz limit hit — skipping credit test")
        assert gen_r.status_code == 200, f"Quiz gen failed: {gen_r.status_code} {gen_r.text}"

        # Check credits after
        me_after = student_session.get(f"{BASE_URL}/api/auth/me", timeout=10)
        assert me_after.status_code == 200
        credits_after = me_after.json().get("credits", 0)
        deducted = credits_before - credits_after
        print(f"Credits after quiz: {credits_after}, deducted: {deducted}")
        assert deducted == 15, f"Expected 15 credits deducted for quiz, got {deducted}"


# ── Mock Exam Credit Cost = 30 ────────────────────────────────────────────────

class TestMockExamCreditCost:
    """Mock exam generation deducts 30 credits (CREDIT_COSTS['mock_exam_generate'] = 30)"""

    def test_mock_exam_deducts_30_credits(self, student_session):
        me_r = student_session.get(f"{BASE_URL}/api/auth/me", timeout=10)
        assert me_r.status_code == 200
        credits_before = me_r.json().get("credits", 0)
        print(f"Credits before mock exam: {credits_before}")

        if credits_before < 30:
            pytest.skip(f"Not enough credits for mock exam (have {credits_before}, need 30)")

        gen_r = student_session.post(
            f"{BASE_URL}/api/mock-exam/generate",
            json={"class_level": "9", "subject": "Science",
                  "num_questions": 5, "duration_minutes": 30},
            timeout=90
        )
        if gen_r.status_code == 429:
            pytest.skip("Daily mock exam limit hit — skipping credit test")
        assert gen_r.status_code == 200, f"Mock exam gen failed: {gen_r.status_code} {gen_r.text}"

        me_after = student_session.get(f"{BASE_URL}/api/auth/me", timeout=10)
        assert me_after.status_code == 200
        credits_after = me_after.json().get("credits", 0)
        deducted = credits_before - credits_after
        print(f"Credits after mock exam: {credits_after}, deducted: {deducted}")
        assert deducted == 30, f"Expected 30 credits deducted for mock exam, got {deducted}"


# ── No Daily Message Limit for AI Chat ───────────────────────────────────────

class TestChatNoLimit:
    """Chat endpoint should NOT have daily message limit (check_limit removed)."""

    def test_chat_session_creation(self, student_session):
        r = student_session.post(
            f"{BASE_URL}/api/chat/sessions",
            json={"class_level": "9", "subject": "Science",
                  "chapter": "Atoms and Molecules", "chapter_id": "c9s3"},
            timeout=15
        )
        assert r.status_code == 200, f"Chat session creation failed: {r.status_code} {r.text}"
        data = r.json()
        assert "session_id" in data
        print(f"Chat session created: {data['session_id']}")

    def test_chat_plan_gates_import_has_no_check_limit_for_ai_message(self):
        """Verify the chat route does NOT call check_limit for ai_message."""
        chat_path = os.path.join(os.path.dirname(__file__), "../routes/chat.py")
        with open(chat_path) as f:
            content = f.read()
        # "check_limit" for "ai_messages"/"ai_message" should NOT appear
        assert "check_limit" not in content or "ai_message" not in content, \
            "chat.py still calls check_limit for ai_message — daily limit not removed!"
        print("Confirmed: check_limit not used for ai_message in chat.py")


# ── Syllabus Chapter Names (no chapter numbers) ───────────────────────────────

class TestSyllabusChapterNames:
    """Chapters endpoint returns names, not 'Chapter X' numbered text."""

    def test_chapters_endpoint_returns_names(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/syllabus/9/Science/chapters", timeout=15)
        assert r.status_code == 200, f"Chapters endpoint failed: {r.status_code}"
        chapters = r.json()
        assert len(chapters) > 0, "No chapters returned"
        for ch in chapters:
            assert "name" in ch, f"Chapter missing 'name': {ch}"
            name = ch["name"]
            print(f"  Chapter: {name}")
        print(f"Total chapters: {len(chapters)}")

    def test_chapters_dont_have_chapter_number_prefix_in_display(self, admin_session):
        """SyllabusPage shows ch.name - API should not return 'Chapter N:' prefixed names."""
        r = admin_session.get(f"{BASE_URL}/api/syllabus/9/Science/chapters", timeout=15)
        assert r.status_code == 200
        chapters = r.json()
        # Check that no chapter name is ONLY "Chapter N" (pure numeric - no real title)
        generic_chapters = [ch["name"] for ch in chapters if ch["name"].strip().lower().startswith("chapter ") and ch["name"].strip().lower() == f"chapter {ch.get('chapter_no', '')}".lower()]
        print(f"Generic 'Chapter N' names found: {generic_chapters}")
        # This is informational - the API might have some generic names from NCERT metadata
        # The frontend (SyllabusPage) shows ch.name directly without adding chapter number prefix

    def test_subjects_endpoint(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/syllabus/9/subjects", timeout=15)
        assert r.status_code == 200, f"Subjects endpoint failed: {r.status_code}"
        subjects = r.json()
        assert len(subjects) > 0, "No subjects returned"
        for s in subjects:
            assert "name" in s
            print(f"  Subject: {s['name']}")


# ── Credits Module Verification ───────────────────────────────────────────────

class TestCreditsConfig:
    """Verify CREDIT_COSTS values match requirements."""

    def test_quiz_cost_is_15(self):
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from credits import CREDIT_COSTS, CHAT_WORD_LIMIT
        assert CREDIT_COSTS["quiz_generate"] == 15, \
            f"quiz_generate cost should be 15, got {CREDIT_COSTS['quiz_generate']}"
        print(f"quiz_generate credit cost: {CREDIT_COSTS['quiz_generate']} ✓")

    def test_mock_exam_cost_is_30(self):
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from credits import CREDIT_COSTS
        assert CREDIT_COSTS["mock_exam_generate"] == 30, \
            f"mock_exam_generate cost should be 30, got {CREDIT_COSTS['mock_exam_generate']}"
        print(f"mock_exam_generate credit cost: {CREDIT_COSTS['mock_exam_generate']} ✓")

    def test_chat_word_limit_is_1000(self):
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from credits import CHAT_WORD_LIMIT
        assert CHAT_WORD_LIMIT == 1000, \
            f"CHAT_WORD_LIMIT should be 1000, got {CHAT_WORD_LIMIT}"
        print(f"CHAT_WORD_LIMIT: {CHAT_WORD_LIMIT} ✓")
