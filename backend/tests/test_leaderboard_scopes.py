"""Tests for new leaderboard scope param (global|class|friends)."""
import os
import uuid
import pytest
import requests

BASE_URL = (os.environ.get('REACT_APP_BACKEND_URL') or open(os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', '.env')).read().split('REACT_APP_BACKEND_URL=')[1].splitlines()[0].strip()).rstrip('/')
API = f"{BASE_URL}/api"


# ---------- Fixtures ----------
@pytest.fixture(scope="module")
def fresh_student():
    s = requests.Session()
    email = f"TEST_lb_{uuid.uuid4().hex[:8]}@neuralearn.ai"
    r = s.post(f"{API}/auth/register", json={"email": email, "password": "Test@1234567", "name": "LB Tester", "class_level": "11"}, timeout=30)
    assert r.status_code == 200, r.text
    return s


@pytest.fixture(scope="module")
def admin_session():
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": "admin@neuralearn.ai", "password": "Admin@123456"}, timeout=30)
    assert r.status_code == 200, f"admin login failed: {r.text}"
    return s


# ---------- Global scope (default) ----------
def test_global_scope_default_unauth():
    """No scope param defaults to global, accessible unauthenticated."""
    r = requests.get(f"{API}/leaderboard", timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert data["scope"] == "global"
    assert "leaderboard" in data and isinstance(data["leaderboard"], list)


def test_global_scope_explicit(fresh_student):
    r = fresh_student.get(f"{API}/leaderboard?scope=global", timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert data["scope"] == "global"
    assert data["class_level"] is None


# ---------- Class scope ----------
def test_class_scope_requires_auth():
    r = requests.get(f"{API}/leaderboard?scope=class", timeout=15)
    assert r.status_code == 401


def test_class_scope_returns_same_class(fresh_student):
    r = fresh_student.get(f"{API}/leaderboard?scope=class", timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert data["scope"] == "class"
    assert data["class_level"] == "11"  # what we registered with
    # All entries should have class_level == 11
    for e in data["leaderboard"]:
        assert str(e["class_level"]) == "11", f"got class_level={e['class_level']}"


def test_class_scope_admin(admin_session):
    r = admin_session.get(f"{API}/leaderboard?scope=class", timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert data["scope"] == "class"
    # Admin is class_level 12 per problem statement
    assert str(data["class_level"]) == "12"


# ---------- Friends scope ----------
def test_friends_scope_requires_auth():
    r = requests.get(f"{API}/leaderboard?scope=friends", timeout=15)
    assert r.status_code == 401


def test_friends_scope_brand_new_user_returns_self(fresh_student):
    """Fresh user with no referrals — leaderboard contains just themselves."""
    r = fresh_student.get(f"{API}/leaderboard?scope=friends", timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert data["scope"] == "friends"
    assert data["total_users"] >= 1
    user_ids = [e["user_id"] for e in data["leaderboard"]]
    # Get my user_id
    me = fresh_student.get(f"{API}/auth/me", timeout=10).json()
    assert me["user_id"] in user_ids


def test_friends_scope_includes_referral_graph():
    """After A refers B, friends leaderboard for A includes B AND vice versa (bidirectional)."""
    # A
    sa = requests.Session()
    ea = f"TEST_lb_a_{uuid.uuid4().hex[:8]}@neuralearn.ai"
    sa.post(f"{API}/auth/register", json={"email": ea, "password": "Test@1234567", "name": "A"}, timeout=30)
    code_a = sa.get(f"{API}/referral/code", timeout=10).json()["code"]
    me_a = sa.get(f"{API}/auth/me", timeout=10).json()["user_id"]
    # B applies A's code
    sb = requests.Session()
    eb = f"TEST_lb_b_{uuid.uuid4().hex[:8]}@neuralearn.ai"
    sb.post(f"{API}/auth/register", json={"email": eb, "password": "Test@1234567", "name": "B"}, timeout=30)
    apply = sb.post(f"{API}/referral/apply", json={"code": code_a}, timeout=10)
    assert apply.status_code == 200
    me_b = sb.get(f"{API}/auth/me", timeout=10).json()["user_id"]
    # A's friends leaderboard
    ra = sa.get(f"{API}/leaderboard?scope=friends", timeout=15).json()
    ids_a = {e["user_id"] for e in ra["leaderboard"]}
    assert me_a in ids_a and me_b in ids_a, f"A's friends: {ids_a}"
    # B's friends leaderboard (bidirectional)
    rb = sb.get(f"{API}/leaderboard?scope=friends", timeout=15).json()
    ids_b = {e["user_id"] for e in rb["leaderboard"]}
    assert me_a in ids_b and me_b in ids_b, f"B's friends: {ids_b}"


# ---------- Validation ----------
def test_invalid_scope_returns_422():
    r = requests.get(f"{API}/leaderboard?scope=foo", timeout=10)
    assert r.status_code == 422
