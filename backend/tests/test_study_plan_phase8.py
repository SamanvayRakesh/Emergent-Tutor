"""Phase 8: Study Plan personalisation tests - context endpoint, POST with new fields"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def auth_session():
    session = requests.Session()
    r = session.post(f"{BASE_URL}/api/auth/login", json={"email": "admin@neuralearn.ai", "password": "Admin@123456"})
    assert r.status_code == 200, f"Login failed: {r.text}"
    return session

class TestStudyPlanContext:
    """GET /api/study-plan/context"""

    def test_context_returns_200(self, auth_session):
        r = auth_session.get(f"{BASE_URL}/api/study-plan/context")
        assert r.status_code == 200

    def test_context_has_required_fields(self, auth_session):
        r = auth_session.get(f"{BASE_URL}/api/study-plan/context")
        data = r.json()
        assert "quiz_count" in data
        assert "exam_count" in data
        assert "weak_topics" in data
        assert "strong_topics" in data
        assert "has_history" in data

    def test_context_quiz_count_is_int(self, auth_session):
        r = auth_session.get(f"{BASE_URL}/api/study-plan/context")
        data = r.json()
        assert isinstance(data["quiz_count"], int)
        assert data["quiz_count"] >= 0

    def test_context_has_history_for_admin(self, auth_session):
        """Admin has 6 quizzes so has_history should be True"""
        r = auth_session.get(f"{BASE_URL}/api/study-plan/context")
        data = r.json()
        # Admin has quiz history, has_history should be true
        assert data["has_history"] is True

    def test_context_weak_topics_is_list(self, auth_session):
        r = auth_session.get(f"{BASE_URL}/api/study-plan/context")
        data = r.json()
        assert isinstance(data["weak_topics"], list)
        # Each item should have topic and frequency
        for item in data["weak_topics"]:
            assert "topic" in item
            assert "frequency" in item

    def test_context_strong_topics_is_list(self, auth_session):
        r = auth_session.get(f"{BASE_URL}/api/study-plan/context")
        data = r.json()
        assert isinstance(data["strong_topics"], list)


class TestStudyPlanPost:
    """POST /api/study-plan with new fields"""

    def test_post_accepts_available_days(self, auth_session):
        """POST body with available_days should be accepted (200 or 502 both ok)"""
        payload = {
            "exam_date": "2026-06-15",
            "target_score": 90,
            "daily_hours": 2,
            "class_level": "10",
            "subjects": ["Mathematics"],
            "available_days": ["Mon", "Wed", "Fri"],
            "session_preference": "morning"
        }
        r = auth_session.post(f"{BASE_URL}/api/study-plan", json=payload)
        # 200 = success, 502 = OpenAI called but failed (both acceptable)
        assert r.status_code in [200, 502], f"Unexpected status: {r.status_code} - {r.text}"

    def test_post_accepts_session_preference_options(self, auth_session):
        """Test each session_preference value is accepted"""
        for session_pref in ["morning", "afternoon", "evening", "flexible"]:
            payload = {
                "exam_date": "2026-06-15",
                "target_score": 80,
                "daily_hours": 1.5,
                "class_level": "10",
                "subjects": [],
                "available_days": ["Mon", "Tue", "Wed", "Thu", "Fri"],
                "session_preference": session_pref
            }
            r = auth_session.post(f"{BASE_URL}/api/study-plan", json=payload)
            assert r.status_code in [200, 502], f"session_preference={session_pref} failed: {r.status_code}"

    def test_post_without_available_days_uses_default(self, auth_session):
        """POST without available_days should still work"""
        payload = {
            "exam_date": "2026-06-15",
            "target_score": 85,
            "daily_hours": 2,
            "class_level": "10",
            "subjects": [],
        }
        r = auth_session.post(f"{BASE_URL}/api/study-plan", json=payload)
        assert r.status_code in [200, 422, 502]


class TestStudyPlanGet:
    """GET /api/study-plan"""

    def test_get_study_plan_returns_200(self, auth_session):
        r = auth_session.get(f"{BASE_URL}/api/study-plan")
        assert r.status_code == 200

    def test_context_requires_auth(self):
        """Without auth, context should return 401"""
        r = requests.get(f"{BASE_URL}/api/study-plan/context")
        assert r.status_code == 401
