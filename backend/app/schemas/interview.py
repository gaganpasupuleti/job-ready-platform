from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import Difficulty
from app.models.interview_enums import (
    ContentBatchStatus,
    ContentReviewStatus,
    ContentValidationStatus,
    ExperienceLevel,
    InterviewQuestionType,
)


class InterviewAnswerPointPublic(BaseModel):
    id: UUID
    point_text: str
    sort_order: int


class InterviewQuestionPublic(BaseModel):
    id: UUID
    slug: str
    question_text: str
    question_type: InterviewQuestionType
    difficulty: Difficulty
    experience_level: ExperienceLevel
    expected_answer: str
    explanation: str | None = None
    key_points: list[InterviewAnswerPointPublic] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    roles: list[str] = Field(default_factory=list)
    companies: list[str] = Field(default_factory=list)


class InterviewQuestionListItem(BaseModel):
    id: UUID
    slug: str
    question_text: str
    question_type: InterviewQuestionType
    difficulty: Difficulty
    experience_level: ExperienceLevel
    skills: list[str] = Field(default_factory=list)
    roles: list[str] = Field(default_factory=list)


class InterviewQuestionListResponse(BaseModel):
    items: list[InterviewQuestionListItem]
    total: int


class InterviewPackPublic(BaseModel):
    id: UUID
    slug: str
    title: str
    description: str | None = None
    experience_level: ExperienceLevel | None = None
    question_count: int = 0


class ContentCandidateUpdate(BaseModel):
    question_text: str | None = None
    question_type: str | None = None
    difficulty: str | None = None
    experience_level: str | None = None
    expected_answer: str | None = None
    explanation: str | None = None
    key_points: list[str] | None = None
    skills: list[str] | None = None
    roles: list[str] | None = None
    companies: list[str] | None = None
    jobs: list[str] | None = None


class BulkIds(BaseModel):
    ids: list[UUID]


class ContentCandidateAdmin(BaseModel):
    id: UUID
    batch_id: UUID
    content_hash: str
    validation_status: ContentValidationStatus
    review_status: ContentReviewStatus
    validation_errors: dict[str, Any] | None = None
    payload_json: dict[str, Any]
    published_question_id: UUID | None = None
    created_at: datetime


class ContentCandidateListResponse(BaseModel):
    items: list[ContentCandidateAdmin]
    total: int


class ContentBatchAdmin(BaseModel):
    id: UUID
    batch_date: date
    content_type: str
    target_domain: str | None = None
    target_role: str | None = None
    target_skill: str | None = None
    target_company: str | None = None
    requested_count: int
    generated_count: int
    accepted_count: int
    rejected_count: int
    status: ContentBatchStatus
    generator: str
    source_filename: str | None = None
    created_at: datetime
    candidates: list[ContentCandidateAdmin] = Field(default_factory=list)


class ContentBatchListResponse(BaseModel):
    items: list[ContentBatchAdmin]
    total: int
