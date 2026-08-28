import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import Difficulty, PracticeMode, SessionStatus


class PracticeSession(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "practice_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    mode: Mapped[PracticeMode] = mapped_column(
        Enum(PracticeMode, name="practice_mode", native_enum=False), nullable=False
    )
    domain_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("domains.id"), nullable=True
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True
    )
    topic_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("topics.id"), nullable=True
    )
    difficulty: Mapped[Difficulty | None] = mapped_column(
        Enum(Difficulty, name="session_difficulty", native_enum=False), nullable=True
    )
    question_count: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus, name="session_status", native_enum=False),
        default=SessionStatus.ACTIVE,
        nullable=False,
    )
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    correct_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    incorrect_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unanswered_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    questions: Mapped[list["PracticeSessionQuestion"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="PracticeSessionQuestion.question_number"
    )
    answers: Mapped[list["PracticeAnswer"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class PracticeSessionQuestion(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "practice_session_questions"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("practice_sessions.id", ondelete="CASCADE"), index=True
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), index=True
    )
    question_number: Mapped[int] = mapped_column(Integer, nullable=False)

    session: Mapped["PracticeSession"] = relationship(back_populates="questions")


class PracticeAnswer(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "practice_answers"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("practice_sessions.id", ondelete="CASCADE"), index=True
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), index=True
    )
    selected_option_ids: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    is_correct: Mapped[bool | None] = mapped_column(nullable=True)
    marks_awarded: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    session: Mapped["PracticeSession"] = relationship(back_populates="answers")


class Bookmark(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "bookmarks"
    __table_args__ = (UniqueConstraint("user_id", "question_id", name="uq_user_question_bookmark"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), index=True
    )
