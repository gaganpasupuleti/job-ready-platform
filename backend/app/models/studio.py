"""Student materials, assignments, and published quiz packs.

These sit beside courses and projects. They do not replace job listings,
saved jobs, or application history.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class LearningMaterial(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "learning_materials"

    content_key: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    kind: Mapped[str] = mapped_column(String(40), nullable=False)
    level: Mapped[str] = mapped_column(String(32), nullable=False)
    audience: Mapped[str | None] = mapped_column(String(32), nullable=True)
    estimated_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    objectives: Mapped[list] = mapped_column(JSONB, nullable=False)
    prerequisites: Mapped[list] = mapped_column(JSONB, nullable=False)
    body_md: Mapped[str] = mapped_column(Text, nullable=False)
    examples: Mapped[list] = mapped_column(JSONB, nullable=False)
    exercises: Mapped[list] = mapped_column(JSONB, nullable=False)
    summary_md: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[list] = mapped_column(JSONB, nullable=False)
    families: Mapped[list] = mapped_column(JSONB, nullable=False)
    skill_tags: Mapped[list] = mapped_column(JSONB, nullable=False)
    download_relpath: Mapped[str | None] = mapped_column(String(400), nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    is_published: Mapped[bool] = mapped_column(nullable=False, default=False)


class LearningMaterialRead(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "learning_material_reads"
    __table_args__ = (UniqueConstraint("user_id", "material_id", name="uq_material_read_user"),)

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    material_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("learning_materials.id", ondelete="CASCADE"), nullable=False)
    read_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Assignment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "assignments"

    content_key: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    goal: Mapped[str] = mapped_column(Text, nullable=False)
    brief_md: Mapped[str] = mapped_column(Text, nullable=False)
    requirements: Mapped[list] = mapped_column(JSONB, nullable=False)
    deliverables: Mapped[list] = mapped_column(JSONB, nullable=False)
    hints: Mapped[list] = mapped_column(JSONB, nullable=False)
    prerequisites: Mapped[list] = mapped_column(JSONB, nullable=False)
    rubric: Mapped[list] = mapped_column(JSONB, nullable=False)
    submission_mode: Mapped[str] = mapped_column(String(40), nullable=False)
    estimated_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    families: Mapped[list] = mapped_column(JSONB, nullable=False)
    skill_tags: Mapped[list] = mapped_column(JSONB, nullable=False)
    sql_problem_slug: Mapped[str | None] = mapped_column(String(150), nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    is_published: Mapped[bool] = mapped_column(nullable=False, default=False)


class AssignmentSubmission(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "assignment_submissions"

    assignment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    assignment_version: Mapped[int] = mapped_column(Integer, nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    evidence_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    brief_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class AssignmentReview(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "assignment_reviews"

    submission_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assignment_submissions.id", ondelete="CASCADE"), nullable=False)
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    submission_version: Mapped[int] = mapped_column(Integer, nullable=False)
    feedback: Mapped[str] = mapped_column(Text, nullable=False)
    grade: Mapped[str | None] = mapped_column(String(40), nullable=True)
    rubric_notes: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ContentPack(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "content_packs"

    content_key: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(40), nullable=False)
    instructions: Mapped[str] = mapped_column(Text, nullable=False)
    families: Mapped[list] = mapped_column(JSONB, nullable=False)
    skill_tags: Mapped[list] = mapped_column(JSONB, nullable=False)
    question_count: Mapped[int] = mapped_column(Integer, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    is_published: Mapped[bool] = mapped_column(nullable=False, default=False)


class ContentPackQuestion(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "content_pack_questions"
    __table_args__ = (UniqueConstraint("pack_id", "question_id", name="uq_pack_question"),)

    pack_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("content_packs.id", ondelete="CASCADE"), nullable=False)
    question_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)


class ContentBatchItem(Base):
    __tablename__ = "content_batch_items"

    item_key: Mapped[str] = mapped_column(String(160), primary_key=True)
    content_type: Mapped[str] = mapped_column(String(40), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    batch_id: Mapped[str] = mapped_column(String(80), nullable=False)
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
