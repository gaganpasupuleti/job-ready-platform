"""Build 8 student interview session state (reuses interview_questions / packs)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
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
from app.models.interview_enums import (
    InterviewConfidence,
    InterviewSelfRating,
    InterviewSessionMode,
    InterviewSessionQuestionStatus,
    InterviewSessionSource,
    InterviewSessionStatus,
)


class InterviewSession(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "interview_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    mode: Mapped[InterviewSessionMode] = mapped_column(
        Enum(InterviewSessionMode, name="interview_session_mode", native_enum=False),
        nullable=False,
    )
    source_type: Mapped[InterviewSessionSource] = mapped_column(
        Enum(InterviewSessionSource, name="interview_session_source", native_enum=False),
        nullable=False,
    )
    pack_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interview_packs.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    question_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_question_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[InterviewSessionStatus] = mapped_column(
        Enum(InterviewSessionStatus, name="interview_session_status", native_enum=False),
        default=InterviewSessionStatus.ACTIVE,
        nullable=False,
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    filters_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    questions: Mapped[list[InterviewSessionQuestion]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="InterviewSessionQuestion.sort_order",
    )


class InterviewSessionQuestion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "interview_session_questions"
    __table_args__ = (
        UniqueConstraint("session_id", "question_id", name="uq_interview_session_question"),
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_questions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[InterviewSessionQuestionStatus] = mapped_column(
        Enum(
            InterviewSessionQuestionStatus,
            name="interview_session_question_status",
            native_enum=False,
        ),
        default=InterviewSessionQuestionStatus.UNSEEN,
        nullable=False,
    )
    answer_revealed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    self_rating: Mapped[InterviewSelfRating | None] = mapped_column(
        Enum(InterviewSelfRating, name="interview_self_rating", native_enum=False),
        nullable=True,
    )
    confidence_level: Mapped[InterviewConfidence | None] = mapped_column(
        Enum(InterviewConfidence, name="interview_confidence", native_enum=False),
        nullable=True,
    )
    key_points_checked_json: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    time_spent_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    session: Mapped[InterviewSession] = relationship(back_populates="questions")


class InterviewQuestionNote(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "interview_question_notes"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "question_id",
            "session_id",
            name="uq_interview_question_note_session",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_questions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    answer_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    private_notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class InterviewQuestionReview(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Latest per-user review snapshot for Needs Review / progress (history stays on session rows)."""

    __tablename__ = "interview_question_reviews"
    __table_args__ = (
        UniqueConstraint("user_id", "question_id", name="uq_interview_question_review"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_questions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    last_session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interview_sessions.id", ondelete="SET NULL"), nullable=True
    )
    self_rating: Mapped[InterviewSelfRating | None] = mapped_column(
        Enum(InterviewSelfRating, name="interview_self_rating", native_enum=False),
        nullable=True,
    )
    confidence_level: Mapped[InterviewConfidence | None] = mapped_column(
        Enum(InterviewConfidence, name="interview_confidence", native_enum=False),
        nullable=True,
    )
    key_point_coverage: Mapped[float | None] = mapped_column(Float, nullable=True)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
