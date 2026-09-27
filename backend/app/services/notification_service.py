"""Recipient-scoped in-app notifications.

Assignment reviews use the stripped note as the event identity. Saving that
same note again, including a retry or a concurrent request, keeps the existing
row and does not change its read time. A different note is a new review and
creates a new unread row. Support notifications are created only for a newly
inserted admin or trainer reply, keyed by that message. Student replies,
status changes, and rows that already existed are not backfilled.
"""

from __future__ import annotations

import base64
import hashlib
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.notification import (
    ASSIGNMENT_REVIEW,
    ASSIGNMENT_REVIEW_MESSAGE,
    ASSIGNMENT_SOURCE,
    SUPPORT_REPLY,
    SUPPORT_REPLY_MESSAGE,
    SUPPORT_SOURCE,
    Notification,
)
from app.models.user import User
from app.schemas.notification import NotificationItem, NotificationPage, UnreadCount

_PAGE_MAX = 30


def assignment_event_key(submission_id: UUID, note: str) -> str:
    digest = hashlib.sha256(note.encode("utf-8")).hexdigest()
    return f"assignment_review:{submission_id}:{digest}"


def support_event_key(message_id: UUID) -> str:
    return f"support_reply:{message_id}"


def assignment_destination(submission_id: UUID) -> str:
    return f"/practice/projects#submission-{submission_id}"


def support_destination(ticket_id: UUID) -> str:
    return f"/support/requests/{ticket_id}"


def _encode_cursor(created_at: datetime, item_id: UUID) -> str:
    raw = f"{created_at.isoformat()}|{item_id}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def _decode_cursor(cursor: str) -> tuple[datetime, UUID]:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
        stamp, item_id = raw.split("|", 1)
        created_at = datetime.fromisoformat(stamp)
        parsed_id = UUID(item_id)
    except (ValueError, UnicodeError):
        raise AppException("Invalid page cursor", status_code=400) from None
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    return created_at, parsed_id


class NotificationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def stage_assignment_review(self, *, recipient_id: UUID, submission_id: UUID, note: str) -> None:
        key = assignment_event_key(submission_id, note)
        existing = await self.db.scalar(select(Notification.id).where(Notification.event_key == key))
        if existing is not None:
            return
        self.db.add(
            Notification(
                recipient_user_id=recipient_id,
                event_type=ASSIGNMENT_REVIEW,
                event_key=key,
                source_type=ASSIGNMENT_SOURCE,
                source_id=submission_id,
                message=ASSIGNMENT_REVIEW_MESSAGE,
                destination_path=assignment_destination(submission_id),
            )
        )

    async def stage_support_reply(
        self,
        *,
        recipient_id: UUID,
        ticket_id: UUID,
        message_id: UUID,
        author_id: UUID | None,
        author_role: str,
    ) -> None:
        if author_id == recipient_id or author_role not in {"admin", "trainer"}:
            return
        key = support_event_key(message_id)
        existing = await self.db.scalar(select(Notification.id).where(Notification.event_key == key))
        if existing is not None:
            return
        self.db.add(
            Notification(
                recipient_user_id=recipient_id,
                event_type=SUPPORT_REPLY,
                event_key=key,
                source_type=SUPPORT_SOURCE,
                source_id=ticket_id,
                message=SUPPORT_REPLY_MESSAGE,
                destination_path=support_destination(ticket_id),
            )
        )

    async def list_for_user(self, user: User, *, limit: int, cursor: str | None) -> NotificationPage:
        page_size = min(max(limit, 1), _PAGE_MAX)
        stmt = select(Notification).where(Notification.recipient_user_id == user.id)
        if cursor:
            created_at, item_id = _decode_cursor(cursor)
            stmt = stmt.where(
                or_(
                    Notification.created_at < created_at,
                    and_(Notification.created_at == created_at, Notification.id < item_id),
                )
            )
        rows = (
            await self.db.scalars(
                stmt.order_by(Notification.created_at.desc(), Notification.id.desc()).limit(page_size + 1)
            )
        ).all()
        has_more = len(rows) > page_size
        visible = rows[:page_size]
        next_cursor = _encode_cursor(visible[-1].created_at, visible[-1].id) if has_more and visible else None
        return NotificationPage(items=[self._item(row) for row in visible], next_cursor=next_cursor)

    async def unread_count(self, user: User) -> UnreadCount:
        count = await self.db.scalar(
            select(func.count())
            .select_from(Notification)
            .where(Notification.recipient_user_id == user.id, Notification.read_at.is_(None))
        )
        return UnreadCount(count=int(count or 0))

    async def mark_read(self, user: User, notification_id: UUID) -> NotificationItem:
        row = await self.db.scalar(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.recipient_user_id == user.id,
            )
        )
        if row is None:
            raise AppException("Notification not found", status_code=404)
        if row.read_at is None:
            row.read_at = datetime.now(timezone.utc)
            await self.db.commit()
            await self.db.refresh(row)
        return self._item(row)

    async def mark_all_read(self, user: User) -> UnreadCount:
        await self.db.execute(
            update(Notification)
            .where(Notification.recipient_user_id == user.id, Notification.read_at.is_(None))
            .values(read_at=datetime.now(timezone.utc))
        )
        await self.db.commit()
        return UnreadCount(count=0)

    def _item(self, row: Notification) -> NotificationItem:
        return NotificationItem(
            id=row.id,
            event_type=row.event_type,
            message=row.message,
            destination_path=row.destination_path,
            created_at=row.created_at,
            read_at=row.read_at,
        )
