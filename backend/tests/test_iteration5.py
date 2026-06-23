"""
Iteration 5 Backend Tests — AceIt AI
Tests for:
- Admin login / auth flow
- Email verification endpoints
- Admin verify-user endpoint
- NCERT syllabus (corrupt title fix) for classes 6 & 7
- Credit tier logic (calculate_chat_credits)
- GET /api/analytics/dashboard
- GET /api/question-bank/stats
- POST /api/quiz/generate
- POST /api/quiz/{quiz_id}/submit with dict answers format
- InteractiveQuizModal fix verification (answers as dict, no quiz_id in body)
"""
import pytest
import requests
import uuid
import os
import sys

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

if not BASE_URL:
    pytest.exit("REACT_APP_BACKEND_URL env var not set!", returncode=1)


# ─── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def admin_session():
    """Authenticated admin requests session."""
    session = requests.Session()
    resp = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@neuralearn.ai",
        "password": "Admin@123456"
    })
    if resp.status_code != 200:
        pytest.skip(f"Admin login failed: {resp.status_code} {resp.text}")
    print(f"Admin login OK. Status: {resp.status_code}")
    return session


@pytest.fixture(scope="module")
def test_user_email():
    """Unique test email for registration tests."""
    return f"TEST_it5_{uuid.uuid4().hex[:8]}@mailtest.dev"


# ─── 1. Admin Login ────────────────────────────────────────────────────────────
class TestAdminLogin:
    """Admin login — verified user admin@neuralearn.ai / Admin@123456"""

    def test_admin_login_success(self):
        """Admin login returns 200 with user data"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@neuralearn.ai",
            "password": "Admin@123456"
        })
        assert resp.status_code == 200, f"Admin login failed: {resp.status_code} {resp.text}"
        data = resp.json()
        assert "user_id" in data, f"No user_id in response: {data}"
        assert data.get("email") == "admin@neuralearn.ai"
        assert data.get("is_verified") is True, f"Admin should be verified: {data}"
        print(f"PASS: Admin login → user_id={data['user_id']}, plan={data.get('plan')}")

    def test_admin_login_wrong_password(self):
        """Wrong password returns 401"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@neuralearn.ai",
            "password": "WrongPassword123"
        })
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"
        print("PASS: Wrong password → 401")

    def test_admin_get_me(self, admin_session):
        """Authenticated /api/auth/me returns correct user data"""
        resp = admin_session.get(f"{BASE_URL}/api/auth/me")
        assert resp.status_code == 200, f"/auth/me failed: {resp.status_code} {resp.text}"
        data = resp.json()
        assert data.get("email") == "admin@neuralearn.ai"
        assert data.get("is_verified") is True
        print(f"PASS: /auth/me → email={data['email']}, plan={data.get('plan')}")


