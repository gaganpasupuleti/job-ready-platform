"""Read-only practice tracker contracts.

These figures are aggregates of records the student already produced.
Opening a catalog page or a question does not create them.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class WeekWindow(BaseModel):
    timezone: Literal["UTC"] = "UTC"
    start: datetime
    end: datetime
    boundary: str


class WeeklyActivity(BaseModel):
    mcq_finalized_answers: int
    coding_submits: int
    sql_submits: int
    total: int


class McqAccuracy(BaseModel):
    graded_answers: int
    correct_answers: int
    accuracy_percent: float | None = None


class RecentPracticeItem(BaseModel):
    kind: Literal["mcq_session", "coding_submit", "sql_submit"]
    source_id: UUID
    title: str
    status: str
    occurred_at: datetime


class WeakTopic(BaseModel):
    topic_id: UUID
    topic_name: str
    topic_slug: str
    graded_answers: int
    correct_answers: int
    incorrect_answers: int
    accuracy_percent: float


class QuizAttempt(BaseModel):
    topic_id: UUID
    topic_name: str
    topic_slug: str
    category_id: UUID
    category_name: str
    active_question_count: int
    attempt_status: Literal["not_started", "in_progress", "completed"]


class RecentlyPublished(BaseModel):
    available: bool = False
    reason: str


class PracticeTrackerResponse(BaseModel):
    week: WeekWindow
    weekly_activity: WeeklyActivity
    mcq_attempted_questions: int
    mcq_attempt_events: int
    mcq_accuracy: McqAccuracy
    completed_sessions: int
    in_progress_sessions: int
    recent_practice: list[RecentPracticeItem] = Field(default_factory=list)
    weak_topics: list[WeakTopic] = Field(default_factory=list)
    quizzes: list[QuizAttempt] = Field(default_factory=list)
    recently_published: RecentlyPublished
