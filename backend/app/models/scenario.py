"""Deterministic scenario challenges — no live cloud, cluster, or SIEM."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import Difficulty
from app.models.scenario_enums import ScenarioDomain, ScenarioProgressStatus, ScenarioType


class ScenarioChallenge(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "scenario_challenges"

    slug: Mapped[str] = mapped_column(String(180), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    domain_key: Mapped[ScenarioDomain] = mapped_column(
        Enum(ScenarioDomain, name="scenario_domain", native_enum=False), index=True
    )
    scenario_type: Mapped[ScenarioType] = mapped_column(
        Enum(ScenarioType, name="scenario_type", native_enum=False)
    )
    difficulty: Mapped[Difficulty] = mapped_column(
        Enum(Difficulty, name="difficulty", native_enum=False, create_constraint=False)
    )
    context_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    evidence_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    unofficial_cert_tag: Mapped[str | None] = mapped_column(String(80), nullable=True)
    mastery_threshold: Mapped[int] = mapped_column(Integer, default=80, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    steps: Mapped[list[ScenarioStep]] = relationship(
        back_populates="challenge", cascade="all, delete-orphan", order_by="ScenarioStep.sort_order"
    )


class ScenarioStep(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "scenario_steps"

    challenge_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenario_challenges.id", ondelete="CASCADE"), index=True
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    context_snippet: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_critical: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    scoring_weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    challenge: Mapped[ScenarioChallenge] = relationship(back_populates="steps")
    options: Mapped[list[ScenarioOption]] = relationship(
        back_populates="step", cascade="all, delete-orphan", order_by="ScenarioOption.sort_order"
    )


class ScenarioOption(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "scenario_options"

    step_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenario_steps.id", ondelete="CASCADE"), index=True
    )
    label: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    step: Mapped[ScenarioStep] = relationship(back_populates="options")


class ScenarioSubmission(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "scenario_submissions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    challenge_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenario_challenges.id", ondelete="CASCADE"), index=True
    )
    overall_score: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    correct_decisions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_steps: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    missed_critical: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    explanation: Mapped[str] = mapped_column(Text, nullable=False, default="")

    answers: Mapped[list[ScenarioStepAnswer]] = relationship(
        back_populates="submission", cascade="all, delete-orphan"
    )


class ScenarioStepAnswer(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "scenario_step_answers"

    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenario_submissions.id", ondelete="CASCADE"), index=True
    )
    step_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenario_steps.id", ondelete="CASCADE"), index=True
    )
    option_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenario_options.id", ondelete="CASCADE")
    )
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    score: Mapped[float] = mapped_column(Float, default=0, nullable=False)

    submission: Mapped[ScenarioSubmission] = relationship(back_populates="answers")


class ScenarioProgress(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "scenario_progress"
    __table_args__ = (UniqueConstraint("user_id", "challenge_id", name="uq_scenario_progress"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    challenge_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenario_challenges.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[ScenarioProgressStatus] = mapped_column(
        Enum(ScenarioProgressStatus, name="scenario_progress_status", native_enum=False),
        default=ScenarioProgressStatus.ATTEMPTED,
    )
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    best_score: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
