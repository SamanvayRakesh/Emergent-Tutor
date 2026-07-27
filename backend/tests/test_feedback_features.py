"""Tests for new features: feedback, tutorial, admin feedback tab"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

ADMIN_EMAIL = "admin@neuralearn.ai"
ADMIN_PASS = "Admin@123456"


@pytest.fixture(scope="module")
def admin_session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
    assert r.status_code == 200, f"Admin login failed: {r.text}"
    return s


class TestFeedbackAPI:
    """Feedback submission and admin retrieval"""

    def test_submit_feedback_unauthenticated(self):
        r = requests.post(f"{BASE_URL}/api/feedback", json={"type": "general", "message": "hello world"})
        assert r.status_code in [401, 403]

    def test_submit_feedback_short_message(self, admin_session):
        r = admin_session.post(f"{BASE_URL}/api/feedback", json={"type": "general", "message": "hi"})
        assert r.status_code == 400

    def test_submit_feedback_success(self, admin_session):
        r = admin_session.post(f"{BASE_URL}/api/feedback", json={"type": "bug", "message": "TEST_ This is a test bug report"})
        assert r.status_code == 200
        data = r.json()
        assert data.get("success") is True

    def test_admin_get_feedback(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/admin/feedback")
        assert r.status_code == 200
        data = r.json()
        assert "feedback" in data
        assert isinstance(data["feedback"], list)

    def test_admin_feedback_has_items(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/admin/feedback")
        data = r.json()
        # At least 1 item from above test
        assert data["total"] >= 1

    def test_admin_resolve_feedback(self, admin_session):
        # Get first open feedback
        r = admin_session.get(f"{BASE_URL}/api/admin/feedback")
        items = r.json()["feedback"]
        open_items = [i for i in items if i.get("status") == "open"]
        if not open_items:
            pytest.skip("No open feedback to resolve")
        fb_id = open_items[0]["feedback_id"]
        r2 = admin_session.patch(f"{BASE_URL}/api/admin/feedback/{fb_id}/resolve")
        assert r2.status_code == 200
        assert r2.json().get("success") is True


class TestTutorialAPI:
    """Tutorial seen flag"""

    def test_admin_tutorial_seen_flag(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/auth/me")
        assert r.status_code == 200
        user = r.json()
        # Admin is existing user - should have is_tutorial_seen=True
        assert user.get("is_tutorial_seen") is True, f"Admin should have is_tutorial_seen=True, got: {user.get('is_tutorial_seen')}"

    def test_tutorial_seen_endpoint(self, admin_session):
        r = admin_session.patch(f"{BASE_URL}/api/auth/tutorial/seen")
        assert r.status_code == 200