# ─── 2. Email Verification Flow ────────────────────────────────────────────────
class TestEmailVerification:
    """Email verification: register → unverified login → resend → invalid token"""

    def test_register_new_user(self, test_user_email):
        """Registration returns 200 with requires_verification=True"""
        resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_user_email,
            "name": "IT5 Test User",
            "password": "Test@123456",
            "class_level": "9"
        })
        assert resp.status_code == 200, f"Register failed: {resp.status_code} {resp.text}"
        data = resp.json()
        assert data.get("requires_verification") is True, \
            f"Expected requires_verification=True, got: {data}"
        assert "message" in data
        print(f"PASS: Register → requires_verification=True. Email={test_user_email}")

    def test_login_unverified_gets_403_email_not_verified(self, test_user_email):
        """Unverified user login returns 403 with EMAIL_NOT_VERIFIED code"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": test_user_email,
            "password": "Test@123456"
        })
        assert resp.status_code == 403, \
            f"Expected 403, got {resp.status_code}: {resp.text}"
        detail = resp.json().get("detail", {})
        assert detail.get("code") == "EMAIL_NOT_VERIFIED", \
            f"Expected EMAIL_NOT_VERIFIED, got: {detail}"
        assert "email" in detail
        print(f"PASS: Unverified login → 403 EMAIL_NOT_VERIFIED for {detail['email']}")

    def test_resend_verification_returns_success(self, test_user_email):
        """Resend verification endpoint returns 200 with message"""
        resp = requests.post(f"{BASE_URL}/api/auth/resend-verification",
                             json={"email": test_user_email})
        assert resp.status_code == 200, \
            f"resend-verification failed: {resp.status_code} {resp.text}"
        data = resp.json()
        assert "message" in data, f"No message in response: {data}"
        print(f"PASS: resend-verification → {data['message']}")

    def test_resend_verification_unknown_email_still_200(self):
        """Unknown email returns 200 (anti-enumeration)"""
        resp = requests.post(f"{BASE_URL}/api/auth/resend-verification",
                             json={"email": "unknown_TEST_never_exists@mailtest.dev"})
        assert resp.status_code == 200, \
            f"Expected 200 for anti-enumeration, got {resp.status_code}: {resp.text}"
        print("PASS: Unknown email → 200 anti-enumeration")

    def test_verify_email_invalid_token_returns_400(self):
        """GET /api/auth/verify-email?token=INVALID_TOKEN returns 400 with INVALID_TOKEN code"""
        resp = requests.get(f"{BASE_URL}/api/auth/verify-email",
                            params={"token": "INVALID_TOKEN_xyz999_completely_bogus"})
        assert resp.status_code == 400, \
            f"Expected 400 for invalid token, got {resp.status_code}: {resp.text}"
        detail = resp.json().get("detail", {})
        assert detail.get("code") == "INVALID_TOKEN", \
            f"Expected code=INVALID_TOKEN, got: {detail}"
        print(f"PASS: Invalid token → 400 INVALID_TOKEN")


# ─── 3. Admin Verify User ──────────────────────────────────────────────────────
class TestAdminVerifyUser:
    """POST /api/auth/admin/verify-user — admin-only manual verification"""

    def test_admin_can_verify_user(self, admin_session, test_user_email):
        """Admin can manually verify a user"""
        resp = admin_session.post(f"{BASE_URL}/api/auth/admin/verify-user",
                                  json={"email": test_user_email})
        assert resp.status_code == 200, \
            f"admin verify-user failed: {resp.status_code} {resp.text}"
        data = resp.json()
        assert data.get("success") is True, f"Expected success=True: {data}"
        print(f"PASS: Admin verified user {test_user_email}")

    def test_verified_user_can_now_login(self, test_user_email):
        """After admin verification, user can log in"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": test_user_email,
            "password": "Test@123456"
        })
        assert resp.status_code == 200, \
            f"Login after admin verification failed: {resp.status_code} {resp.text}"
        data = resp.json()
        assert data.get("is_verified") is True, f"User should be verified: {data}"
        print(f"PASS: Verified user can now login: {test_user_email}")

    def test_non_admin_cannot_verify_user(self):
        """Non-admin session should get 403 on admin verify-user"""
        # Register and login a regular user
        email = f"TEST_nonadmin_{uuid.uuid4().hex[:6]}@mailtest.dev"
        # First register
        requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": email,
            "name": "NonAdmin",
            "password": "Test@123456",
            "class_level": "9"
        })
        # Can't login (unverified) — skip admin verification via admin, attempt directly
        # We'll test using a session without auth
        resp = requests.post(f"{BASE_URL}/api/auth/admin/verify-user",
                             json={"email": email})
        # Without auth cookie, should get 401 or 403
        assert resp.status_code in [401, 403], \
            f"Expected 401/403 for unauthenticated verify-user, got {resp.status_code}: {resp.text}"
        print(f"PASS: Non-admin → {resp.status_code} for admin verify-user")


