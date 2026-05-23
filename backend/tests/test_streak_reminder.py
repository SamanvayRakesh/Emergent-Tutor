"""Tests for new GET /api/streak-reminder endpoint."""
import os
import uuid
import pytest
import requests

BASE_URL = (os.environ.get('REACT_APP_BACKEND_URL') or open(os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', '.env')).read().split('REACT_APP_BACKEND_URL=')[1].splitlines()[0].strip()).rstrip('/')
API = f"{BASE_URL}/api"


REQUIRED_KEYS = {"streak", "longest_streak", "hours_since_active", "active_today", "at_risk", "broken", "days_to_exam", "message", "cta"}


@pytest.fixture(scope="module")
def admin_session():
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": "admin@neuralearn.ai", "password": "Admin@123456"}, timeout=30)
    assert r.status_code == 200, r.text
    return s


@pytest.fixture(scope="module")
def fresh_student():
    s = requests.Session()
    email = f"TEST_sr_{uuid.uuid4().hex[:8]}@neuralearn.ai"
    r = s.post(f"{API}/auth/register", json={"email": email, "password": "Test@1234567", "name": "Streak Tester"}, timeout=30)
    assert r.status_code == 200, r.text
    return s


def test_streak_reminder_requires_auth():
    r = requests.get(f"{API}/streak-reminder", timeout=10)
    assert r.status_code == 401


def test_streak_reminder_admin_active(admin_session):
    """Admin has 30-day streak per seed; should be active_today (login just happened)."""
    r = admin_session.get(f"{API}/streak-reminder", timeout=15)
    assert r.status_code == 200, r.text
    data = r.json()
    assert REQUIRED_KEYS.issubset(set(data.keys())), f"missing keys: {REQUIRED_KEYS - set(data.keys())}"
    assert data["active_today"] is True
    assert data["at_risk"] is False
    assert data["broken"] is False
    assert data["streak"] == 30, f"expected streak=30, got {data['streak']}"
    # Message should reference 30 (or be fire/streak-themed)
    assert "30" in data["message"] or "streak" in data["message"].lower()


def test_streak_reminder_fresh_user(fresh_student):
    """Brand-new user — registered moments ago, no streak yet."""
    r = fresh_student.get(f"{API}/streak-reminder", timeout=15)
    assert r.status_code == 200, r.text
    data = r.json()
    assert REQUIRED_KEYS.issubset(set(data.keys()))
    assert data["active_today"] is True  # just registered = very recent last_active
    assert data["at_risk"] is False
    # Fresh user: streak could be 0 or 1 depending on registration flow
    assert data["streak"] in (0, 1), f"expected streak 0 or 1, got {data['streak']}"
    # Should not be a "broken" message
    assert data["broken"] is False
    # Message should exist and not be empty
    assert isinstance(data["message"], str) and len(data["message"]) > 5
    assert isinstance(data["cta"], str) and len(data["cta"]) > 0
