"""Tests for the NEW POST /api/mock-exam/{exam_id}/followup-quiz endpoint and the
quiz submission of the generated follow-up quiz.

Covers:
  - 401 when unauthenticated
  - 404 when exam doesn't exist
  - 400 when exam exists but not yet submitted
  - 400 when exam submitted but no weak topics (perfect score)
  - 200 success path: 5 questions, weak topics referenced, quiz_id present
  - Submitting the follow-up quiz via /api/quiz/{quiz_id}/submit awards XP
"""
import os
import uuid
import pytest
import requests
from pathlib import Path


def _load_backend_url():
    url = os.environ.get('REACT_APP_BACKEND_URL')
    if url:
        return url.rstrip('/')
    env_path = Path(__file__).resolve().parents[2] / 'frontend' / '.env'
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith('REACT_APP_BACKEND_URL='):
                return line.split('=', 1)[1].strip().rstrip('/')
    raise RuntimeError("REACT_APP_BACKEND_URL is not set")


BASE_URL = _load_backend_url()
API = f"{BASE_URL}/api"


# ---------- Shared fixtures ----------

@pytest.fixture(scope="module")
def student():
    s = requests.Session()
    email = f"TEST_followup_{uuid.uuid4().hex[:8]}@neuralearn.ai"
    pw = "Test@1234567"
    r = s.post(f"{API}/auth/register", json={"email": email, "password": pw, "name": "Followup Tester"}, timeout=30)
    assert r.status_code == 200, f"register failed: {r.status_code} {r.text}"
    s.email = email
    return s


def _gen_exam(session):
    payload = {"class_level": "10", "subject": "Mathematics", "duration_minutes": 30, "num_questions": 10}
    r = session.post(f"{API}/mock-exam/generate", json=payload, timeout=120)
    assert r.status_code == 200, f"mock exam gen failed: {r.status_code} {r.text[:200]}"
    return r.json()


def _flip_letter(letter):
    """Return a wrong option letter different from the correct one."""
    order = ["A", "B", "C", "D"]
    for x in order:
        if x != letter:
            return x
    return "B"


# ---------- 401 / 404 / 400 paths ----------

def test_followup_quiz_unauthenticated():
    r = requests.post(f"{API}/mock-exam/exam_nonexistent/followup-quiz", timeout=10)
    assert r.status_code == 401, f"expected 401, got {r.status_code} {r.text[:200]}"


def test_followup_quiz_exam_not_found(student):
    r = student.post(f"{API}/mock-exam/exam_doesnotexist123/followup-quiz", timeout=15)
    assert r.status_code == 404
    assert "not found" in r.json().get("detail", "").lower()


def test_followup_quiz_exam_not_submitted(student):
    """Generate an exam but DO NOT submit it. Should 400."""
    exam = _gen_exam(student)
    r = student.post(f"{API}/mock-exam/{exam['exam_id']}/followup-quiz", timeout=15)
    assert r.status_code == 400, f"expected 400, got {r.status_code} {r.text[:200]}"
    assert "submit" in r.json().get("detail", "").lower()


def test_followup_quiz_no_weak_topics(student):
    """Submit exam with all correct answers -> no weak topics -> 400 with friendly msg."""
    exam = _gen_exam(student)
    answers = {}
    for sec in exam["sections"]:
        for q in sec["questions"]:
            answers[q["id"]] = q.get("correct", "A")
    body = {"quiz_id": exam["exam_id"], "answers": answers}
    r = student.post(f"{API}/mock-exam/{exam['exam_id']}/submit", json=body, timeout=20)
    assert r.status_code == 200
    assert r.json().get("weak_topics") == []

    r2 = student.post(f"{API}/mock-exam/{exam['exam_id']}/followup-quiz", timeout=15)
    assert r2.status_code == 400, f"expected 400 no-weak-topics, got {r2.status_code} {r2.text[:200]}"
    detail = r2.json().get("detail", "").lower()
    assert "weak topic" in detail or "nailed" in detail or "harder" in detail


# ---------- 200 happy path: weak topics present ----------

@pytest.fixture(scope="module")
def submitted_exam_with_weak_topics(student):
    """Submit exam with intentionally wrong answers so weak_topics will be populated."""
    exam = _gen_exam(student)
    answers = {}
    for sec in exam["sections"]:
        for q in sec["questions"]:
            # Flip every answer so they are all wrong -> all topics become weak topics
            correct = q.get("correct", "A")
            answers[q["id"]] = _flip_letter(correct)
    body = {"quiz_id": exam["exam_id"], "answers": answers}
    r = student.post(f"{API}/mock-exam/{exam['exam_id']}/submit", json=body, timeout=20)
    assert r.status_code == 200
    submit_data = r.json()
    assert isinstance(submit_data.get("weak_topics"), list)
    assert len(submit_data["weak_topics"]) > 0, "expected weak topics after wrong answers"
    return exam, submit_data


def test_followup_quiz_success(student, submitted_exam_with_weak_topics):
    exam, submit_data = submitted_exam_with_weak_topics
    r = student.post(f"{API}/mock-exam/{exam['exam_id']}/followup-quiz", timeout=90)
    assert r.status_code == 200, f"followup-quiz failed: {r.status_code} {r.text[:300]}"
    quiz = r.json()
    # Quiz shape
    assert "quiz_id" in quiz and quiz["quiz_id"].startswith("quiz_")
    assert quiz.get("source_exam_id") == exam["exam_id"]
    assert quiz.get("difficulty") == "adaptive"
    assert quiz.get("subject") == exam["subject"]
    assert quiz.get("class_level") == exam["class_level"]
    # 5 questions expected
    questions = quiz.get("questions", [])
    assert len(questions) == 5, f"expected 5 follow-up questions, got {len(questions)}"
    for q in questions:
        assert "question" in q
        assert "options" in q and len(q["options"]) == 4
        assert "correct" in q
    # Weak topics propagated
    assert set(quiz.get("weak_topics", [])) == set(submit_data["weak_topics"])
    return quiz


def test_followup_quiz_submission_awards_xp(student, submitted_exam_with_weak_topics):
    """Create a follow-up quiz, then submit it via /api/quiz/{quiz_id}/submit and verify XP awarded."""
    exam, _ = submitted_exam_with_weak_topics

    # XP before
    me_before = student.get(f"{API}/auth/me", timeout=10).json()
    xp_before = me_before.get("xp", 0)

    # Create follow-up
    rq = student.post(f"{API}/mock-exam/{exam['exam_id']}/followup-quiz", timeout=90)
    assert rq.status_code == 200
    quiz = rq.json()
    quiz_id = quiz["quiz_id"]
    questions = quiz["questions"]

    # Submit all correct answers
    answers = {str(i): q["correct"] for i, q in enumerate(questions)}
    rs = student.post(f"{API}/quiz/{quiz_id}/submit", json={"quiz_id": quiz_id, "answers": answers}, timeout=20)
    assert rs.status_code == 200, f"quiz submit failed: {rs.status_code} {rs.text[:200]}"
    result = rs.json()
    assert result["score"] == 100
    assert result["correct_count"] == len(questions)
    assert result["xp_earned"] == len(questions) * 20

    # XP after
    me_after = student.get(f"{API}/auth/me", timeout=10).json()
    xp_after = me_after.get("xp", 0)
    assert xp_after >= xp_before + result["xp_earned"], (
        f"XP did not increase as expected. before={xp_before}, after={xp_after}, earned={result['xp_earned']}"
    )
