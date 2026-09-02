"""Build 10 readiness persistence models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.readiness_enums import (
    MistakeSourceType,
    MistakeStatus,
    RoleSkillImportance,
    RoleSkillSource,
)


class RoleSkillRequirement(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "role_skill_requirements"
    __table_args__ = (
        UniqueConstraint("role_id", "skill_id", name="uq_role_skill_requirement"),
    )

    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_roles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), index=True, nullable=False
    )
    importance: Mapped[RoleSkillImportance] = mapped_column(
        Enum(RoleSkillImportance, name="role_skill_importance", native_enum=False),
        nullable=False,
    )
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    minimum_readiness: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[RoleSkillSource] = mapped_column(
        Enum(RoleSkillSource, name="role_skill_source", native_enum=False),
        nullable=False,
        default=RoleSkillSource.SEED,
    )


class MistakeItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "mistake_items"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "source_type",
            "source_id",
            name="uq_mistake_user_source",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    source_type: Mapped[MistakeSourceType] = mapped_column(
        Enum(MistakeSourceType, name="mistake_source_type", native_enum=False),
        nullable=False,
        index=True,
    )
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    skill_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id", ondelete="SET NULL"), nullable=True, index=True
    )
    topic_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("topics.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    mistake_type: Mapped[str] = mapped_column(String(80), nullable=False, default="incorrect")
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    occurrence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[MistakeStatus] = mapped_column(
        Enum(MistakeStatus, name="mistake_status", native_enum=False),
        nullable=False,
        default=MistakeStatus.OPEN,
        index=True,
    )
    latest_context_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    retry_href: Mapped[str | None] = mapped_column(String(500), nullable=True)


class UserRoleReadinessSnapshot(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "user_role_readiness_snapshots"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_roles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    evidence_strength: Mapped[str] = mapped_column(String(20), nullable=False)
    breakdown_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
