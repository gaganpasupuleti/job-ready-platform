import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class McqBankRegistry(Base, TimestampMixin):
    __tablename__ = "mcq_bank_registry"

    bank_key: Mapped[str] = mapped_column(String(80), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    question_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class McqImportRun(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "mcq_import_runs"

    bank_key: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    import_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="staged", nullable=False)
    workbook_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    bank_version_at_preview: Mapped[int] = mapped_column(Integer, nullable=False)
    staged_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    preview_summary: Mapped[dict] = mapped_column(JSONB, nullable=False)
    row_errors: Mapped[list] = mapped_column(JSONB, nullable=False)
    allow_empty_replace: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class McqQuestionRevision(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "mcq_question_revisions"

    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), index=True
    )
    content_key: Mapped[str] = mapped_column(String(160), index=True, nullable=False)
    bank_key: Mapped[str | None] = mapped_column(String(80), nullable=True)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    import_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("mcq_import_runs.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
