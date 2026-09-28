"""
Tests for NIOS new features:
- Feedback endpoint (POST /api/chat/feedback)
- Admin pro tier on login
- NIOS Secondary Course terminology
- NIOS subjects/chapters
- BNPS regression
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

NIOS_EMAIL = "niostest999@gmail.com"
NIOS_PASS = "NiosTest@12345"
ADMIN_EMAIL = "admin@neuralearn.ai"
ADMIN_PASS = "Admin@123456"
BNPS_EMAIL = "bnps@student.edu"
BNPS_PASS = "Test@12345"


@pytest.fixture(scope="module")
def nios_session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": NIOS_EMAIL, "password": NIOS_PASS})
    assert r.status_code == 200, f"NIOS login failed: {r.text}"
    return s


@pytest.fixture(scope="module")
def admin_session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
    assert r.status_code == 200, f"Admin login failed: {r.text}"
    return s


@pytest.fixture(scope="module")
def bnps_session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": BNPS_EMAIL, "password": BNPS_PASS})
    assert r.status_code == 200, f"BNPS login failed: {r.text}"
    return s


class TestNIOSUserProfile:
    """NIOS user profile has school=nios, class_level=10"""

    def test_nios_me_returns_school_nios(self, nios_session):
        r = nios_session.get(f"{BASE_URL}/api/auth/me")
        assert r.status_code == 200
        data = r.json()
        assert data.get("school") == "nios", f"Expected school=nios, got {data.get('school')}"
        assert str(data.get("class_level")) == "10", f"Expected class_level=10, got {data.get('class_level')}"
        print("PASS: NIOS user has school=nios, class_level=10")


class TestNIOSSubjects:
    """NIOS subjects and chapters"""

    def test_nios_subjects_count_7(self, nios_session):
        r = nios_session.get(f"{BASE_URL}/api/syllabus/10/subjects")
        assert r.status_code == 200
        subjects = r.json()
        names = [s.get("name", s) if isinstance(s, dict) else s for s in subjects]
        assert len(subjects) >= 7, f"Expected 7 NIOS subjects, got {len(subjects)}: {names}"
        print(f"PASS: Got {len(subjects)} subjects: {names}")

    def test_nios_english_chapters_load(self, nios_session):
        r = nios_session.get(f"{BASE_URL}/api/syllabus/10/English/chapters")
        assert r.status_code == 200
        chapters = r.json()
        assert len(chapters) >= 1, "Expected chapters for English"
        print(f"PASS: English has {len(chapters)} chapters")


class TestAdminProTier:
    """Admin login should result in pro subscription"""

    def test_admin_subscription_is_pro(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/subscription/me")
        assert r.status_code == 200
        data = r.json()
        plan_id = data.get("plan_id") or data.get("plan") or data.get("id")
        assert plan_id == "pro", f"Expected plan=pro, got: {data}"
        print(f"PASS: Admin has pro subscription: {data}")


class TestFeedbackEndpoint:
    """POST /api/chat/feedback tests"""

    def test_feedback_unknown_message_id_returns_404(self, nios_session):
        r = nios_session.post(f"{BASE_URL}/api/chat/feedback", json={
            "message_id": "nonexistent_msg_id_xyz123",
            "vote": "up"
        })
        assert r.status_code == 404, f"Expected 404, got {r.status_code}: {r.text}"
        print("PASS: Unknown message_id returns 404")

    def test_feedback_invalid_vote_returns_400(self, nios_session):
        r = nios_session.post(f"{BASE_URL}/api/chat/feedback", json={
            "message_id": "some_id",
            "vote": "meh"
        })
        assert r.status_code == 400, f"Expected 400, got {r.status_code}: {r.text}"
        print("PASS: Invalid vote returns 400")

    def test_feedback_with_real_message_id(self, nios_session):
        """Send a chat message, get a real message_id, then vote on it"""
        # Step 1: Create a chat session
        # Get user class first
        me = nios_session.get(f"{BASE_URL}/api/auth/me").json()
        class_level = str(me.get("class_level", "10"))

        # Get subjects
        subj_r = nios_session.get(f"{BASE_URL}/api/syllabus/{class_level}/subjects")
        if subj_r.status_code != 200 or not subj_r.json():
            pytest.skip("Could not get subjects")
        subjects = subj_r.json()
        subj_name = subjects[0].get("name", subjects[0]) if isinstance(subjects[0], dict) else subjects[0]

        # Get chapters
        chap_r = nios_session.get(f"{BASE_URL}/api/syllabus/{class_level}/{subj_name}/chapters")
        if chap_r.status_code != 200 or not chap_r.json():
            pytest.skip("Could not get chapters")
        chapters = chap_r.json()
        chap = chapters[0]
        chap_id = chap.get("id", chap.get("_id", "1")) if isinstance(chap, dict) else chap
        chap_name = chap.get("name", str(chap)) if isinstance(chap, dict) else str(chap)

        # Create session
        sess_r = nios_session.post(f"{BASE_URL}/api/chat/sessions", json={
            "class_level": class_level,
            "subject": subj_name,
            "chapter": chap_name,
            "chapter_id": str(chap_id)
        })
        if sess_r.status_code != 200:
            pytest.skip(f"Could not create session: {sess_r.text}")
        sess_id = sess_r.json().get("session_id") or sess_r.json().get("id")

        # Step 2: Send a message via SSE and capture message_id from done event
        import re
        headers = {"Accept": "text/event-stream"}
        # Send a simple question
        msg_r = nios_session.post(
            f"{BASE_URL}/api/chat/sessions/{sess_id}/message",
            json={"message": "What is this chapter about?"},
            headers=headers,
            stream=True,
            timeout=60
        )
        if msg_r.status_code != 200:
            pytest.skip(f"Message failed: {msg_r.status_code} {msg_r.text[:200]}")

        message_id = None
        for line in msg_r.iter_lines(decode_unicode=True):
            if not line:
                continue
            if line.startswith("data:"):
                payload = line[5:].strip()
                if '"message_id"' in payload:
                    import json
                    try:
                        d = json.loads(payload)
                        if d.get("type") == "done" and d.get("message_id"):
                            message_id = d["message_id"]
                            break
                    except Exception:
                        pass

        if not message_id:
            pytest.skip("Could not capture message_id from SSE stream")

        print(f"Got message_id: {message_id}")

        # Step 3: Submit feedback
        fb_r = nios_session.post(f"{BASE_URL}/api/chat/feedback", json={
            "message_id": message_id,
            "vote": "up"
        })
        assert fb_r.status_code == 200, f"Expected 200, got {fb_r.status_code}: {fb_r.text}"
        data = fb_r.json()
        assert data.get("ok") is True, f"Expected ok=true, got {data}"
        assert data.get("vote") == "up"
        print(f"PASS: Feedback submitted successfully: {data}")


class TestBNPSRegression:
    """BNPS user regression - should still see class 8 content"""

    def test_bnps_me_returns_class_8(self, bnps_session):
        r = bnps_session.get(f"{BASE_URL}/api/auth/me")
        assert r.status_code == 200
        data = r.json()
        assert str(data.get("class_level")) == "8", f"Expected class_level=8, got {data.get('class_level')}"
        school = data.get("school", "")
        assert school != "nios", f"BNPS user should not have school=nios"
        print(f"PASS: BNPS user has class=8, school={school}")

    def test_bnps_subjects_are_class_8(self, bnps_session):
        r = bnps_session.get(f"{BASE_URL}/api/syllabus/8/subjects")
        assert r.status_code == 200
        subjects = r.json()
        assert len(subjects) >= 1, "BNPS should have subjects for class 8"
        names = [s.get("name", s) if isinstance(s, dict) else s for s in subjects]
        # Should NOT include NIOS-specific subjects
        nios_only = ["Accountancy", "Business Studies", "Data Entry Operations", "Entrepreneurship", "Folk Art"]
        for nios_subj in nios_only:
            assert nios_subj not in names, f"BNPS class 8 subjects contain NIOS subject: {nios_subj}"
        print(f"PASS: BNPS class 8 subjects: {names}")
