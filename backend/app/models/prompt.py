"""Prompt challenge domain — deterministic practice, no LLM execution."""

from __future__ import annotations

import uuid
from datetime import datetime

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
from app.models.enums import Difficulty
from app.models.prompt_enums import PromptProgressStatus, PromptTaskType


class PromptChallenge(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "prompt_challenges"

    slug: Mapped[str] = mapped_column(String(180), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    difficulty: Mapped[Difficulty] = mapped_column(
        Enum(Difficulty, name="difficulty", native_enum=False, create_constraint=False),
        nullable=False,
    )
    task_type: Mapped[PromptTaskType] = mapped_column(
        Enum(PromptTaskType, name="prompt_task_type", native_enum=False),
        nullable=False,
    )
    scenario: Mapped[str] = mapped_column(Text, nullable=False, default="")
    instructions: Mapped[str] = mapped_column(Text, nullable=False, default="")
    input_description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    expected_behavior: Mapped[str] = mapped_column(Text, nullable=False, default="")
    starter_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    max_prompt_length: Mapped[int] = mapped_column(Integer, default=8000, nullable=False)
    mastery_threshold: Mapped[int] = mapped_column(Integer, default=80, nullable=False)
    rubric_weights: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    hints: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    common_mistakes: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    evaluation_criteria_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    cases: Mapped[list[PromptChallengeCase]] = relationship(
        back_populates="challenge", cascade="all, delete-orphan", order_by="PromptChallengeCase.sort_order"
    )
    rubrics: Mapped[list[PromptEvaluationRubric]] = relationship(
        back_populates="challenge", cascade="all, delete-orphan"
    )


class PromptChallengeCase(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "prompt_challenge_cases"

    challenge_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prompt_challenges.id", ondelete="CASCADE"), index=True
    )
    input_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    variables: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    expected_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_schema: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    evaluation_config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    hide_input: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    challenge: Mapped[PromptChallenge] = relationship(back_populates="cases")


class PromptEvaluationRubric(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Optional per-dimension weights; JSON on the challenge is the runtime source of truth."""

    __tablename__ = "prompt_evaluation_rubrics"

    challenge_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prompt_challenges.id", ondelete="CASCADE"), index=True
    )
    dimension: Mapped[str] = mapped_column(String(80), nullable=False)
    weight: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")

    challenge: Mapped[PromptChallenge] = relationship(back_populates="rubrics")


class PromptSubmission(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "prompt_submissions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    challenge_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prompt_challenges.id", ondelete="CASCADE"), index=True
    )
    prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_test: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    passed_cases: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_cases: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rubric_breakdown: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    feedback: Mapped[str] = mapped_column(Text, nullable=False, default="")

    case_results: Mapped[list[PromptSubmissionCaseResult]] = relationship(
        back_populates="submission", cascade="all, delete-orphan"
    )


class PromptSubmissionCaseResult(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "prompt_submission_case_results"

    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prompt_submissions.id", ondelete="CASCADE"), index=True
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prompt_challenge_cases.id", ondelete="CASCADE"), index=True
    )
    passed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    score: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    feedback: Mapped[str] = mapped_column(Text, nullable=False, default="")
    check_results: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    revealed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    submission: Mapped[PromptSubmission] = relationship(back_populates="case_results")


class PromptProblemProgress(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "prompt_problem_progress"
    __table_args__ = (UniqueConstraint("user_id", "challenge_id", name="uq_prompt_problem_progress"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    challenge_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prompt_challenges.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[PromptProgressStatus] = mapped_column(
        Enum(PromptProgressStatus, name="prompt_progress_status", native_enum=False),
        default=PromptProgressStatus.ATTEMPTED,
        nullable=False,
    )
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    best_score: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    first_attempted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    first_mastered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
