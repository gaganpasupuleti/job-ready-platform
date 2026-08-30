"""Interview Q&A bank, packs, and content-factory staging (same jobready_db)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import Difficulty
from app.models.interview_enums import (
    ContentBatchStatus,
    ContentReviewStatus,
    ContentSourceType,
    ContentType,
    ContentValidationStatus,
    ExperienceLevel,
    InterviewQuestionType,
)


class JobListing(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Catalog stub for future Jobs Portal — not the full jobs product."""

    __tablename__ = "jobs"

    slug: Mapped[str] = mapped_column(String(180), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class InterviewQuestion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "interview_questions"

    slug: Mapped[str] = mapped_column(String(180), unique=True, index=True, nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[InterviewQuestionType] = mapped_column(
        Enum(InterviewQuestionType, name="interview_question_type", native_enum=False),
        nullable=False,
    )
    difficulty: Mapped[Difficulty] = mapped_column(
        Enum(Difficulty, name="difficulty", native_enum=False),
        nullable=False,
    )
    experience_level: Mapped[ExperienceLevel] = mapped_column(
        Enum(ExperienceLevel, name="experience_level", native_enum=False),
        nullable=False,
    )
    expected_answer: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_type: Mapped[ContentSourceType] = mapped_column(
        Enum(ContentSourceType, name="content_source_type", native_enum=False),
        default=ContentSourceType.MANUAL,
        nullable=False,
    )
    review_status: Mapped[ContentReviewStatus] = mapped_column(
        Enum(ContentReviewStatus, name="content_review_status", native_enum=False),
        default=ContentReviewStatus.PENDING,
        nullable=False,
        index=True,
    )
    content_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    domain_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("domains.id"), nullable=True
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True
    )
    topic_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("topics.id"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    key_points: Mapped[list[InterviewAnswerPoint]] = relationship(
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="InterviewAnswerPoint.sort_order",
    )


class InterviewAnswerPoint(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "interview_answer_points"

    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_questions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    point_text: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    question: Mapped[InterviewQuestion] = relationship(back_populates="key_points")


class InterviewQuestionSkill(Base):
    __tablename__ = "interview_question_skills"
    __table_args__ = (
        UniqueConstraint("question_id", "skill_id", name="uq_interview_question_skill"),
    )

    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_questions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True
    )


class InterviewQuestionRole(Base):
    __tablename__ = "interview_question_roles"
    __table_args__ = (
        UniqueConstraint("question_id", "role_id", name="uq_interview_question_role"),
    )

    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_questions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_roles.id", ondelete="CASCADE"), primary_key=True
    )


class InterviewQuestionCompany(Base):
    __tablename__ = "interview_question_companies"
    __table_args__ = (
        UniqueConstraint("question_id", "company_id", name="uq_interview_question_company"),
    )

    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_questions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), primary_key=True
    )


class InterviewQuestionJob(Base):
    __tablename__ = "interview_question_jobs"
    __table_args__ = (
        UniqueConstraint("question_id", "job_id", name="uq_interview_question_job"),
    )

    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_questions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True
    )


class InterviewPack(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "interview_packs"

    slug: Mapped[str] = mapped_column(String(180), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    experience_level: Mapped[ExperienceLevel | None] = mapped_column(
        Enum(ExperienceLevel, name="experience_level", native_enum=False),
        nullable=True,
    )
    target_role_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_roles.id"), nullable=True
    )
    target_company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    items: Mapped[list[InterviewPackQuestion]] = relationship(
        back_populates="pack",
        cascade="all, delete-orphan",
        order_by="InterviewPackQuestion.sort_order",
    )


class InterviewPackQuestion(Base):
    __tablename__ = "interview_pack_questions"
    __table_args__ = (
        UniqueConstraint("pack_id", "question_id", name="uq_interview_pack_question"),
    )

    pack_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_packs.id", ondelete="CASCADE"),
        primary_key=True,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_questions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    section_name: Mapped[str | None] = mapped_column(String(150), nullable=True)

    pack: Mapped[InterviewPack] = relationship(back_populates="items")


class ContentGenerationBatch(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "content_generation_batches"

    batch_date: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    content_type: Mapped[ContentType] = mapped_column(
        Enum(ContentType, name="content_type", native_enum=False),
        default=ContentType.INTERVIEW_QA,
        nullable=False,
    )
    target_domain: Mapped[str | None] = mapped_column(String(150), nullable=True)
    target_role: Mapped[str | None] = mapped_column(String(150), nullable=True)
    target_company: Mapped[str | None] = mapped_column(String(150), nullable=True)
    target_skill: Mapped[str | None] = mapped_column(String(150), nullable=True)
    requested_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    generated_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    accepted_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rejected_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[ContentBatchStatus] = mapped_column(
        Enum(ContentBatchStatus, name="content_batch_status", native_enum=False),
        default=ContentBatchStatus.PENDING,
        nullable=False,
    )
    generator: Mapped[str] = mapped_column(String(50), default="cursor", nullable=False)
    source_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    candidates: Mapped[list[ContentGenerationCandidate]] = relationship(
        back_populates="batch", cascade="all, delete-orphan"
    )


class ContentGenerationCandidate(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "content_generation_candidates"

    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content_generation_batches.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    content_type: Mapped[ContentType] = mapped_column(
        Enum(ContentType, name="content_type", native_enum=False),
        default=ContentType.INTERVIEW_QA,
        nullable=False,
    )
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    validation_status: Mapped[ContentValidationStatus] = mapped_column(
        Enum(ContentValidationStatus, name="content_validation_status", native_enum=False),
        default=ContentValidationStatus.PENDING,
        nullable=False,
    )
    review_status: Mapped[ContentReviewStatus] = mapped_column(
        Enum(ContentReviewStatus, name="content_review_status", native_enum=False),
        default=ContentReviewStatus.PENDING,
        nullable=False,
        index=True,
    )
    validation_errors: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    published_question_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interview_questions.id"), nullable=True
    )

    batch: Mapped[ContentGenerationBatch] = relationship(back_populates="candidates")
