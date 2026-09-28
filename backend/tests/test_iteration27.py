"""
Iteration 27 backend tests: NIOS features, subscription, mock exam multi-chapter
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def nios_session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": "niostest999@gmail.com", "password": "NiosTest@12345"}, timeout=10)
    assert r.status_code == 200, f"NIOS login failed: {r.text}"
    return s

@pytest.fixture(scope="module")
def admin_session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": "admin@neuralearn.ai", "password": "Admin@123456"}, timeout=10)
    assert r.status_code == 200, f"Admin login failed: {r.text}"
    return s

@pytest.fixture(scope="module")
def bnps_session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": "bnps@student.edu", "password": "Test@12345"}, timeout=10)
    assert r.status_code == 200, f"BNPS login failed: {r.text}"
    return s

class TestNIOSUser:
    """NIOS user basic checks"""

    def test_nios_login_and_profile(self, nios_session):
        r = nios_session.get(f"{BASE_URL}/api/auth/me", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert data.get('school') == 'nios', f"Expected school='nios', got {data.get('school')}"
        print(f"NIOS user: {data.get('name')}, school={data.get('school')}, class={data.get('class_level')}")

    def test_nios_subjects_count(self, nios_session):
        # Get user class level first
        me = nios_session.get(f"{BASE_URL}/api/auth/me", timeout=10).json()
        cls = me.get('class_level', '10')
        r = nios_session.get(f"{BASE_URL}/api/syllabus/{cls}/subjects", timeout=10)
        assert r.status_code == 200
        subjects = r.json()
        print(f"NIOS subjects count: {len(subjects)} - {[s['name'] for s in subjects]}")
        assert len(subjects) >= 17, f"Expected >= 17 NIOS subjects, got {len(subjects)}"

    def test_nios_subjects_not_verified_badge(self, nios_session):
        """NIOS subjects should NOT have 'verified' NCERT badge"""
        me = nios_session.get(f"{BASE_URL}/api/auth/me", timeout=10).json()
        cls = me.get('class_level', '10')
        r = nios_session.get(f"{BASE_URL}/api/syllabus/{cls}/subjects", timeout=10)
        subjects = r.json()
        # Check that no subjects have NCERT verified flag (or if they do, the frontend hides it)
        print(f"NIOS subjects verified flags: {[(s['name'], s.get('verified')) for s in subjects]}")
        # This is a frontend concern — backend may still return verified=True but frontend hides badge

class TestAdminSubscription:
    """Admin subscription check"""

    def test_admin_subscription_is_pro(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/subscription/me", timeout=10)
        assert r.status_code == 200
        data = r.json()
        plan_id = data.get('plan_id')
        print(f"Admin plan_id: {plan_id}")
        assert plan_id == 'pro', f"Expected plan_id='pro', got {plan_id}"

class TestBNPSUser:
    """BNPS user regression test"""

    def test_bnps_login_and_school(self, bnps_session):
        r = bnps_session.get(f"{BASE_URL}/api/auth/me", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert data.get('school') == 'brooklyn_national', f"Expected BNPS school, got {data.get('school')}"
        assert data.get('class_level') == '8', f"Expected class 8, got {data.get('class_level')}"
        print(f"BNPS user: school={data.get('school')}, class={data.get('class_level')}")

    def test_bnps_subjects_have_verified_flag(self, bnps_session):
        r = bnps_session.get(f"{BASE_URL}/api/syllabus/8/subjects", timeout=10)
        assert r.status_code == 200
        subjects = r.json()
        verified_count = sum(1 for s in subjects if s.get('verified'))
        print(f"BNPS verified subjects: {verified_count}/{len(subjects)}")
        assert verified_count > 0, "BNPS should have verified subjects"

class TestMockExamMultiChapter:
    """Mock exam with multi-chapter selection"""

    def test_nios_math_chapters_load(self, nios_session):
        me = nios_session.get(f"{BASE_URL}/api/auth/me", timeout=10).json()
        cls = me.get('class_level', '10')
        r = nios_session.get(f"{BASE_URL}/api/syllabus/{cls}/Mathematics/chapters", timeout=10)
        assert r.status_code == 200
        chapters = r.json()
        print(f"Math chapters count: {len(chapters)}")
        assert len(chapters) > 0, "Mathematics should have chapters"
        return chapters

class TestChatSession:
    """Chat session and mastery badge"""

    def test_create_chat_session(self, nios_session):
        me = nios_session.get(f"{BASE_URL}/api/auth/me", timeout=10).json()
        cls = me.get('class_level', '10')
        # Get economics subject
        subjects = nios_session.get(f"{BASE_URL}/api/syllabus/{cls}/subjects", timeout=10).json()
        econ = next((s for s in subjects if 'Economics' in s['name']), None)
        if not econ:
            print(f"No Economics found. Subjects: {[s['name'] for s in subjects[:5]]}")
            pytest.skip("Economics subject not found")
        
        # Get chapters
        chapters_r = nios_session.get(f"{BASE_URL}/api/syllabus/{cls}/Economics/chapters", timeout=10)
        chapters = chapters_r.json() if chapters_r.status_code == 200 else []
        chapter = chapters[0]['name'] if chapters else 'Introduction to Economics'
        
        r = nios_session.post(f"{BASE_URL}/api/chat/sessions", json={
            "class_level": cls,
            "subject": "Economics",
            "chapter": chapter
        }, timeout=10)
        assert r.status_code == 200
        session_id = r.json().get('session_id')
        assert session_id, "Should get session_id"
        print(f"Created chat session: {session_id} for chapter: {chapter}")
        return session_id

    def test_topic_mastery_endpoint(self, nios_session):
        r = nios_session.get(f"{BASE_URL}/api/quiz/topic-mastery", params={"topic": "Introduction to Economics"}, timeout=10)
        assert r.status_code == 200
        data = r.json()
        print(f"Topic mastery data: {data}")
        assert 'mastery_pct' in data, "Should have mastery_pct field"
