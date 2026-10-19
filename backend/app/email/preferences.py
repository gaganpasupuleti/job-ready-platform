"""Signed, single-purpose unsubscribe tokens and preference reads.

The token is not an access token. It names one user and one email category.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppException
from app.models.email_notification import EmailPreference
from app.models.notification import ASSIGNMENT_REVIEW, EVENT_TYPES, SUPPORT_REPLY
from app.models.user import User
from app.schemas.email_preference import EmailPreferenceUpdate, EmailPreferences

_TOKEN_TTL = timedelta(days=90)


def category_enabled(row: EmailPreference | None, event_type: str) -> bool:
    if row is None:
        return True
    if event_type == ASSIGNMENT_REVIEW:
        return row.assignment_review_enabled
    if event_type == SUPPORT_REPLY:
        return row.support_reply_enabled
    return False


def make_unsubscribe_token(user_id: UUID, category: str, *, now: datetime | None = None) -> str:
    if category not in EVENT_TYPES:
        raise AppException("Unknown email category", status_code=400)
    issued = now or datetime.now(timezone.utc)
    expires = int((issued + _TOKEN_TTL).timestamp())
    payload = f"{user_id}.{category}.{expires}"
    signature = hmac.new(settings.jwt_secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{payload}.{signature}".encode()).decode().rstrip("=")


def read_unsubscribe_token(token: str, *, now: datetime | None = None) -> tuple[UUID, str]:
    try:
        padded = token + ("=" * (-len(token) % 4))
        raw = base64.urlsafe_b64decode(padded.encode()).decode()
        user_raw, category, expires_raw, signature = raw.split(".")
        payload = f"{user_raw}.{category}.{expires_raw}"
        expected = hmac.new(settings.jwt_secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise ValueError
        if category not in EVENT_TYPES:
            raise ValueError
        if int(expires_raw) < int((now or datetime.now(timezone.utc)).timestamp()):
            raise AppException("This unsubscribe link has expired", status_code=400)
        return UUID(user_raw), category
    except AppException:
        raise
    except (ValueError, UnicodeError):
        raise AppException("This unsubscribe link is not valid", status_code=400) from None


class EmailPreferenceService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_for_user(self, user: User) -> EmailPreferences:
        row = await self.db.get(EmailPreference, user.id)
        return EmailPreferences(
            assignment_review_enabled=category_enabled(row, ASSIGNMENT_REVIEW),
            support_reply_enabled=category_enabled(row, SUPPORT_REPLY),
        )

    async def update_for_user(self, user: User, payload: EmailPreferenceUpdate) -> EmailPreferences:
        if payload.assignment_review_enabled is None and payload.support_reply_enabled is None:
            raise AppException("Choose an email preference to update", status_code=400)
        row = await self._row(user.id)
        if payload.assignment_review_enabled is not None:
            row.assignment_review_enabled = payload.assignment_review_enabled
        if payload.support_reply_enabled is not None:
            row.support_reply_enabled = payload.support_reply_enabled
        row.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        return await self.get_for_user(user)

    async def unsubscribe(self, token: str) -> EmailPreferences:
        user_id, category = read_unsubscribe_token(token)
        if await self.db.get(User, user_id) is None:
            raise AppException("This unsubscribe link is not valid", status_code=400)
        row = await self._row(user_id)
        if category == ASSIGNMENT_REVIEW:
            row.assignment_review_enabled = False
        else:
            row.support_reply_enabled = False
        row.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        return EmailPreferences(
            assignment_review_enabled=row.assignment_review_enabled,
            support_reply_enabled=row.support_reply_enabled,
        )

    async def _row(self, user_id: UUID) -> EmailPreference:
        row = await self.db.get(EmailPreference, user_id)
        if row is None:
            row = EmailPreference(user_id=user_id)
            self.db.add(row)
            await self.db.flush()
        return row