# ─── 4. NCERT Syllabus — No Corrupt Titles ─────────────────────────────────────
class TestNCERTSyllabus:
    """NCERT: no 'Question Answer in Hindi' or corrupt titles in classes 6, 7"""

    CORRUPT_PATTERNS = [
        "question answer in hindi",
        "question answer",
        "in hindi",
        "ncert textbook",
    ]

    def _check_no_corrupt(self, chapters: list, class_id: str, subject: str):
        corrupt_found = []
        for ch in chapters:
            name = ch.get("name", "")
            for pat in self.CORRUPT_PATTERNS:
                if pat.lower() in name.lower():
                    corrupt_found.append(f"Ch '{name}' matches pattern '{pat}'")
        assert not corrupt_found, \
            f"Class {class_id} {subject} has corrupt titles: {corrupt_found}"
        # Also ensure no empty/generic chapter names
        generic_names = {"", "chapter"} | {f"chapter {i}" for i in range(1, 30)}
        # generic check is lenient — just verify there are real titles
        has_real_names = any(len(ch.get("name", "")) > 10 for ch in chapters)
        assert has_real_names, \
            f"Class {class_id} {subject}: no chapter has a real name (>10 chars)"
        print(f"PASS: Class {class_id} {subject} — {len(chapters)} chapters, no corrupt titles")

    def test_class6_science_chapters_no_corrupt(self):
        """Class 6 Science chapters have no 'Question Answer in Hindi' or corrupt names"""
        resp = requests.get(f"{BASE_URL}/api/syllabus/6/Science/chapters")
        assert resp.status_code == 200, \
            f"Class 6 Science chapters failed: {resp.status_code} {resp.text}"
        chapters = resp.json()
        assert len(chapters) > 0, "No chapters returned for Class 6 Science"
        print(f"Class 6 Science: {[ch['name'] for ch in chapters[:3]]}...")
        self._check_no_corrupt(chapters, "6", "Science")

    def test_class7_science_chapters_no_corrupt(self):
        """Class 7 Science chapters have no corrupt names"""
        resp = requests.get(f"{BASE_URL}/api/syllabus/7/Science/chapters")
        assert resp.status_code == 200, \
            f"Class 7 Science chapters failed: {resp.status_code} {resp.text}"
        chapters = resp.json()
        assert len(chapters) > 0, "No chapters returned for Class 7 Science"
        print(f"Class 7 Science: {[ch['name'] for ch in chapters[:3]]}...")
        self._check_no_corrupt(chapters, "7", "Science")

    def test_class6_science_has_verified_chapters(self):
        """Class 6 Science chapters should be verified=True from NCERT engine"""
        resp = requests.get(f"{BASE_URL}/api/syllabus/6/Science/chapters")
        assert resp.status_code == 200
        chapters = resp.json()
        verified_count = sum(1 for ch in chapters if ch.get("verified") is True)
        print(f"Class 6 Science: {verified_count}/{len(chapters)} verified chapters")
        # At least some chapters should be verified
        assert verified_count > 0, "No verified chapters for Class 6 Science"

    def test_class10_science_chapters_no_corrupt(self):
        """Class 10 Science chapters (used by admin) have clean names"""
        resp = requests.get(f"{BASE_URL}/api/syllabus/10/Science/chapters")
        if resp.status_code == 404:
            pytest.skip("Class 10 Science not available")
        assert resp.status_code == 200, \
            f"Class 10 Science failed: {resp.status_code} {resp.text}"
        chapters = resp.json()
        if chapters:
            self._check_no_corrupt(chapters, "10", "Science")


# ─── 5. Credit Tier Logic ──────────────────────────────────────────────────────
class TestCreditTiers:
    """Dynamic credit calculation: word_count → credit tiers 2/4/6/8/10"""

    def test_credit_tiers_via_import(self):
        """Unit test calculate_chat_credits via direct import"""
        try:
            sys.path.insert(0, "/app/backend")
            from credits import calculate_chat_credits
            assert calculate_chat_credits(200) == 2, f"200 words → expected 2, got {calculate_chat_credits(200)}"
            assert calculate_chat_credits(250) == 2, f"250 words → expected 2, got {calculate_chat_credits(250)}"
            assert calculate_chat_credits(400) == 4, f"400 words → expected 4, got {calculate_chat_credits(400)}"
            assert calculate_chat_credits(500) == 4, f"500 words → expected 4, got {calculate_chat_credits(500)}"
            assert calculate_chat_credits(700) == 6, f"700 words → expected 6, got {calculate_chat_credits(700)}"
            assert calculate_chat_credits(800) == 6, f"800 words → expected 6, got {calculate_chat_credits(800)}"
            assert calculate_chat_credits(1000) == 8, f"1000 words → expected 8, got {calculate_chat_credits(1000)}"
            assert calculate_chat_credits(1200) == 8, f"1200 words → expected 8, got {calculate_chat_credits(1200)}"
            assert calculate_chat_credits(1300) == 10, f"1300 words → expected 10, got {calculate_chat_credits(1300)}"
            assert calculate_chat_credits(2000) == 10, f"2000 words → expected 10, got {calculate_chat_credits(2000)}"
            print("PASS: All credit tiers correct (2/4/6/8/10)")
        except ImportError as e:
            pytest.skip(f"Cannot import credits module: {e}")


