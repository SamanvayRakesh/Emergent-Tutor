"""Iteration 16: Test new auth (no email verification), password validation, admin endpoints"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# ── Registration & Password Validation ──────────────────────────────────────

class TestRegistration:
    """Test new registration flow (no email verification required)"""

    def test_register_weak_password_too_short(self):
        """Password under 6 chars should return 422"""
        resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"test_{uuid.uuid4().hex[:8]}@gmail.com",
            "name": "Test User",
            "password": "abc",
            "class_level": "9"
        })
        assert resp.status_code == 422, f"Expected 422 for short pw, got {resp.status_code}: {resp.text}"
        data = resp.json()
        detail = data.get("detail", "")
        assert "6" in str(detail).lower() or "character" in str(detail).lower(), f"Expected length error: {detail}"
        print("PASS: Short password (abc) rejected with 422")

    def test_register_no_special_char(self):
        """Password without special char should return 422"""
        resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"test_{uuid.uuid4().hex[:8]}@gmail.com",
            "name": "Test User",
            "password": "abcdefgh",
            "class_level": "9"
        })
        assert resp.status_code == 422, f"Expected 422 for no special char, got {resp.status_code}: {resp.text}"
        data = resp.json()
        detail = data.get("detail", "")
        assert "special" in str(detail).lower(), f"Expected special char error: {detail}"
        print("PASS: No special character password (abcdefgh) rejected with 422")

    def test_register_valid_user_no_verification(self):
        """Valid registration should succeed immediately (no email verification)"""
        email = f"TEST_newuser_{uuid.uuid4().hex[:8]}@gmail.com"
        resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": email,
            "name": "Test New User",
            "password": "Hello@123",
            "class_level": "9"
        }, allow_redirects=True)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        # Should be verified immediately
        assert data.get("is_verified") == True, f"Expected is_verified=True, got: {data.get('is_verified')}"
        assert data.get("email_verified") == True, f"Expected email_verified=True, got: {data.get('email_verified')}"
        assert data.get("status") == "active", f"Expected status=active, got: {data.get('status')}"
        # Should NOT require verification
        assert data.get("requires_verification") != True, f"Should not require verification: {data}"
        print(f"PASS: User {email} registered immediately without verification")
        return email

    def test_register_sets_auth_cookies(self):
        """Registration should set auth cookies"""
        email = f"TEST_cookie_{uuid.uuid4().hex[:8]}@gmail.com"
        session = requests.Session()
        resp = session.post(f"{BASE_URL}/api/auth/register", json={
            "email": email,
            "name": "Cookie Test",
            "password": "Hello@123",
            "class_level": "9"
        })
        assert resp.status_code == 200
        # Check cookies exist in session or response
        cookies = session.cookies
        has_auth_cookie = 'access_token' in cookies or 'access_token' in resp.cookies
        print(f"PASS: Registration cookies present: {has_auth_cookie}")
        print(f"  Response cookies: {dict(resp.cookies)}")
        print(f"  Session cookies: {dict(session.cookies)}")


class TestAdminEndpoints:
    """Test admin API endpoints"""

    @pytest.fixture
    def admin_session(self):
        session = requests.Session()
        resp = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@neuralearn.ai",
            "password": "Admin@123456"
        })
        assert resp.status_code == 200, f"Admin login failed: {resp.status_code}: {resp.text}"
        return session

    def test_admin_login(self):
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@neuralearn.ai",
            "password": "Admin@123456"
        })
        assert resp.status_code == 200, f"Admin login failed: {resp.text}"
        data = resp.json()
        assert data.get("role") == "admin", f"Expected role=admin, got: {data.get('role')}"
        print(f"PASS: Admin login successful, role={data.get('role')}")

    def test_admin_earnings(self, admin_session):
        resp = admin_session.get(f"{BASE_URL}/api/admin/earnings")
        assert resp.status_code == 200, f"Earnings failed: {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "total_users" in data
        assert "plan_distribution" in data
        assert "estimated_mrr_inr" in data
        print(f"PASS: Earnings data: total_users={data['total_users']}, MRR={data['estimated_mrr_inr']}")

    def test_admin_leaderboard_users(self, admin_session):
        resp = admin_session.get(f"{BASE_URL}/api/admin/leaderboard/users")
        assert resp.status_code == 200, f"Leaderboard users failed: {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "users" in data
        assert isinstance(data["users"], list)
        print(f"PASS: Leaderboard users: {data['total']} users")

    def test_admin_grade_requests(self, admin_session):
        resp = admin_session.get(f"{BASE_URL}/api/admin/grade-requests")
        assert resp.status_code == 200, f"Grade requests failed: {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "requests" in data
        print(f"PASS: Grade requests: {data['total']} requests")

    def test_non_admin_blocked(self):
        """Regular user should get 403 on admin endpoints"""
        session = requests.Session()
        resp = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "bnps@student.edu",
            "password": "Test@12345"
        })
        assert resp.status_code == 200
        resp2 = session.get(f"{BASE_URL}/api/admin/earnings")
        assert resp2.status_code == 403, f"Expected 403, got {resp2.status_code}"
        print("PASS: Non-admin blocked from admin endpoints")
