"""Iteration 13 backend tests: subtopics endpoint, subscription plans, curriculum status."""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Admin credentials
ADMIN_EMAIL = "admin@neuralearn.ai"
ADMIN_PASSWORD = "Admin@123456"


@pytest.fixture(scope="module")
def auth_token():
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.cookies


def test_curriculum_status():
    """GET /api/curriculum/status returns 200"""
    r = requests.get(f"{BASE_URL}/api/curriculum/status")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    print("PASS: /api/curriculum/status returns 200")


def test_subtopics_real_numbers(auth_token):
    """GET /api/quiz/subtopics for Real Numbers returns correct subtopics"""
    r = requests.get(
        f"{BASE_URL}/api/quiz/subtopics",
        params={"class_level": "10", "subject": "Mathematics", "chapter": "Real Numbers"},
        cookies=auth_token,
    )
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    data = r.json()
    subs = data.get("subtopics", [])
    assert "Euclid's Division Lemma" in subs, f"Expected 'Euclid's Division Lemma' in {subs}"
    assert "Fundamental Theorem of Arithmetic" in subs, f"Missing FTA in {subs}"
    assert "Irrational Numbers" in subs
    assert "Rational Numbers & Decimals" in subs
    print(f"PASS: subtopics for Real Numbers: {subs}")


def test_subtopics_fallback(auth_token):
    """GET /api/quiz/subtopics for unknown chapter returns fallback options"""
    r = requests.get(
        f"{BASE_URL}/api/quiz/subtopics",
        params={"class_level": "10", "subject": "Mathematics", "chapter": "Unknown Chapter XYZ"},
        cookies=auth_token,
    )
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    data = r.json()
    subs = data.get("subtopics", [])
    assert any("Introduction & Concepts" in s for s in subs), f"Expected fallback in {subs}"
    print(f"PASS: fallback subtopics: {subs}")


def test_subscription_plans_starter_highlights():
    """Starter plan should have exactly 7 highlights, no '5 mock exams / week'"""
    r = requests.get(f"{BASE_URL}/api/subscription/plans")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    data = r.json()
    plans = data if isinstance(data, list) else data.get("plans", [])
    starter = next((p for p in plans if p.get("id") == "starter"), None)
    assert starter is not None, "Starter plan not found"
    highlights = starter.get("highlights", [])
    print(f"Starter highlights ({len(highlights)}): {highlights}")
    assert len(highlights) == 7, f"Expected 7 highlights, got {len(highlights)}: {highlights}"
    assert "5 mock exams / week" not in highlights, f"'5 mock exams / week' should not be in highlights"
    print("PASS: Starter plan has 7 highlights, no '5 mock exams / week'")


def test_subscription_plans_pro_highlights():
    """Pro plan should have exactly 6 highlights"""
    r = requests.get(f"{BASE_URL}/api/subscription/plans")
    assert r.status_code == 200
    data = r.json()
    plans = data if isinstance(data, list) else data.get("plans", [])
    pro = next((p for p in plans if p.get("id") == "pro"), None)
    assert pro is not None, "Pro plan not found"
    highlights = pro.get("highlights", [])
    print(f"Pro highlights ({len(highlights)}): {highlights}")
    assert len(highlights) == 6, f"Expected 6 highlights, got {len(highlights)}: {highlights}"
    print("PASS: Pro plan has 6 highlights")