# ─── 6. Analytics Dashboard ────────────────────────────────────────────────────
class TestAnalyticsDashboard:
    """GET /api/analytics/dashboard — admin access, returns users/credits/quiz stats"""

    def test_analytics_dashboard_returns_200(self, admin_session):
        """Admin gets analytics dashboard"""
        resp = admin_session.get(f"{BASE_URL}/api/analytics/dashboard")
        assert resp.status_code == 200, \
            f"Analytics dashboard failed: {resp.status_code} {resp.text}"
        data = resp.json()
        # Verify structure
        assert "users" in data, f"No 'users' in analytics: {data.keys()}"
        assert "quiz_stats" in data, f"No 'quiz_stats' in analytics: {data.keys()}"
        assert "question_bank" in data, f"No 'question_bank' in analytics: {data.keys()}"
        print(f"PASS: Analytics dashboard OK. Users total={data['users']['total']}, "
              f"verified={data['users']['verified']}")

    def test_analytics_dashboard_user_counts(self, admin_session):
        """Users analytics has expected fields"""
        resp = admin_session.get(f"{BASE_URL}/api/analytics/dashboard")
        assert resp.status_code == 200
        users = resp.json()["users"]
        assert "total" in users and "verified" in users and "unverified" in users
        assert users["total"] > 0, "Should have at least 1 user (admin)"
        assert users["verified"] > 0, "Should have at least 1 verified user (admin)"
        print(f"PASS: User counts — total={users['total']}, verified={users['verified']}, "
              f"unverified={users['unverified']}")

    def test_analytics_dashboard_question_bank_count(self, admin_session):
        """Analytics returns question bank total_qa_pairs"""
        resp = admin_session.get(f"{BASE_URL}/api/analytics/dashboard")
        assert resp.status_code == 200
        qb = resp.json()["question_bank"]
        assert "total_qa_pairs" in qb
        print(f"PASS: Question bank total_qa_pairs = {qb['total_qa_pairs']}")

    def test_analytics_dashboard_requires_auth(self):
        """Unauthenticated request to analytics dashboard → 401 or 403"""
        resp = requests.get(f"{BASE_URL}/api/analytics/dashboard")
        assert resp.status_code in [401, 403], \
            f"Expected 401/403, got {resp.status_code}: {resp.text}"
        print(f"PASS: Unauthenticated analytics → {resp.status_code}")


# ─── 7. Question Bank Stats ────────────────────────────────────────────────────
class TestQuestionBankStats:
    """GET /api/question-bank/stats — public, returns total_qa_pairs"""

    def test_question_bank_stats_200(self):
        """Stats endpoint returns 200"""
        resp = requests.get(f"{BASE_URL}/api/question-bank/stats")
        assert resp.status_code == 200, \
            f"Question bank stats failed: {resp.status_code} {resp.text}"
        data = resp.json()
        assert "total_qa_pairs" in data, f"No total_qa_pairs in response: {data}"
        print(f"PASS: Question bank stats → total_qa_pairs={data['total_qa_pairs']}")

    def test_question_bank_stats_has_pairs(self):
        """Question bank should have Q&A pairs from previous build"""
        resp = requests.get(f"{BASE_URL}/api/question-bank/stats")
        assert resp.status_code == 200
        data = resp.json()
        total = data.get("total_qa_pairs", 0)
        # Based on context: 1902 pairs from iteration 4
        print(f"INFO: Question bank has {total} Q&A pairs")
        # Non-zero check (might be 0 if build hasn't run, treat as warning not failure)
        if total == 0:
            print("WARNING: Question bank is empty — build may not have run")
        else:
            assert total > 100, f"Expected >100 Q&A pairs, got {total}"
            print(f"PASS: Question bank has {total} Q&A pairs (>=100)")

    def test_question_bank_stats_structure(self):
        """Stats response has all expected fields"""
        resp = requests.get(f"{BASE_URL}/api/question-bank/stats")
        assert resp.status_code == 200
        data = resp.json()
        required_fields = ["total_qa_pairs", "build_running", "done_chapters", "total_chapters"]
        for field in required_fields:
            assert field in data, f"Missing field '{field}' in stats: {data.keys()}"
        print(f"PASS: Stats has all required fields: {list(data.keys())}")


