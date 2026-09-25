"""Tests for P0/P1/P2a/P2b fixes and NIOS curriculum features."""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

ADMIN_EMAIL = "admin@neuralearn.ai"
ADMIN_PASS = "Admin@123456"
BNPS_EMAIL = "bnps@student.edu"
BNPS_PASS = "Test@12345"
NIOS_EMAIL = f"niostest{uuid.uuid4().hex[:6]}@gmail.com"
NIOS_PASS = "NiosTest@12345"


@pytest.fixture(scope="module")
def admin_session():
    """Return a requests.Session with admin auth cookies set."""
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
    assert r.status_code == 200, f"Admin login failed: {r.text}"
    return s


@pytest.fixture(scope="module")
def bnps_session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": BNPS_EMAIL, "password": BNPS_PASS})
    if r.status_code != 200:
        pytest.skip(f"BNPS login failed: {r.text}")
    return s


@pytest.fixture(scope="module")
def nios_session():
    """Register a NIOS user and return an authenticated session."""
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/register", json={
        "email": NIOS_EMAIL,
        "password": NIOS_PASS,
        "name": "NIOS Test Student",
        "school": "nios",
        "class_level": "10",
    })
    assert r.status_code in [200, 201], f"NIOS register failed: {r.text}"
    # Verify login works (cookies set by register)
    me = s.get(f"{BASE_URL}/api/auth/me")
    assert me.status_code == 200, f"GET /me after register failed: {me.text}"
    return s


# ──────────────────────────────────────────────────────────
# P0: Subscribe endpoint returns 403
# ──────────────────────────────────────────────────────────

class TestP0Subscribe:
    """P0: /api/subscription/subscribe must return 403 (paywall bypass blocked)."""

    def test_subscribe_unauthenticated_returns_401(self):
        r = requests.post(f"{BASE_URL}/api/subscription/subscribe", json={"plan": "pro"})
        # Unauthenticated → 401
        assert r.status_code == 401, f"Expected 401, got {r.status_code}: {r.text}"
        print(f"PASS: unauthenticated subscribe → {r.status_code}")

    def test_subscribe_authenticated_returns_403(self, admin_session):
        r = admin_session.post(
            f"{BASE_URL}/api/subscription/subscribe",
            json={"plan": "pro"},
        )
        assert r.status_code == 403, f"Expected 403, got {r.status_code}: {r.text}"
        print(f"PASS: authenticated subscribe → 403 as expected")
        data = r.json()
        assert "detail" in data
        print(f"  detail: {data['detail']}")


# ──────────────────────────────────────────────────────────
# NIOS: Schools list
# ──────────────────────────────────────────────────────────

class TestNIOSSchools:
    """NIOS schools list tests."""

    def test_schools_list_contains_nios(self):
        r = requests.get(f"{BASE_URL}/api/auth/schools")
        assert r.status_code == 200, f"Schools API failed: {r.text}"
        data = r.json()
        schools = data if isinstance(data, list) else data.get("schools", [])
        ids = [s.get("id") for s in schools]
        assert "nios" in ids, f"NIOS not found in schools: {ids}"
        print(f"PASS: nios in school list: {ids}")

    def test_nios_school_available_and_note(self):
        r = requests.get(f"{BASE_URL}/api/auth/schools")
        assert r.status_code == 200
        data = r.json()
        schools = data if isinstance(data, list) else data.get("schools", [])
        nios = next((s for s in schools if s.get("id") == "nios"), None)
        assert nios is not None
        assert nios.get("available") is True, f"nios available != True: {nios}"
        note = nios.get("note", "")
        assert "Secondary" in note or "Class 10" in note, f"nios note unexpected: {note}"
        print(f"PASS: nios school entry: {nios}")


# ──────────────────────────────────────────────────────────
# NIOS: Registration and class_level auto-set
# ──────────────────────────────────────────────────────────

