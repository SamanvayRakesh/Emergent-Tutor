"""Admin earnings, leaderboard, grade-requests, feedback endpoint tests."""
import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

ADMIN_CREDS = {"email": "truecursemahito28@gmail.com", "password": "Samanvay@247"}
FALLBACK_CREDS = {"email": "admin@neuralearn.ai", "password": "Admin@123456"}


@pytest.fixture(scope="module")
def admin_client():
    session = requests.Session()
    r = session.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
    if r.status_code != 200:
        r = session.post(f"{BASE_URL}/api/auth/login", json=FALLBACK_CREDS)
    if r.status_code != 200:
        pytest.skip(f"Admin login failed: {r.text[:200]}")
    # Extract token from response and set as cookie + bearer
    data = r.json()
    token = data.get("access_token") or data.get("token")
    if token:
        session.cookies.set("access_token", token)
        session.headers.update({"Authorization": f"Bearer {token}"})
    print(f"Login status: {r.status_code}, token present: {bool(token)}")
    return session


class TestAdminEarnings:
    """Earnings endpoint tests"""

    def test_earnings_status_200(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/admin/earnings")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:200]}"

    def test_earnings_top_level_keys(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/admin/earnings")
        data = r.json()
        for key in ["total_users", "total_paid_users", "total_revenue_inr", "mrr_inr",
                    "plan_distribution", "active_subscriptions", "cancelled_subscriptions",
                    "recent_payments", "monthly_revenue", "paid_users"]:
            assert key in data, f"Missing key: {key}"
        print(f"Earnings: total_users={data['total_users']}, paid={data['total_paid_users']}, MRR={data['mrr_inr']}, revenue={data['total_revenue_inr']}")

    def test_earnings_mrr_calculation(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/admin/earnings")
        data = r.json()
        active_subs = data["active_subscriptions"]
        expected_mrr = active_subs.get("starter", 0) * 399 + active_subs.get("pro", 0) * 699
        assert data["mrr_inr"] == expected_mrr, f"MRR mismatch: expected {expected_mrr}, got {data['mrr_inr']}"
        print(f"MRR check: starter={active_subs.get('starter')}, pro={active_subs.get('pro')}, mrr={data['mrr_inr']}")

    def test_earnings_plan_distribution_keys(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/admin/earnings")
        data = r.json()
        dist = data["plan_distribution"]
        assert "free" in dist and "starter" in dist and "pro" in dist

    def test_earnings_paid_users_fields(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/admin/earnings")
        data = r.json()
        paid = data["paid_users"]
        print(f"Paid users count: {len(paid)}")
        for u in paid:
            assert "name" in u
            assert "email" in u
            assert "plan" in u
            assert "status" in u
            assert "expires_at" in u

    def test_earnings_recent_payments_fields(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/admin/earnings")
        data = r.json()
        payments = data["recent_payments"]
        print(f"Recent payments count: {len(payments)}")
        for p in payments:
            assert "txnid" in p
            assert "amount" in p
            assert "plan" in p


class TestAdminLeaderboard:
    """Leaderboard admin endpoint tests"""

    def test_leaderboard_users_status(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/admin/leaderboard/users")
        assert r.status_code == 200
        data = r.json()
        assert "users" in data and "total" in data
        print(f"Leaderboard users: {data['total']}")


class TestAdminGradeRequests:
    """Grade requests endpoint tests"""

    def test_grade_requests_status(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/admin/grade-requests")
        assert r.status_code == 200
        data = r.json()
        assert "requests" in data
        print(f"Grade requests: {data['total']}")
