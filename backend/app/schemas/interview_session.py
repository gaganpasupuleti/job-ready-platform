"""Schemas for Build 8 interview sessions (student practice)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import Difficulty
from app.models.interview_enums import (
    ExperienceLevel,
    InterviewConfidence,
    InterviewQuestionType,
    InterviewSelfRating,
    InterviewSessionMode,
    InterviewSessionQuestionStatus,
    InterviewSessionSource,
    InterviewSessionStatus,
)
from app.schemas.interview import InterviewAnswerPointPublic, InterviewPackPublic


class InterviewSessionCreate(BaseModel):
    mode: InterviewSessionMode = InterviewSessionMode.STUDY
    source_type: InterviewSessionSource = InterviewSessionSource.CUSTOM_FILTER
    pack_id: UUID | None = None
    pack_slug: str | None = None
    title: str | None = None
    question_count: int = Field(default=10, ge=1, le=50)
    role: str | None = None
    skill: str | None = None
    company: str | None = None
    difficulty: Difficulty | None = None
    experience_level: ExperienceLevel | None = None
    question_type: InterviewQuestionType | None = None
    question_ids: list[UUID] | None = None
    deterministic: bool = False


class InterviewSessionSummary(BaseModel):
    id: UUID
    title: str
    mode: InterviewSessionMode
    source_type: InterviewSessionSource
    pack_id: UUID | None = None
    pack_slug: str | None = None
    question_count: int
    current_question_index: int
    status: InterviewSessionStatus
    started_at: datetime
    completed_at: datetime | None = None
    reviewed_count: int = 0
    needs_review_count: int = 0
    key_point_coverage_avg: float | None = None


class InterviewNavigatorItem(BaseModel):
    number: int
    status: InterviewSessionQuestionStatus
    needs_review: bool = False
    current: bool = False


class InterviewSessionQuestionPublic(BaseModel):
    number: int
    question_id: UUID
    slug: str
    question_text: str
    question_type: InterviewQuestionType
    difficulty: Difficulty
    experience_level: ExperienceLevel
    skills: list[str] = Field(default_factory=list)
    roles: list[str] = Field(default_factory=list)
    companies: list[str] = Field(default_factory=list)
    status: InterviewSessionQuestionStatus
    answer_revealed: bool = False
    expected_answer: str | None = None
    explanation: str | None = None
    key_points: list[InterviewAnswerPointPublic] = Field(default_factory=list)
    answer_text: str | None = None
    private_notes: str | None = None
    self_rating: InterviewSelfRating | None = None
    confidence_level: InterviewConfidence | None = None
    key_points_checked: list[UUID] = Field(default_factory=list)
    needs_review: bool = False
    time_spent_seconds: int | None = None
    key_point_coverage: float | None = None


class InterviewSessionDetail(BaseModel):
    session: InterviewSessionSummary
    navigator: list[InterviewNavigatorItem] = Field(default_factory=list)
    current: InterviewSessionQuestionPublic | None = None


class InterviewNotesPayload(BaseModel):
    answer_text: str | None = None
    private_notes: str | None = None


class InterviewReviewPayload(BaseModel):
    key_point_ids: list[UUID] = Field(default_factory=list)
    confidence: InterviewConfidence
    self_rating: InterviewSelfRating
    needs_review: bool | None = None
    time_spent_seconds: int | None = Field(default=None, ge=0, le=86_400)


class InterviewSkillBreakdown(BaseModel):
    skill: str
    question_count: int
    key_point_coverage_avg: float | None = None


class InterviewTypeBreakdown(BaseModel):
    question_type: str
    question_count: int
    needs_review_count: int = 0


class InterviewSessionResults(BaseModel):
    session: InterviewSessionSummary
    questions_total: int
    reviewed_count: int
    needs_review_count: int
    strong: int = 0
    good: int = 0
    partial: int = 0
    needs_review_rating: int = 0
    key_point_coverage_avg: float | None = None
    confidence_breakdown: dict[str, int] = Field(default_factory=dict)
    skill_breakdown: list[InterviewSkillBreakdown] = Field(default_factory=list)
    type_breakdown: list[InterviewTypeBreakdown] = Field(default_factory=list)
    weak_question_ids: list[UUID] = Field(default_factory=list)
    label: str = "Self-Review Summary"


class InterviewProgressResponse(BaseModel):
    questions_reviewed: int = 0
    sessions_completed: int = 0
    needs_review: int = 0
    high_confidence_percent: float | None = None
    average_key_point_coverage: float | None = None
    by_role: dict[str, int] = Field(default_factory=dict)
    by_skill: dict[str, int] = Field(default_factory=dict)
    by_type: dict[str, int] = Field(default_factory=dict)
    by_experience: dict[str, int] = Field(default_factory=dict)


class InterviewNeedsReviewItem(BaseModel):
    question_id: UUID
    slug: str
    question_text: str
    self_rating: InterviewSelfRating | None = None
    confidence_level: InterviewConfidence | None = None
    key_point_coverage: float | None = None
    needs_review: bool = True
    skills: list[str] = Field(default_factory=list)


class InterviewHubResponse(BaseModel):
    continue_session: InterviewSessionSummary | None = None
    packs: list[InterviewPackPublic] = Field(default_factory=list)
    progress: InterviewProgressResponse
    needs_review_count: int = 0
    recent_sessions: list[InterviewSessionSummary] = Field(default_factory=list)


class InterviewPackDetail(InterviewPackPublic):
    target_role: str | None = None
    target_company: str | None = None
    skills_covered: list[str] = Field(default_factory=list)
    difficulty_mix: dict[str, int] = Field(default_factory=dict)
    estimated_minutes: int | None = None
    active_session_id: UUID | None = None


class AdminInterviewPackCreate(BaseModel):
    slug: str | None = None
    title: str
    description: str | None = None
    experience_level: ExperienceLevel | None = None
    target_role: str | None = None
    target_company: str | None = None
    is_active: bool = False
    question_ids: list[UUID] = Field(default_factory=list)


class AdminInterviewPackUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    experience_level: ExperienceLevel | None = None
    target_role: str | None = None
    target_company: str | None = None
    is_active: bool | None = None
    question_ids: list[UUID] | None = None


class CompanyPrepCard(BaseModel):
    slug: str
    name: str
    interview_pack_count: int = 0
    practice_path_slugs: list[str] = Field(default_factory=list)


class CompanyPrepDetail(BaseModel):
    slug: str
    name: str
    disclaimer: str
    skills: list[str] = Field(default_factory=list)
    packs: list[InterviewPackPublic] = Field(default_factory=list)
    practice_paths: list[dict[str, Any]] = Field(default_factory=list)