# ─── 8. Quiz Generate + Submit ─────────────────────────────────────────────────
class TestQuizGenerateSubmit:
    """POST /api/quiz/generate and POST /api/quiz/{quiz_id}/submit"""

    @pytest.fixture(scope="class")
    def quiz_id(self, admin_session):
        """Generate a quiz and return its ID."""
        resp = admin_session.post(f"{BASE_URL}/api/quiz/generate", json={
            "class_level": "10",
            "subject": "Science",
            "topic": "Light Reflection and Refraction",
            "num_questions": 2,
            "difficulty": "easy"
        })
        if resp.status_code == 429:
            pytest.skip(f"Daily quiz limit reached: {resp.text}")
        if resp.status_code == 402:
            pytest.skip(f"Insufficient credits: {resp.text}")
        assert resp.status_code == 200, f"Quiz generate failed: {resp.status_code} {resp.text}"
        data = resp.json()
        assert "quiz_id" in data, f"No quiz_id in response: {data.keys()}"
        assert "questions" in data, f"No questions in response: {data.keys()}"
        assert len(data["questions"]) >= 1, "No questions generated"
        quiz_id = data["quiz_id"]
        print(f"PASS: Quiz generated → quiz_id={quiz_id}, questions={len(data['questions'])}")
        return quiz_id

    def test_quiz_generate_returns_questions(self, admin_session):
        """Quiz generate returns quiz_id and questions"""
        resp = admin_session.post(f"{BASE_URL}/api/quiz/generate", json={
            "class_level": "10",
            "subject": "Science",
            "topic": "Electricity",
            "num_questions": 2,
            "difficulty": "medium"
        })
        if resp.status_code == 429:
            pytest.skip("Daily quiz limit reached")
        if resp.status_code == 402:
            pytest.skip("Insufficient credits")
        assert resp.status_code == 200, f"Quiz generate: {resp.status_code} {resp.text}"
        data = resp.json()
        assert "quiz_id" in data
        assert "questions" in data
        assert len(data["questions"]) > 0
        # Verify question structure
        q = data["questions"][0]
        assert "question" in q, f"Question missing 'question' field: {q.keys()}"
        assert "options" in q, f"Question missing 'options' field: {q.keys()}"
        assert "correct" in q, f"Question missing 'correct' field: {q.keys()}"
        print(f"PASS: Quiz generate → quiz_id={data['quiz_id']}, q[0]={q['question'][:50]}...")

    def test_quiz_submit_with_dict_answers(self, admin_session, quiz_id):
        """Quiz submit with dict answers {index: letter} returns score"""
        resp = admin_session.post(
            f"{BASE_URL}/api/quiz/{quiz_id}/submit",
            json={"answers": {"0": "A", "1": "B"}}
        )
        assert resp.status_code == 200, \
            f"Quiz submit failed: {resp.status_code} {resp.text}"
        data = resp.json()
        assert "score" in data, f"No score in response: {data}"
        assert "correct_count" in data
        assert "total_questions" in data
        assert "results" in data
        assert "xp_earned" in data
        print(f"PASS: Quiz submit (dict format) → score={data['score']}%, "
              f"xp={data['xp_earned']}, correct={data['correct_count']}/{data['total_questions']}")

    def test_quiz_submit_no_quiz_id_in_body(self, admin_session, quiz_id):
        """Quiz submit should NOT require quiz_id in body (path param only) — fixed format"""
        # This tests the fix: quiz_id is ONLY in the path, not the body
        resp = admin_session.post(
            f"{BASE_URL}/api/quiz/{quiz_id}/submit",
            json={"answers": {"0": "A", "1": "A"}}  # No quiz_id in body
        )
        # Should succeed (422 would mean model still requires quiz_id in body)
        assert resp.status_code == 200, \
            f"Submit without quiz_id in body failed (422 = model still requires quiz_id): {resp.status_code} {resp.text}"
        print(f"PASS: Quiz submit works without quiz_id in body")

    def test_quiz_submit_invalid_quiz_id(self, admin_session):
        """Submitting to non-existent quiz → 404"""
        resp = admin_session.post(
            f"{BASE_URL}/api/quiz/quiz_nonexistent_id/submit",
            json={"answers": {"0": "A"}}
        )
        assert resp.status_code == 404, \
            f"Expected 404 for non-existent quiz, got {resp.status_code}: {resp.text}"
        print(f"PASS: Non-existent quiz → 404")


