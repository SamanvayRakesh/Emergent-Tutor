"""Phase 6/7/10 backend tests: QuizArena topic-mastery, weak-areas, subscription cancel."""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    # Login
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": "admin@neuralearn.ai", "password": "Admin@123456"})
    assert r.status_code == 200, f"Login failed: {r.text}"
    return s

class TestTopicMastery:
    """GET /api/quiz/topic-mastery"""

    def test_topic_mastery_returns_valid_structure(self, session):
        r = session.get(f"{BASE_URL}/api/quiz/topic-mastery", params={"topic": "Photosynthesis"})
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert "topic" in data
        assert "mastery" in data
        assert "mastery_pct" in data
        assert "recommended_difficulty" in data
        assert "attempts" in data
        assert data["recommended_difficulty"] in ["easy", "medium", "hard"]
        print(f"PASS: topic-mastery returns valid structure: {data}")

    def test_topic_mastery_recommended_difficulty_consistent(self, session):
        r = session.get(f"{BASE_URL}/api/quiz/topic-mastery", params={"topic": "Newton's Laws"})
        assert r.status_code == 200
        data = r.json()
        mastery = data["mastery"]
        rec = data["recommended_difficulty"]
        if mastery < 0.4:
            assert rec == "easy"
        elif mastery < 0.7:
            assert rec == "medium"
        else:
            assert rec == "hard"
        assert data["mastery_pct"] == int(mastery * 100)
        print(f"PASS: difficulty consistent with mastery: {mastery} -> {rec}")

    def test_topic_mastery_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/quiz/topic-mastery", params={"topic": "Test"})
        assert r.status_code in [401, 403], f"Expected 401/403 for unauthenticated, got {r.status_code}"
        print(f"PASS: topic-mastery requires auth, got {r.status_code}")


class TestWeakAreas:
    """GET /api/weak-areas"""

    def test_weak_areas_returns_valid_structure(self, session):
        r = session.get(f"{BASE_URL}/api/weak-areas")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert "weak_topics" in data
        assert "adaptive_weak" in data
        assert "exam_count" in data
        assert isinstance(data["weak_topics"], list)
        assert isinstance(data["adaptive_weak"], list)
        print(f"PASS: weak-areas returns valid structure: exam_count={data['exam_count']}")

    def test_weak_areas_topic_has_frequency(self, session):
        r = session.get(f"{BASE_URL}/api/weak-areas")
        assert r.status_code == 200
        data = r.json()
        for item in data["weak_topics"]:
            assert "topic" in item
            assert "frequency" in item
        print("PASS: weak_topics items have topic and frequency fields")

    def test_weak_areas_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/weak-areas")
        assert r.status_code in [401, 403], f"Expected 401/403 for unauthenticated, got {r.status_code}"
        print(f"PASS: weak-areas requires auth, got {r.status_code}")


class TestSubscriptionCancel:
    """POST /api/subscription/cancel"""

    def test_subscription_cancel_free_user_returns_error_or_200(self, session):
        # Admin is free plan, cancel should return 400 or a graceful response
        r = session.post(f"{BASE_URL}/api/subscription/cancel", json={})
        # Should be 400 (no active subscription) or 200
        assert r.status_code in [200, 400, 404], f"Unexpected status: {r.status_code}: {r.text}"
        print(f"PASS: subscription/cancel returned {r.status_code}: {r.json()}")

    def test_subscription_cancel_requires_auth(self):
        r = requests.post(f"{BASE_URL}/api/subscription/cancel", json={})
        assert r.status_code in [401, 403], f"Expected 401/403 for unauthenticated, got {r.status_code}"
        print(f"PASS: cancel requires auth, got {r.status_code}")


class TestSyllabusForQuizArena:
    """GET /api/syllabus/{class}/subjects for quiz setup"""

    def test_subjects_returns_list(self, session):
        r = session.get(f"{BASE_URL}/api/syllabus/12/subjects")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "name" in data[0]
        print(f"PASS: Class 12 subjects returned {len(data)} items: {[s['name'] for s in data[:3]]}")

    def test_chapters_returns_list(self, session):
        # Get first subject
        r = session.get(f"{BASE_URL}/api/syllabus/12/subjects")
        subjects = r.json()
        if not subjects:
            pytest.skip("No subjects available")
        first_subject = subjects[0]["name"]
        r2 = session.get(f"{BASE_URL}/api/syllabus/12/subjects/{requests.utils.quote(first_subject)}/chapters")
        assert r2.status_code == 200, f"Expected 200, got {r2.status_code}: {r2.text}"
        data = r2.json()
        chapters = data if isinstance(data, list) else data.get("chapters", [])
        assert isinstance(chapters, list)
        print(f"PASS: Chapters for {first_subject}: {len(chapters)} chapters")
