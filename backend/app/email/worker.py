"""Database outbox worker.

Events created while EMAIL_ENABLED is false, or while the sender or API key
is still a placeholder, are stored as suppressed. They are not queued and
are not sent when sending is turned on later. Only an event created while
email_can_send is true, and while that user's category preference is on,
is inserted as queued.

While email_can_send is false the worker does not claim queued rows, does
not call Brevo, and does not increment attempt_count. A row left in `sending`
from an earlier crash is still moved to `ambiguous` so it cannot be sent
twice. That recovery does not count as a retry.

Duplicate-delivery limits:
- One outbox row per channel and event key. A retried source request does
  not create a second email.
- Brevo POST /v3/smtp/email does not document an idempotency key that
  suppresses a duplicate POST. Timeouts, connection errors, HTTP 408, and
  a claim that expires before the result is saved are `ambiguous` and are
  not retried. A message can be missed if the worker dies after claiming
  and before Brevo accepts it.
- HTTP 429 and 500/502/503/504 are retried on a bounded schedule. A 5xx
  returned after Brevo had already accepted the message could theoretically
  deliver twice, because the provider does not dedupe that retry. Those
  responses are the only automatic retries.
- `accepted` stores provider_message_id. Nothing in this worker is labeled
  delivered. Delivery webhooks are not consumed.

Run from the backend directory:
  python -m app.email.worker --once
  python -m app.email.worker

Environment names used when sending is enabled: EMAIL_PROVIDER, EMAIL_ENABLED,
EMAIL_FROM_ADDRESS, EMAIL_FROM_NAME, BREVO_API_KEY, FRONTEND_BASE_URL.
Optional tuning names: EMAIL_HTTP_TIMEOUT_SECONDS, EMAIL_MAX_ATTEMPTS,
EMAIL_WORKER_BATCH_SIZE, EMAIL_CLAIM_TIMEOUT_SECONDS. DATABASE_URL selects
the application database. Do not put BREVO_API_KEY on the frontend.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.email.brevo import BrevoClient, OutboundEmail, SendResult, safe_reason
from app.email.preferences import category_enabled
from app.models.email_notification import (
    STATUS_ACCEPTED,
    STATUS_AMBIGUOUS,
    STATUS_FAILED,
    STATUS_QUEUED,
    STATUS_SENDING,
    STATUS_SUPPRESSED,
    EmailOutbox,
    EmailPreference,
)
from app.models.user import User

logger = logging.getLogger(__name__)
_BACKOFF_SECONDS = (60, 300, 900, 3600)


@dataclass
class WorkerTick:
    claimed: int = 0
    provider_calls: int = 0
    accepted: int = 0
    retrying: int = 0
    failed: int = 0
    ambiguous: int = 0
    suppressed: int = 0
    skipped_disabled: bool = False


def retry_delay_seconds(attempt_count: int) -> int | None:
    if attempt_count >= settings.email_max_attempts:
        return None
    index = min(max(attempt_count, 1) - 1, len(_BACKOFF_SECONDS) - 1)
    return _BACKOFF_SECONDS[index]


def _claim_timeout() -> timedelta:
    floor = int(settings.email_http_timeout_seconds) + 15
    return timedelta(seconds=max(settings.email_claim_timeout_seconds, floor))


async def process_once(sender: BrevoClient | None = None) -> WorkerTick:
    now = datetime.now(timezone.utc)
    tick = WorkerTick()
    client = sender or BrevoClient()
    async with AsyncSessionLocal() as session:
        claimed = await _claim_batch(session, now, tick)
        await session.commit()
    for outbox_id, token in claimed:
        await _deliver(outbox_id, token, client, tick)
    return tick


async def _claim_batch(session: AsyncSession, now: datetime, tick: WorkerTick) -> list[tuple[uuid.UUID, uuid.UUID]]:
    cutoff = now - _claim_timeout()
    recovered = await session.execute(
        update(EmailOutbox)
        .where(EmailOutbox.status == STATUS_SENDING, EmailOutbox.claimed_at.is_not(None), EmailOutbox.claimed_at < cutoff)
        .values(status=STATUS_AMBIGUOUS, reason="claim_expired", claim_token=None, updated_at=now)
    )
    tick.ambiguous += int(recovered.rowcount or 0)
    if not settings.email_can_send:
        tick.skipped_disabled = True
        return []
    rows = (
        await session.scalars(
            select(EmailOutbox)
            .where(
                EmailOutbox.status == STATUS_QUEUED,
                or_(EmailOutbox.next_attempt_at.is_(None), EmailOutbox.next_attempt_at <= now),
            )
            .order_by(EmailOutbox.next_attempt_at.asc(), EmailOutbox.id.asc())
            .limit(max(settings.email_worker_batch_size, 1))
            .with_for_update(skip_locked=True)
        )
    ).all()
    claimed: list[tuple[uuid.UUID, uuid.UUID]] = []
    for row in rows:
        token = uuid.uuid4()
        row.status = STATUS_SENDING
        row.claimed_at = now
        row.claim_token = token
        row.updated_at = now
        claimed.append((row.id, token))
    tick.claimed = len(claimed)
    return claimed


async def _deliver(outbox_id: uuid.UUID, token: uuid.UUID, sender: BrevoClient, tick: WorkerTick) -> None:
    async with AsyncSessionLocal() as session:
        row = await session.scalar(
            select(EmailOutbox).where(
                EmailOutbox.id == outbox_id,
                EmailOutbox.claim_token == token,
                EmailOutbox.status == STATUS_SENDING,
            )
        )
        if row is None:
            return
        now = datetime.now(timezone.utc)
        if not settings.email_can_send:
            row.status = STATUS_QUEUED
            row.claim_token = None
            row.claimed_at = None
            row.updated_at = now
            await session.commit()
            return
        preference = await session.get(EmailPreference, row.recipient_user_id)
        if not category_enabled(preference, row.event_type):
            row.status = STATUS_SUPPRESSED
            row.reason = "preference_off"
            row.claim_token = None
            row.next_attempt_at = None
            row.updated_at = now
            tick.suppressed += 1
            await session.commit()
            return
        user = await session.get(User, row.recipient_user_id)
        message = OutboundEmail(
            outbox_id=str(row.id),
            recipient_email=row.recipient_email,
            recipient_name=(user.full_name or user.username) if user else "",
            subject=row.subject,
            text_body=row.text_body,
            html_body=row.html_body,
        )
        tick.provider_calls += 1
        result = await sender.send(message)
        _record(row, result, now, tick)
        await session.commit()


def _record(row: EmailOutbox, result: SendResult, now: datetime, tick: WorkerTick) -> None:
    reason = safe_reason(result.reason)
    row.claim_token = None
    row.updated_at = now
    if result.outcome == "accepted" and result.message_id:
        row.attempt_count += 1
        row.status = STATUS_ACCEPTED
        row.reason = None
        row.provider_message_id = result.message_id
        row.accepted_at = now
        row.next_attempt_at = None
        tick.accepted += 1
        logger.info("email outbox accepted id=%s", row.id)
        return
    if result.outcome == "ambiguous":
        row.attempt_count += 1
        row.status = STATUS_AMBIGUOUS
        row.reason = reason
        row.next_attempt_at = None
        tick.ambiguous += 1
        logger.info("email outbox ambiguous id=%s reason=%s", row.id, reason)
        return
    row.attempt_count += 1
    delay = retry_delay_seconds(row.attempt_count) if result.outcome == "retryable" else None
    if delay is None:
        row.status = STATUS_FAILED
        row.reason = "provider_retry_exhausted" if result.outcome == "retryable" else reason
        row.next_attempt_at = None
        tick.failed += 1
        logger.info("email outbox failed id=%s reason=%s", row.id, row.reason)
        return
    row.status = STATUS_QUEUED
    row.reason = reason
    row.claimed_at = None
    row.next_attempt_at = now + timedelta(seconds=delay)
    tick.retrying += 1
    logger.info("email outbox retry scheduled id=%s reason=%s", row.id, reason)


async def _run(once: bool, poll_seconds: float) -> None:
    while True:
        tick = await process_once()
        logger.info(
            "email worker tick claimed=%s calls=%s accepted=%s disabled=%s",
            tick.claimed,
            tick.provider_calls,
            tick.accepted,
            tick.skipped_disabled,
        )
        if once:
            return
        await asyncio.sleep(poll_seconds)


def main() -> None:
    parser = argparse.ArgumentParser(description="Send queued JobReady email without calling Brevo while disabled.")
    parser.add_argument("--once", action="store_true", help="Process one batch and exit.")
    parser.add_argument("--poll-seconds", type=float, default=15.0)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    asyncio.run(_run(args.once, args.poll_seconds))


if __name__ == "__main__":
    main()
