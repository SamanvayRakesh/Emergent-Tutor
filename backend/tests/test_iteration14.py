"""Iteration 14: School selection, BNPS curriculum, and auth tests."""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestSchoolsEndpoint:
    def test_schools_list_returns_two_schools(self):
        r = requests.get(f"{BASE_URL}/api/auth/schools")
        assert r.status_code == 200
        data = r.json()
        assert "schools" in data
        schools = data["schools"]
        assert len(schools) == 2

    def test_bnps_school_available(self):
        r = requests.get(f"{BASE_URL}/api/auth/schools")
        schools = r.json()["schools"]
        bnps = next((s for s in schools if s["id"] == "brooklyn_national"), None)
        assert bnps is not None
        assert bnps["available"] == True
        assert bnps["name"] == "Brooklyn National Public School"

    def test_nps_school_coming_soon(self):
        r = requests.get(f"{BASE_URL}/api/auth/schools")
        schools = r.json()["schools"]
        nps = next((s for s in schools if s["id"] == "national_public"), None)
        assert nps is not None
        assert nps["available"] == False


class TestAdminLogin:
    def test_admin_login_success(self):
        r = requests.post(f"{BASE_URL}/api/auth/login",
                          json={"email": "admin@neuralearn.ai", "password": "Admin@123456"})
        assert r.status_code == 200
        data = r.json()
        assert data["email"] == "admin@neuralearn.ai"


class TestBNPSStudent:
    """Tests for BNPS student login and school-specific syllabus"""

    @pytest.fixture(scope="class")
    def bnps_session(self):
        s = requests.Session()
        r = s.post(f"{BASE_URL}/api/auth/login",
                   json={"email": "bnps@student.edu", "password": "Test@12345"})
        assert r.status_code == 200, f"BNPS login failed: {r.text}"
        return s

    def test_bnps_login_success(self, bnps_session):
        r = bnps_session.get(f"{BASE_URL}/api/auth/me")
        assert r.status_code == 200
        data = r.json()
        assert data["email"] == "bnps@student.edu"
        assert data.get("school") == "brooklyn_national"

    def test_bnps_grade8_subjects_count(self, bnps_session):
        r = bnps_session.get(f"{BASE_URL}/api/syllabus/8/subjects")
        assert r.status_code == 200
        subjects = r.json()
        assert len(subjects) == 4, f"Expected 4 subjects, got {len(subjects)}: {[s['name'] for s in subjects]}"

    def test_bnps_grade8_subjects_names(self, bnps_session):
        r = bnps_session.get(f"{BASE_URL}/api/syllabus/8/subjects")
        names = [s["name"] for s in r.json()]
        assert "Mathematics" in names
        assert "Science" in names
        assert "Social Studies" in names
        assert "English" in names
        assert "Social Science" not in names, "Should NOT have 'Social Science'"

    def test_bnps_grade8_science_13_chapters(self, bnps_session):
        r = bnps_session.get(f"{BASE_URL}/api/syllabus/8/Science/chapters")
        assert r.status_code == 200
        chapters = r.json()
        assert len(chapters) == 13, f"Expected 13 chapters, got {len(chapters)}"
        assert chapters[0]["name"] == "Exploring the Investigative World of Science"

    def test_bnps_grade8_maths_16_chapters(self, bnps_session):
        r = bnps_session.get(f"{BASE_URL}/api/syllabus/8/Mathematics/chapters")
        assert r.status_code == 200
        chapters = r.json()
        assert len(chapters) == 16, f"Expected 16 chapters, got {len(chapters)}"
        assert chapters[0]["name"] == "Rational Numbers"

    def test_bnps_grade8_english_chapters(self, bnps_session):
        r = bnps_session.get(f"{BASE_URL}/api/syllabus/8/English/chapters")
        assert r.status_code == 200
        chapters = r.json()
        names = [c["name"] for c in chapters]
        assert "The Time Machine" in names
        assert "Stopping by Woods on a Snowy Evening" in names

    def test_bnps_grade8_sst_7_chapters(self, bnps_session):
        r = bnps_session.get(f"{BASE_URL}/api/syllabus/8/Social Studies/chapters")
        assert r.status_code == 200
        chapters = r.json()
        assert len(chapters) == 7, f"Expected 7 chapters, got {len(chapters)}"