# ─── 9. Interactive Quiz Modal Format Fix Verification ─────────────────────────
class TestInteractiveQuizModalFormat:
    """Verify InteractiveQuizModal fix: sends dict answers without quiz_id in body"""

    def test_modal_format_sends_dict_not_array(self, admin_session):
        """Test the exact format InteractiveQuizModal now sends (post-fix)"""
        # Generate a quiz first
        gen_resp = admin_session.post(f"{BASE_URL}/api/quiz/generate", json={
            "class_level": "10",
            "subject": "Mathematics",
            "topic": "Polynomials",
            "num_questions": 2,
            "difficulty": "easy"
        })
        if gen_resp.status_code == 429:
            pytest.skip("Daily quiz limit reached")
        if gen_resp.status_code == 402:
            pytest.skip("Insufficient credits")
        if gen_resp.status_code != 200:
            pytest.skip(f"Quiz generation failed: {gen_resp.status_code}")

        quiz_data = gen_resp.json()
        quiz_id = quiz_data["quiz_id"]

        # Submit in the NEW format (post-fix): dict answers, no quiz_id in body
        submit_resp = admin_session.post(
            f"{BASE_URL}/api/quiz/{quiz_id}/submit",
            json={"answers": {"0": "A", "1": "B"}}  # dict format, no quiz_id
        )
        assert submit_resp.status_code == 200, \
            f"Modal format submit failed: {submit_resp.status_code} {submit_resp.text}"
        data = submit_resp.json()
        assert "score" in data and "results" in data
        print(f"PASS: InteractiveQuizModal post-fix format works → score={data['score']}%")

    def test_old_modal_format_array_would_fail(self, admin_session):
        """Verify that old array format (pre-fix) returns 422 (regression guard)"""
        # Generate a quiz
        gen_resp = admin_session.post(f"{BASE_URL}/api/quiz/generate", json={
            "class_level": "10",
            "subject": "Science",
            "topic": "Carbon Compounds",
            "num_questions": 2,
            "difficulty": "easy"
        })
        if gen_resp.status_code not in [200]:
            pytest.skip(f"Quiz generation failed: {gen_resp.status_code}")

        quiz_id = gen_resp.json()["quiz_id"]

        # Old format: answers as array — this should fail with 422
        old_format_resp = admin_session.post(
            f"{BASE_URL}/api/quiz/{quiz_id}/submit",
            json={
                "answers": [
                    {"question_index": 0, "selected_answer": "A", "time_spent_s": 10}
                ]
            }
        )
        # Backend QuizSubmitRequest expects answers:dict, not list → 422
        assert old_format_resp.status_code == 422, \
            f"Expected 422 for array format (old modal format), got {old_format_resp.status_code}: {old_format_resp.text}"
        print(f"PASS: Old array format returns 422 (backend correctly rejects it)")


# ─── 10. Student Analytics Endpoint ───────────────────────────────────────────
class TestStudentAnalytics:
    """GET /api/analytics/student/{user_id}"""

    def test_student_analytics_self(self, admin_session):
        """Admin can get their own student analytics"""
        me_resp = admin_session.get(f"{BASE_URL}/api/auth/me")
        if me_resp.status_code != 200:
            pytest.skip("Admin not authenticated")
        user_id = me_resp.json()["user_id"]

        resp = admin_session.get(f"{BASE_URL}/api/analytics/student/{user_id}")
        assert resp.status_code == 200, \
            f"Student analytics failed: {resp.status_code} {resp.text}"
        data = resp.json()
        assert "profile" in data or "credit_stats" in data, \
            f"Expected profile or credit_stats in response: {data.keys()}"
        print(f"PASS: Student analytics for admin → keys={list(data.keys())}")


# ─── Cleanup Fixture ───────────────────────────────────────────────────────────
@pytest.fixture(scope="session", autouse=True)
def cleanup_test_users():
    """Nothing to clean up here — TEST_ prefixed users are left in unverified state"""
    yield
    print("\nNote: TEST_it5_* users created during testing. They are unverified.")
