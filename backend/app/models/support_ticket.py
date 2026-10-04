import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin

TICKET_CATEGORIES = ("bug", "improvement", "feature_request", "general")
TICKET_STATUSES = ("new", "in_review", "planned", "in_progress", "resolved", "closed")


class SupportTicket(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "support_tickets"
    __table_args__ = (
        UniqueConstraint("user_id", "client_request_id", name="uq_support_tickets_user_request"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reference: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    page_path: Mapped[str | None] = mapped_column(String(300), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="new")
    client_request_id: Mapped[str] = mapped_column(String(80), nullable=False)

    user = relationship("User")
    messages: Mapped[list["SupportTicketMessage"]] = relationship(
        back_populates="ticket",
        cascade="all, delete-orphan",
    )
    status_events: Mapped[list["SupportTicketStatusEvent"]] = relationship(
        back_populates="ticket",
        cascade="all, delete-orphan",
    )


class SupportTicketMessage(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "support_ticket_messages"
    __table_args__ = (
        UniqueConstraint("ticket_id", "client_request_id", name="uq_support_ticket_messages_request"),
    )

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("support_tickets.id", ondelete="CASCADE"),
        nullable=False,
    )
    author_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    author_name: Mapped[str] = mapped_column(String(255), nullable=False)
    author_role: Mapped[str] = mapped_column(String(32), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    client_request_id: Mapped[str] = mapped_column(String(80), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    ticket = relationship("SupportTicket", back_populates="messages")


class SupportTicketStatusEvent(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "support_ticket_status_events"
    __table_args__ = (
        UniqueConstraint("ticket_id", "client_request_id", name="uq_support_ticket_status_request"),
    )

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("support_tickets.id", ondelete="CASCADE"),
        nullable=False,
    )
    actor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    actor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    actor_role: Mapped[str] = mapped_column(String(32), nullable=False)
    from_status: Mapped[str] = mapped_column(String(32), nullable=False)
    to_status: Mapped[str] = mapped_column(String(32), nullable=False)
    client_request_id: Mapped[str] = mapped_column(String(80), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    ticket = relationship("SupportTicket", back_populates="status_events")