class TestNIOSRegistration:
    """NIOS user registration tests."""

    def test_nios_user_class_level_is_10(self, nios_session):
        r = nios_session.get(f"{BASE_URL}/api/auth/me")
        assert r.status_code == 200, f"GET /me failed: {r.text}"
        user = r.json()
        assert user.get("school") == "nios", f"school != nios: {user.get('school')}"
        assert str(user.get("class_level")) == "10", f"class_level != 10: {user.get('class_level')}"
        print(f"PASS: NIOS user class_level={user.get('class_level')}, school={user.get('school')}")


# ──────────────────────────────────────────────────────────
# NIOS: Syllabus subjects and chapters
# ──────────────────────────────────────────────────────────

class TestNIOSSyllabus:
    """NIOS syllabus API tests."""

    def test_nios_subjects_returns_7(self, nios_session):
        r = nios_session.get(f"{BASE_URL}/api/syllabus/10/subjects")
        assert r.status_code == 200, f"Subjects API failed: {r.text}"
        data = r.json()
        subjects = data if isinstance(data, list) else data.get("subjects", [])
        names = [s.get("name") for s in subjects]
        assert len(subjects) == 7, f"Expected 7 NIOS subjects, got {len(subjects)}: {names}"
        expected = {"Accountancy", "Business Studies", "Data Entry Operations", "Economics", "English", "Entrepreneurship", "Folk Art"}
        for e in expected:
            assert e in names, f"Subject '{e}' missing from NIOS subjects: {names}"
        print(f"PASS: NIOS subjects ({len(subjects)}): {names}")

    def test_nios_business_studies_has_15_chapters(self, nios_session):
        r = nios_session.get(f"{BASE_URL}/api/syllabus/10/Business%20Studies/chapters")
        assert r.status_code == 200, f"Chapters API failed: {r.text}"
        data = r.json()
        chapters = data if isinstance(data, list) else data.get("chapters", [])
        assert len(chapters) == 15, f"Expected 15 chapters for Business Studies, got {len(chapters)}"
        print(f"PASS: Business Studies chapters: {len(chapters)}")


# ──────────────────────────────────────────────────────────
# P2a: Mock exam replay guard
# ──────────────────────────────────────────────────────────

class TestP2aMockExamReplay:
    """P2a: Submitting same exam twice returns 400."""

    def test_double_submit_returns_400(self, bnps_session):
        """Create a mock exam in DB directly and verify double-submit guard."""
        import uuid as _uuid
        from datetime import datetime, timezone

        # We can't easily create an exam via API (requires AI). 
        # Instead, insert a fake completed exam into DB via the submit endpoint.
        # First, we need to generate a real exam (skip if generation fails).
        
        # Try generating a mock exam via API  
        r_gen = bnps_session.post(
            f"{BASE_URL}/api/mock-exam/generate",
            json={"class_level": "8", "subject": "Science", "num_questions": 10, "duration_minutes": 30},
        )
        
        if r_gen.status_code != 200:
            pytest.skip(f"Mock exam generation failed (status {r_gen.status_code}), skipping replay guard test: {r_gen.text[:200]}")
        
        exam = r_gen.json()
        exam_id = exam.get("exam_id")
        assert exam_id
        print(f"Generated exam: {exam_id}")
        
        r1 = bnps_session.post(f"{BASE_URL}/api/mock-exam/{exam_id}/submit", json={"answers": {}})
        assert r1.status_code == 200, f"First submit failed: {r1.text}"
        
        r2 = bnps_session.post(f"{BASE_URL}/api/mock-exam/{exam_id}/submit", json={"answers": {}})
        assert r2.status_code == 400, f"Expected 400 on second submit, got {r2.status_code}: {r2.text}"
        data2 = r2.json()
        detail = data2.get("detail", "")
        assert "already" in detail.lower() or "submitted" in detail.lower(), f"Unexpected error detail: {detail}"
        print(f"PASS: second submit → 400: {detail}")
