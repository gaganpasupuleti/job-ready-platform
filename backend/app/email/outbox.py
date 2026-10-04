"""Create one email outbox row in the same transaction as its notification."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.email.messages import build_email
from app.email.preferences import category_enabled
from app.models.email_notification import (
    CHANNEL_EMAIL,
    STATUS_QUEUED,
    STATUS_SUPPRESSED,
    EmailOutbox,
    EmailPreference,
)
from app.models.notification import Notification
from app.models.user import User


async def stage_email_for_notification(db: AsyncSession, notification: Notification) -> None:
    existing = await db.scalar(
        select(EmailOutbox.id).where(
            EmailOutbox.channel == CHANNEL_EMAIL,
            EmailOutbox.event_key == notification.event_key,
        )
    )
    if existing is not None:
        return
    user = await db.get(User, notification.recipient_user_id)
    if user is None or not user.email:
        return
    preference = await db.get(EmailPreference, user.id)
    block = settings.email_block_reason
    if block is None and not category_enabled(preference, notification.event_type):
        block = "preference_off"
    name = user.full_name or user.username
    built = build_email(
        recipient_id=user.id,
        recipient_name=name,
        event_type=notification.event_type,
        destination_path=notification.destination_path,
    )
    if built is None:
        subject, text_body, html_body = ("", "", "")
        block = block or "invalid_frontend_base_url"
    else:
        subject, text_body, html_body = built
    now = datetime.now(timezone.utc)
    queued = block is None
    db.add(
        EmailOutbox(
            recipient_user_id=user.id,
            recipient_email=user.email,
            notification_id=notification.id,
            event_type=notification.event_type,
            event_key=notification.event_key,
            channel=CHANNEL_EMAIL,
            destination_path=notification.destination_path,
            subject=subject,
            text_body=text_body,
            html_body=html_body,
            status=STATUS_QUEUED if queued else STATUS_SUPPRESSED,
            reason=None if queued else block,
            attempt_count=0,
            next_attempt_at=now if queued else None,
            updated_at=now,
        )
    )
