"""In-app notifications. Email delivery is intentionally absent."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.base import UUIDPrimaryKeyMixin

ASSIGNMENT_REVIEW = "assignment_review"
SUPPORT_REPLY = "support_reply"
EVENT_TYPES = (ASSIGNMENT_REVIEW, SUPPORT_REPLY)

ASSIGNMENT_SOURCE = "assignment_submission"
SUPPORT_SOURCE = "support_ticket"

ASSIGNMENT_REVIEW_MESSAGE = "Your assignment has been reviewed."
SUPPORT_REPLY_MESSAGE = "You have a new reply on your request."


class Notification(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "notifications"
    __table_args__ = (
        UniqueConstraint("event_key", name="uq_notifications_event_key"),
        CheckConstraint(
            "event_type IN ('assignment_review', 'support_reply')",
            name="ck_notifications_event_type",
        ),
    )

    recipient_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    event_key: Mapped[str] = mapped_column(String(160), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    message: Mapped[str] = mapped_column(String(160), nullable=False)
    destination_path: Mapped[str] = mapped_column(String(300), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
