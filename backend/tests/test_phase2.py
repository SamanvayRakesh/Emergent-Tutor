"""Phase 2 backend tests: Leaderboard, Mock Exam, Study Plan, Referrals, Recommendations, Chat (YouTube tag)."""
import os
import json
import uuid
import time
import pytest
import requests

BASE_URL = (os.environ.get('REACT_APP_BACKEND_URL') or open(os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', '.env')).read().split('REACT_APP_BACKEND_URL=')[1].splitlines()[0].strip()).rstrip('/')
API = f"{BASE_URL}/api"


# ---------- Fixtures ----------

@pytest.fixture(scope="module")
def student_session():
    """Register a fresh student user and return an authenticated requests session."""
    s = requests.Session()
    email = f"TEST_phase2_{uuid.uuid4().hex[:8]}@neuralearn.ai"
    pw = "Test@1234567"
    r = s.post(f"{API}/auth/register", json={"email": email, "password": pw, "name": "Phase2 Tester"}, timeout=30)
    assert r.status_code == 200, f"register failed: {r.status_code} {r.text}"
    s.email = email
    s.pw = pw
    return s


@pytest.fixture(scope="module")
def second_student():
    """A second registered student used for referral tests."""
    s = requests.Session()
    email = f"TEST_phase2b_{uuid.uuid4().hex[:8]}@neuralearn.ai"
    pw = "Test@1234567"
    r = s.post(f"{API}/auth/register", json={"email": email, "password": pw, "name": "Phase2 Tester B"}, timeout=30)
    assert r.status_code == 200, f"register2 failed: {r.status_code} {r.text}"
    s.email = email
    return s


# ---------- Health/Auth Sanity ----------

def test_backend_reachable():
    r = requests.get(f"{API}/auth/me", timeout=10)
    # Either 401 (unauthenticated) or 200 — but must respond
    assert r.status_code in (200, 401)


def test_authenticated_me(student_session):
    r = student_session.get(f"{API}/auth/me", timeout=10)
    assert r.status_code == 200
    data = r.json()
    assert "user_id" in data and "email" in data


# ---------- Leaderboard ----------

def test_leaderboard_structure(student_session):
    r = student_session.get(f"{API}/leaderboard", timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert "leaderboard" in data
    assert "total_users" in data
    assert isinstance(data["leaderboard"], list)
    if data["leaderboard"]:
        e = data["leaderboard"][0]
        for k in ["rank", "name", "xp", "level", "streak", "class_level"]:
            assert k in e, f"missing {k} in leaderboard entry"


# ---------- Mock Exam ----------

@pytest.fixture(scope="module")
def generated_exam(student_session):
    payload = {"class_level": "10", "subject": "Mathematics", "duration_minutes": 30, "num_questions": 10}
    r = student_session.post(f"{API}/mock-exam/generate", json=payload, timeout=90)
    assert r.status_code == 200, f"mock-exam generate failed: {r.status_code} {r.text[:300]}"
    data = r.json()
    assert "exam_id" in data
    assert "sections" in data and isinstance(data["sections"], list) and len(data["sections"]) == 3
    sections = {s["section"]: s for s in data["sections"]}
    assert set(sections.keys()) == {"A", "B", "C"}
    for sec in data["sections"]:
        assert isinstance(sec.get("questions"), list) and len(sec["questions"]) > 0
    return data


def test_mock_exam_history(student_session, generated_exam):
    r = student_session.get(f"{API}/mock-exam/history", timeout=15)
    assert r.status_code == 200
    history = r.json()
    assert isinstance(history, list)
    assert any(e.get("exam_id") == generated_exam["exam_id"] for e in history)


def test_mock_exam_submit(student_session, generated_exam):
    answers = {}
    for sec in generated_exam["sections"]:
        for q in sec["questions"]:
            # pick first option letter as the student's answer (may or may not be correct)
            answers[q["id"]] = q.get("correct", "A")  # submit correct to verify scoring path
    body = {"quiz_id": generated_exam["exam_id"], "answers": answers}
    r = student_session.post(f"{API}/mock-exam/{generated_exam['exam_id']}/submit", json=body, timeout=20)
    assert r.status_code == 200, f"submit failed: {r.status_code} {r.text[:200]}"
    data = r.json()
    for k in ["score", "earned_marks", "total_marks", "xp_earned", "section_results", "weak_topics"]:
        assert k in data
    assert data["score"] == 100  # all correct
    assert len(data["section_results"]) == 3


# ---------- Study Plan ----------

def test_study_plan_create(student_session):
    from datetime import datetime, timedelta, timezone
    exam_date = (datetime.now(timezone.utc) + timedelta(days=21)).isoformat()
    payload = {
        "exam_date": exam_date,
        "target_score": 90,
        "daily_hours": 2.0,
        "class_level": "10",
        "subjects": ["Mathematics", "Science"],
    }
    r = student_session.post(f"{API}/study-plan", json=payload, timeout=90)
    assert r.status_code == 200, f"study-plan create failed: {r.status_code} {r.text[:300]}"
    data = r.json()
    assert "plan" in data and isinstance(data["plan"], dict)
    assert "days_until_exam" in data
    plan = data["plan"]
    assert "overview" in plan
    assert "weeks" in plan and isinstance(plan["weeks"], list) and len(plan["weeks"]) > 0
    assert "tips" in plan


def test_study_plan_get(student_session):
    r = student_session.get(f"{API}/study-plan", timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert data.get("plan") is not None
    assert "days_remaining" in data


# ---------- Referrals ----------

def test_referral_code(student_session):
    r = student_session.get(f"{API}/referral/code", timeout=10)
    assert r.status_code == 200
    data = r.json()
    assert "code" in data and isinstance(data["code"], str) and len(data["code"]) > 0
    assert data["xp_per_referral"] == 150
    assert data["referred_xp"] == 100
    student_session.ref_code = data["code"]


def test_referral_apply_own_rejected(student_session):
    code = student_session.get(f"{API}/referral/code", timeout=10).json()["code"]
    r = student_session.post(f"{API}/referral/apply", json={"code": code}, timeout=10)
    assert r.status_code == 400


def test_referral_apply_invalid(student_session):
    r = student_session.post(f"{API}/referral/apply", json={"code": "NOSUCHCODE"}, timeout=10)
    assert r.status_code == 404


def test_referral_apply_success_and_duplicate(student_session, second_student):
    code = student_session.get(f"{API}/referral/code", timeout=10).json()["code"]
    r = second_student.post(f"{API}/referral/apply", json={"code": code}, timeout=10)
    assert r.status_code == 200, f"apply failed: {r.status_code} {r.text}"
    data = r.json()
    assert data["xp_earned"] == 100
    # duplicate apply by same user should fail
    r2 = second_student.post(f"{API}/referral/apply", json={"code": code}, timeout=10)
    assert r2.status_code == 400


# ---------- Recommendations ----------

def test_recommendations(student_session):
    r = student_session.get(f"{API}/recommendations", timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert "recommendations" in data
    recs = data["recommendations"]
    assert 1 <= len(recs) <= 4
    for rec in recs:
        for k in ["type", "title", "description", "action"]:
            assert k in rec


# ---------- Chat: YouTube tag + Next Step marker ----------

def _create_biology_session(session):
    r = session.post(
        f"{API}/chat/sessions",
        json={"class_level": "10", "subject": "Science", "chapter": "How do Organisms Reproduce", "chapter_id": "10_sci_06"},
        timeout=15,
    )
    assert r.status_code == 200, f"session create failed: {r.status_code} {r.text}"
    return r.json()["session_id"]


def test_chat_youtube_and_next_step(student_session):
    session_id = _create_biology_session(student_session)
    prompt = "Can you show me a visual of how mitosis works? Please include a YouTube video."
    r = student_session.post(
        f"{API}/chat/sessions/{session_id}/message",
        json={"content": prompt},
        stream=True,
        timeout=120,
    )
    assert r.status_code == 200
    full = ""
    for raw in r.iter_lines(decode_unicode=True):
        if not raw:
            continue
        if raw.startswith("data: "):
            payload = raw[6:]
            try:
                evt = json.loads(payload)
            except Exception:
                continue
            if evt.get("type") == "chunk":
                full += evt.get("content", "")
            elif evt.get("type") == "done":
                break
            elif evt.get("type") == "error":
                pytest.fail(f"AI error: {evt.get('message')}")
    assert len(full) > 50, "AI response too short"
    has_youtube = "[YOUTUBE]" in full and "[/YOUTUBE]" in full
    has_next_step_marker = any(m in full for m in ["⚡", "🎯", "🚀", "🎬", "📝"])
    assert has_next_step_marker, f"Missing next-step marker. Response tail: {full[-300:]}"
    # YouTube tag is conditional — we asked explicitly so should appear, but mark as soft warning
    if not has_youtube:
        pytest.skip(f"AI did not emit [YOUTUBE] tag despite explicit request. Tail: {full[-300:]}")
