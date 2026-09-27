"""Email preferences and the durable outbox.

Accepted means Brevo returned a message id. It does not mean the message
was delivered. Rows created while sending is disabled or the credentials
are still placeholders are suppressed, not queued.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.base import UUIDPrimaryKeyMixin

CHANNEL_EMAIL = "email"
STATUS_QUEUED = "queued"
STATUS_SENDING = "sending"
STATUS_ACCEPTED = "accepted"
STATUS_FAILED = "failed"
STATUS_AMBIGUOUS = "ambiguous"
STATUS_SUPPRESSED = "suppressed"


class EmailPreference(Base):
    __tablename__ = "email_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    assignment_review_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    support_reply_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class EmailOutbox(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "email_outbox"
    __table_args__ = (
        UniqueConstraint("channel", "event_key", name="uq_email_outbox_channel_event"),
        CheckConstraint("channel = 'email'", name="ck_email_outbox_channel"),
        CheckConstraint(
            "status IN ('queued', 'sending', 'accepted', 'failed', 'ambiguous', 'suppressed')",
            name="ck_email_outbox_status",
        ),
    )

    recipient_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False)
    notification_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("notifications.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    event_key: Mapped[str] = mapped_column(String(160), nullable=False)
    channel: Mapped[str] = mapped_column(String(16), nullable=False, default=CHANNEL_EMAIL)
    destination_path: Mapped[str] = mapped_column(String(300), nullable=False)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    text_body: Mapped[str] = mapped_column(Text, nullable=False)
    html_body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    claim_token: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    provider_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
