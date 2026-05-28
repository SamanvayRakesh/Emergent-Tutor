"""Pydantic request/response models."""
from typing import List
from pydantic import BaseModel


# ----- Auth -----
class UserRegister(BaseModel):
    email: str
    password: str
    name: str
    class_level: str = "9"


class UserLogin(BaseModel):
    email: str
    password: str


class GoogleSessionRequest(BaseModel):
    session_id: str


# ----- Chat -----
class ChatSessionCreate(BaseModel):
    class_level: str
    subject: str
    chapter: str
    chapter_id: str


class ChatMessageRequest(BaseModel):
    content: str


# ----- Quiz -----
class QuizGenerateRequest(BaseModel):
    class_level: str
    subject: str
    topic: str
    difficulty: str = "medium"
    num_questions: int = 5


class QuizSubmitRequest(BaseModel):
    quiz_id: str
    answers: dict


# ----- Progress -----
class ProgressUpdate(BaseModel):
    class_level: str
    subject: str
    chapter_id: str
    chapter_name: str
    mastery_delta: int = 10


# ----- Mock Exam -----
class MockExamRequest(BaseModel):
    class_level: str
    subject: str
    duration_minutes: int = 60
    num_questions: int = 20


# ----- Study Plan -----
class StudyPlanRequest(BaseModel):
    exam_date: str
    target_score: int = 90
    daily_hours: float = 2.0
    class_level: str
    subjects: List[str] = []


# ----- Referral -----
class ReferralApplyRequest(BaseModel):
    code: str


# ----- User -----
class UpdateClassRequest(BaseModel):
    class_level: str


# ----- Onboarding -----
class OnboardingSubmit(BaseModel):
    name: str
    class_level: str
    exam_goal: str  # e.g. "Class 10 Boards", "JEE", "NEET", "Improve grades"
    weak_subjects: List[str] = []
    learning_style: str = "balanced"  # visual | quizzes | explanations | interactive | balanced


# ----- Subscription -----
class SubscribeRequest(BaseModel):
    plan: str  # "pro" | "elite"
    billing_cycle: str = "monthly"  # "monthly" | "yearly"
