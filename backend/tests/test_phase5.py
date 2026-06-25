"""Phase 1-5 feature tests: leaderboard filtering, study plan lock, quiz topic fix, ai_router tokens."""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Admin credentials (has onboarding completed)
ADMIN_EMAIL = "admin@neuralearn.ai"
ADMIN_PWD = "Admin@123456"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PWD})
    assert r.status_code == 200, f"Admin login failed: {r.text}"
    cookies = r.cookies
    return cookies


class TestLeaderboard:
    """Leaderboard should exclude admin and test_* accounts."""

    def test_global_leaderboard_no_admin(self, admin_token):
        """Admin account (role=admin) should NOT appear in leaderboard by user_id."""
        # First get admin's user_id
        login_r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PWD})
        admin_user_id = login_r.json().get("user_id", "")
        
        r = requests.get(f"{BASE_URL}/api/leaderboard?scope=global", cookies=admin_token)
        assert r.status_code == 200
        data = r.json()
        entries = data.get("leaderboard", [])
        # Check admin user_id not in entries
        admin_entries = [e for e in entries if e.get("user_id") == admin_user_id]
        assert len(admin_entries) == 0, f"Admin user found in leaderboard by user_id: {admin_entries}"

    def test_global_leaderboard_returns_list(self, admin_token):
        r = requests.get(f"{BASE_URL}/api/leaderboard?scope=global", cookies=admin_token)
        assert r.status_code == 200
        data = r.json()
        assert "leaderboard" in data
        assert "scope" in data
        assert data["scope"] == "global"

    def test_leaderboard_unauthenticated(self):
        """Global leaderboard works without auth."""
        r = requests.get(f"{BASE_URL}/api/leaderboard?scope=global")
        assert r.status_code == 200

    def test_class_leaderboard_requires_auth(self):
        """Class leaderboard requires auth."""
        r = requests.get(f"{BASE_URL}/api/leaderboard?scope=class")
        assert r.status_code == 401

    def test_friends_leaderboard_requires_auth(self):
        """Friends leaderboard requires auth."""
        r = requests.get(f"{BASE_URL}/api/leaderboard?scope=friends")
        assert r.status_code == 401


class TestAIRouter:
    """Validate ai_router max_tokens config."""

    def test_category_c_normal_max_tokens(self):
        """Category C normal budget should be 1800 tokens."""
        import sys
        sys.path.insert(0, '/app/backend')
        from ai_router import build_routing_decision
        result = build_routing_decision("How does thermodynamics work step by step?", "pro", near_budget=False, critical=False, over_budget=False)
        assert result["category"] == "C"
        assert result["max_tokens"] == 1800, f"Expected 1800 but got {result['max_tokens']}"

    def test_category_b_normal_max_tokens(self):
        """Category B normal budget should be 800 tokens."""
        import sys
        sys.path.insert(0, '/app/backend')
        from ai_router import build_routing_decision
        result = build_routing_decision("define photosynthesis", "free", near_budget=False, critical=False, over_budget=False)
        assert result["category"] == "B"
        assert result["max_tokens"] == 800, f"Expected 800 but got {result['max_tokens']}"

    def test_category_c_near_budget_tokens(self):
        """Category C near budget = 600 tokens."""
        import sys
        sys.path.insert(0, '/app/backend')
        from ai_router import build_routing_decision
        result = build_routing_decision("explain thermodynamics derivation in depth", "pro", near_budget=True, critical=False)
        assert result["max_tokens"] == 600

    def test_over_budget_blocked(self):
        """Over budget requests should be blocked."""
        import sys
        sys.path.insert(0, '/app/backend')
        from ai_router import build_routing_decision
        result = build_routing_decision("anything", "free", over_budget=True)
        assert result["blocked"] is True


class TestStudyPlanAPI:
    """Study plan API - test it's accessible for admin."""

    def test_get_study_plan(self, admin_token):
        r = requests.get(f"{BASE_URL}/api/study-plan", cookies=admin_token)
        # Should return 200 (plan may or may not exist)
        assert r.status_code == 200

    def test_quiz_history_endpoint(self, admin_token):
        r = requests.get(f"{BASE_URL}/api/quiz/history", cookies=admin_token)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)


class TestProgressAPI:
    """Progress and gamification APIs."""

    def test_progress_endpoint(self, admin_token):
        r = requests.get(f"{BASE_URL}/api/progress", cookies=admin_token)
        assert r.status_code == 200
        data = r.json()
        assert "overall_mastery" in data or "subject_progress" in data

    def test_gamification_stats(self, admin_token):
        r = requests.get(f"{BASE_URL}/api/gamification/stats", cookies=admin_token)
        assert r.status_code == 200
        data = r.json()
        assert "xp" in data
        assert "streak" in data
        # Check longest_streak is present
        assert "longest_streak" in data
