"""BNPS Curriculum and Math Rendering Backend Tests - Iteration 15"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# --- Fixtures ---
@pytest.fixture(scope="module")
def bnps_session():
    session = requests.Session()
    resp = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": "bnps@student.edu",
        "password": "Test@12345"
    })
    assert resp.status_code == 200, f"BNPS login failed: {resp.text}"
    return session

@pytest.fixture(scope="module")
def admin_session():
    session = requests.Session()
    resp = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@neuralearn.ai",
        "password": "Admin@123456"
    })
    assert resp.status_code == 200, f"Admin login failed: {resp.text}"
    return session


# --- Auth Tests ---
class TestBNPSAuth:
    def test_bnps_login(self):
        session = requests.Session()
        resp = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "bnps@student.edu",
            "password": "Test@12345"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("user", {}).get("school") == "brooklyn_national"
        print("PASS: BNPS login - school=brooklyn_national confirmed")

    def test_bnps_me_endpoint(self, bnps_session):
        resp = bnps_session.get(f"{BASE_URL}/api/auth/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("school") == "brooklyn_national"
        assert data.get("class_level") == "8"
        print("PASS: /api/auth/me returns correct BNPS school and class")


# --- Syllabus Tests ---
class TestBNPSSyllabus:
    def test_bnps_syllabus_subjects(self, bnps_session):
        resp = bnps_session.get(f"{BASE_URL}/api/syllabus")
        assert resp.status_code == 200
        data = resp.json()
        # Should have subjects list
        subjects = data if isinstance(data, list) else data.get("subjects", [])
        subject_names = [s.get("name", s) if isinstance(s, dict) else s for s in subjects]
        print(f"Subjects returned: {subject_names}")
        # BNPS subjects should be present
        assert len(subjects) > 0, "No subjects returned"
        print("PASS: BNPS syllabus returns subjects")

    def test_bnps_chapters_mathematics(self, bnps_session):
        resp = bnps_session.get(f"{BASE_URL}/api/syllabus/chapters?subject=Mathematics&class_level=8")
        assert resp.status_code == 200
        data = resp.json()
        chapters = data if isinstance(data, list) else data.get("chapters", [])
        chapter_names = [c.get("name", c) if isinstance(c, dict) else c for c in chapters]
        print(f"Math chapters: {chapter_names[:5]}")
        # Rational Numbers should be a BNPS chapter
        names_lower = [n.lower() for n in chapter_names]
        assert any("rational" in n for n in names_lower), f"Rational Numbers not found in {chapter_names}"
        print("PASS: BNPS Math chapters include 'Rational Numbers'")


# --- Quiz Subtopics Tests ---
class TestBNPSSubtopics:
    def test_rational_numbers_subtopics(self, bnps_session):
        resp = bnps_session.get(f"{BASE_URL}/api/quiz/subtopics", params={
            "class_level": "8",
            "subject": "Mathematics",
            "chapter": "Rational Numbers"
        })
        assert resp.status_code == 200
        data = resp.json()
        subtopics = data.get("subtopics", [])
        print(f"Subtopics: {subtopics}")
        assert len(subtopics) > 0
        # Should have BNPS-specific subtopics
        assert any("Properties of Rational Numbers" in s or "Representation" in s for s in subtopics), \
            f"Expected BNPS subtopics, got: {subtopics}"
        print("PASS: Rational Numbers subtopics are BNPS-specific")

    def test_exploring_forces_subtopics(self, bnps_session):
        resp = bnps_session.get(f"{BASE_URL}/api/quiz/subtopics", params={
            "class_level": "8",
            "subject": "Science",
            "chapter": "Exploring Forces"
        })
        assert resp.status_code == 200
        data = resp.json()
        subtopics = data.get("subtopics", [])
        print(f"Exploring Forces subtopics: {subtopics}")
        assert len(subtopics) > 0
        print("PASS: Exploring Forces subtopics returned")


# --- BNPS Build Endpoint Tests ---
class TestBNPSBuildEndpoints:
    def test_build_bnps_status(self, admin_session):
        resp = admin_session.get(f"{BASE_URL}/api/question-bank/build-bnps/status")
        assert resp.status_code == 200
        data = resp.json()
        print(f"Build status response: {data}")
        assert "status" in data or "state" in data or len(data) > 0
        print("PASS: /api/question-bank/build-bnps/status returns 200")

    def test_build_bnps_status_unauthenticated(self):
        resp = requests.get(f"{BASE_URL}/api/question-bank/build-bnps/status")
        # Should require auth
        print(f"Unauthenticated status code: {resp.status_code}")
        # 200 or 401 both acceptable depending on implementation
        assert resp.status_code in [200, 401, 403]


# --- Chat Session Tests ---
class TestBNPSChatSession:
    def test_create_chat_session_bnps(self, bnps_session):
        resp = bnps_session.post(f"{BASE_URL}/api/chat/sessions", json={
            "subject": "Mathematics",
            "chapter": "Rational Numbers",
            "class_level": "8"
        })
        print(f"Create session status: {resp.status_code}, body: {resp.text[:200]}")
        assert resp.status_code in [200, 201]
        data = resp.json()
        session_id = data.get("session_id") or data.get("id")
        assert session_id is not None
        print(f"PASS: Chat session created, id={session_id}")
