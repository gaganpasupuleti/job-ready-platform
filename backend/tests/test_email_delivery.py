"""Email outbox, worker, and preference tests.

Provider calls in this file use a fake sender or httpx.MockTransport.
They are not real Brevo deliveries.
"""

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.email.brevo import BrevoClient, OutboundEmail, SendResult, safe_reason
from app.email.preferences import make_unsubscribe_token
from app.email.worker import process_once
from app.models.email_notification import EmailOutbox
from app.models.notification import Notification


def _assignment():
    return {
        "title": "Catalog filters",
        "link": "https://github.com/example/catalog-filters",
        "note": "The filter chips are in the repository README.",
    }


def _ticket(description: str):
    return {
        "category": "bug",
        "title": "SQL results do not refresh",
        "description": description,
        "page_path": "/practice/sql",
        "client_request_id": uuid.uuid4().hex,
    }


async def _user_id(client, headers) -> str:
    me = await client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200, me.text
    return me.json()["id"]


async def _rows(user_id: str) -> list[dict]:
    async with AsyncSessionLocal() as session:
        found = (
            await session.scalars(select(EmailOutbox).where(EmailOutbox.recipient_user_id == uuid.UUID(user_id)))
        ).all()
        return [
            {
                "id": row.id,
                "status": row.status,
                "reason": row.reason,
                "attempts": row.attempt_count,
                "text": row.text_body,
                "html": row.html_body,
                "subject": row.subject,
                "message_id": row.provider_message_id,
                "accepted_at": row.accepted_at,
                "event_type": row.event_type,
            }
            for row in found
        ]


async def _notification_count(user_id: str) -> int:
    async with AsyncSessionLocal() as session:
        count = await session.scalar(
            select(func.count()).select_from(Notification).where(Notification.recipient_user_id == uuid.UUID(user_id))
        )
        return int(count or 0)


def _enable(monkeypatch, *, enabled: bool = True, address: str = "notifications@jobready.example", key: str = "not-a-real-key"):
    monkeypatch.setattr(settings, "email_provider", "brevo")
    monkeypatch.setattr(settings, "email_enabled", enabled)
    monkeypatch.setattr(settings, "email_from_address", address)
    monkeypatch.setattr(settings, "email_from_name", "JobReady")
    monkeypatch.setattr(settings, "brevo_api_key", key)
    monkeypatch.setattr(settings, "frontend_base_url", "http://localhost:5173")


async def _park_queued() -> None:
    """Keep this file's worker from sending rows left by another test."""
    async with AsyncSessionLocal() as session:
        rows = (await session.scalars(select(EmailOutbox).where(EmailOutbox.status == "queued"))).all()
        for row in rows:
            row.status = "suppressed"
            row.reason = "email_disabled"
            row.next_attempt_at = None
        await session.commit()


class FakeSender:
    def __init__(self, results: list[SendResult]) -> None:
        self.results = list(results)
        self.calls: list[OutboundEmail] = []

    async def send(self, message: OutboundEmail) -> SendResult:
        self.calls.append(message)
        return self.results.pop(0)


async def _review(client, headers, admin_headers, note: str) -> str:
    created = await client.post("/api/v1/assignments", json=_assignment(), headers=headers)
    assert created.status_code == 201, created.text
    submission_id = created.json()["id"]
    saved = await client.patch(
        f"/api/v1/admin/assignments/{submission_id}",
        json={"review_note": note},
        headers=admin_headers,
    )
    assert saved.status_code == 200, saved.text
    return submission_id


@pytest.mark.asyncio
async def test_disabled_sending_suppresses_the_event_and_later_enable_does_not_send(
    client, student_auth, admin_auth, monkeypatch
):
    headers, _email = student_auth
    user_id = await _user_id(client, headers)
    await _park_queued()
    _enable(monkeypatch, enabled=False)
    note = "Private review text that must stay off the email."
    await _review(client, headers, admin_auth, note)
    rows = await _rows(user_id)
    assert len(rows) == 1
    assert rows[0]["status"] == "suppressed"
    assert rows[0]["reason"] == "email_disabled"
    assert rows[0]["attempts"] == 0
    assert note not in rows[0]["text"]
    assert note not in rows[0]["html"]
    assert await _notification_count(user_id) == 1

    _enable(monkeypatch, enabled=True)
    sender = FakeSender([SendResult("accepted", message_id="<should-not-send@example.test>")])
    tick = await process_once(sender)
    assert tick.provider_calls == 0
    assert tick.skipped_disabled is False
    assert sender.calls == []
    again = await _rows(user_id)
    assert again[0]["status"] == "suppressed"
    assert again[0]["attempts"] == 0
    assert again[0]["message_id"] is None


@pytest.mark.asyncio
async def test_placeholder_configuration_suppresses_even_when_enabled(client, student_auth, admin_auth, monkeypatch):
    headers, _email = student_auth
    user_id = await _user_id(client, headers)
    _enable(monkeypatch, enabled=True, address="notifications@example.com", key="REPLACE_WITH_REAL_BREVO_API_KEY")
    await _review(client, headers, admin_auth, "Another private note that is not emailed.")
    rows = await _rows(user_id)
    assert rows[0]["status"] == "suppressed"
    assert rows[0]["reason"] == "placeholder_configuration"
    assert rows[0]["attempts"] == 0
    sender = FakeSender([])
    tick = await process_once(sender)
    assert tick.skipped_disabled is True
    assert tick.provider_calls == 0
    assert sender.calls == []


@pytest.mark.asyncio
async def test_repeated_review_and_failed_commit_do_not_duplicate_or_leave_email(
    client, student_auth, admin_auth, monkeypatch
):
    headers, _email = student_auth
    user_id = await _user_id(client, headers)
    _enable(monkeypatch, enabled=True)
    created = await client.post("/api/v1/assignments", json=_assignment(), headers=headers)
    submission_id = created.json()["id"]
    note = "Same review saved twice should stay one email."
    for _ in range(2):
        saved = await client.patch(
            f"/api/v1/admin/assignments/{submission_id}",
            json={"review_note": note},
            headers=admin_auth,
        )
        assert saved.status_code == 200, saved.text
    assert len(await _rows(user_id)) == 1
    assert await _notification_count(user_id) == 1

    async def fail_commit(self):
        raise RuntimeError("review commit failed")

    monkeypatch.setattr(AsyncSession, "commit", fail_commit)
    try:
        failed = await client.patch(
            f"/api/v1/admin/assignments/{submission_id}",
            json={"review_note": "This rollback must not leave an email."},
            headers=admin_auth,
        )
    except RuntimeError as exc:
        assert "review commit failed" in str(exc)
    else:
        assert failed.status_code == 500, failed.text
    finally:
        monkeypatch.undo()
        _enable(monkeypatch, enabled=True)
    assert len(await _rows(user_id)) == 1
    assert await _notification_count(user_id) == 1
    stored = await _rows(user_id)
    assert "This rollback must not leave an email." not in stored[0]["text"]


@pytest.mark.asyncio
async def test_worker_accepts_without_calling_it_delivered_and_retries_then_stops(
    client, student_auth, admin_auth, monkeypatch
):
    headers, _email = student_auth
    user_id = await _user_id(client, headers)
    await _park_queued()
    _enable(monkeypatch, enabled=True)
    monkeypatch.setattr(settings, "email_max_attempts", 2)
    monkeypatch.setattr("app.email.worker.retry_delay_seconds", lambda attempt_count: 0 if attempt_count < 2 else None)
    note = "Review text excluded from the provider payload."
    await _review(client, headers, admin_auth, note)
    retry = FakeSender(
        [
            SendResult("retryable", reason="http_503"),
            SendResult("retryable", reason="http_503"),
        ]
    )
    first = await process_once(retry)
    assert first.provider_calls == 1
    assert first.retrying == 1
    assert note not in retry.calls[0].text_body
    assert note not in retry.calls[0].html_body
    waiting = await _rows(user_id)
    assert waiting[0]["status"] == "queued"
    assert waiting[0]["attempts"] == 1
    assert waiting[0]["message_id"] is None

    second = await process_once(retry)
    assert second.failed == 1
    failed = await _rows(user_id)
    assert failed[0]["status"] == "failed"
    assert failed[0]["reason"] == "provider_retry_exhausted"
    assert failed[0]["attempts"] == 2
    assert failed[0]["message_id"] is None
    third = await process_once(FakeSender([]))
    assert third.provider_calls == 0

    created = await client.post("/api/v1/assignments", json=_assignment(), headers=headers)
    submission_id = created.json()["id"]
    saved = await client.patch(
        f"/api/v1/admin/assignments/{submission_id}",
        json={"review_note": "A different review that can be accepted."},
        headers=admin_auth,
    )
    assert saved.status_code == 200, saved.text
    accepted = FakeSender([SendResult("accepted", message_id="<accepted-id@example.test>")])
    tick = await process_once(accepted)
    assert tick.accepted == 1
    assert tick.provider_calls == 1
    rows = await _rows(user_id)
    accepted_row = next(row for row in rows if row["message_id"] == "<accepted-id@example.test>")
    assert accepted_row["status"] == "accepted"
    assert accepted_row["accepted_at"] is not None
    assert accepted_row["status"] != "delivered"


@pytest.mark.asyncio
async def test_ambiguous_timeout_and_expired_claim_are_not_retried(client, student_auth, admin_auth, monkeypatch):
    headers, _email = student_auth
    user_id = await _user_id(client, headers)
    await _park_queued()
    _enable(monkeypatch, enabled=True)
    await _review(client, headers, admin_auth, "Timeout review stays private.")
    sender = FakeSender([SendResult("ambiguous", reason="provider_timeout")])
    tick = await process_once(sender)
    assert tick.ambiguous >= 1
    assert tick.provider_calls == 1
    rows = await _rows(user_id)
    assert rows[0]["status"] == "ambiguous"
    assert rows[0]["reason"] == "provider_timeout"
    assert rows[0]["attempts"] == 1
    again = await process_once(FakeSender([]))
    assert again.provider_calls == 0
    assert (await _rows(user_id))[0]["status"] == "ambiguous"

    created = await client.post("/api/v1/assignments", json=_assignment(), headers=headers)
    submission_id = created.json()["id"]
    await client.patch(
        f"/api/v1/admin/assignments/{submission_id}",
        json={"review_note": "Crash before the provider result is saved."},
        headers=admin_auth,
    )
    async with AsyncSessionLocal() as session:
        pending = (
            await session.scalars(
                select(EmailOutbox).where(
                    EmailOutbox.recipient_user_id == uuid.UUID(user_id),
                    EmailOutbox.status == "queued",
                )
            )
        ).all()
        assert len(pending) == 1
        pending[0].status = "sending"
        pending[0].claimed_at = datetime.now(timezone.utc) - timedelta(hours=1)
        pending[0].claim_token = uuid.uuid4()
        await session.commit()
    recovered = await process_once(FakeSender([]))
    assert recovered.provider_calls == 0
    statuses = {row["status"] for row in await _rows(user_id)}
    assert "queued" not in statuses
    assert "ambiguous" in statuses


@pytest.mark.asyncio
async def test_disabled_worker_does_not_claim_or_spend_attempts(client, student_auth, admin_auth, monkeypatch):
    headers, _email = student_auth
    user_id = await _user_id(client, headers)
    await _park_queued()
    _enable(monkeypatch, enabled=True)
    await _review(client, headers, admin_auth, "Queued while enabled, then paused.")
    _enable(monkeypatch, enabled=False)
    sender = FakeSender([SendResult("accepted", message_id="<paused@example.test>")])
    tick = await process_once(sender)
    assert tick.skipped_disabled is True
    assert tick.claimed == 0
    assert tick.provider_calls == 0
    assert sender.calls == []
    rows = await _rows(user_id)
    assert rows[0]["status"] == "queued"
    assert rows[0]["attempts"] == 0


@pytest.mark.asyncio
async def test_concurrent_workers_send_one_queued_event(client, student_auth, admin_auth, monkeypatch):
    headers, _email = student_auth
    user_id = await _user_id(client, headers)
    await _park_queued()
    _enable(monkeypatch, enabled=True)
    await _review(client, headers, admin_auth, "Only one worker may claim this review.")
    gate = asyncio.Event()

    class SlowSender:
        def __init__(self) -> None:
            self.calls: list[OutboundEmail] = []

        async def send(self, message: OutboundEmail) -> SendResult:
            self.calls.append(message)
            await gate.wait()
            return SendResult("accepted", message_id=f"<{message.outbox_id}@example.test>")

    left = SlowSender()
    right = SlowSender()
    task_left = asyncio.create_task(process_once(left))
    task_right = asyncio.create_task(process_once(right))
    for _ in range(50):
        if left.calls or right.calls:
            break
        await asyncio.sleep(0.05)
    gate.set()
    ticks = await asyncio.gather(task_left, task_right)
    assert sum(tick.provider_calls for tick in ticks) == 1
    assert len(left.calls) + len(right.calls) == 1
    rows = await _rows(user_id)
    assert rows[0]["status"] == "accepted"
    assert rows[0]["attempts"] == 1


@pytest.mark.asyncio
async def test_preference_off_keeps_the_in_app_item_and_is_rechecked_before_send(
    client, student_auth, admin_auth, monkeypatch
):
    headers, _email = student_auth
    user_id = await _user_id(client, headers)
    other = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"other_{uuid.uuid4().hex[:8]}@example.com",
            "username": f"other_{uuid.uuid4().hex[:8]}",
            "full_name": "Other Student",
            "password": "Student123!",
        },
    )
    other_headers = {"Authorization": f"Bearer {other.json()['access_token']}"}
    await _park_queued()
    _enable(monkeypatch, enabled=True)
    turned_off = await client.patch(
        "/api/v1/notifications/email-preferences",
        json={"assignment_review_enabled": False},
        headers=headers,
    )
    assert turned_off.status_code == 200, turned_off.text
    assert turned_off.json()["support_reply_enabled"] is True
    await _review(client, headers, admin_auth, "Preference blocks the email, not the bell.")
    rows = await _rows(user_id)
    assert rows[0]["status"] == "suppressed"
    assert rows[0]["reason"] == "preference_off"
    assert await _notification_count(user_id) == 1
    page = await client.get("/api/v1/notifications", headers=headers)
    assert page.json()["items"][0]["message"] == "Your assignment has been reviewed."

    created = await client.post("/api/v1/assignments", json=_assignment(), headers=headers)
    submission_id = created.json()["id"]
    await client.patch(
        "/api/v1/notifications/email-preferences",
        json={"assignment_review_enabled": True},
        headers=headers,
    )
    await client.patch(
        f"/api/v1/admin/assignments/{submission_id}",
        json={"review_note": "Queued first, then the student turns email off."},
        headers=admin_auth,
    )
    await client.patch(
        "/api/v1/notifications/email-preferences",
        json={"assignment_review_enabled": False},
        headers=headers,
    )
    sender = FakeSender([SendResult("accepted", message_id="<blocked@example.test>")])
    tick = await process_once(sender)
    assert tick.provider_calls == 0
    assert sender.calls == []
    queued = [row for row in await _rows(user_id) if row["status"] != "suppressed"]
    assert queued == []

    own = await client.get("/api/v1/notifications/email-preferences", headers=headers)
    theirs = await client.get("/api/v1/notifications/email-preferences", headers=other_headers)
    assert own.json()["assignment_review_enabled"] is False
    assert theirs.json()["assignment_review_enabled"] is True
    leaked = await client.patch(
        "/api/v1/notifications/email-preferences",
        json={"assignment_review_enabled": True, "support_reply_enabled": False},
        headers=headers,
    )
    assert leaked.status_code == 200
    theirs_again = await client.get("/api/v1/notifications/email-preferences", headers=other_headers)
    assert theirs_again.json() == {"assignment_review_enabled": True, "support_reply_enabled": True}
    anonymous = await client.get("/api/v1/notifications/email-preferences")
    assert anonymous.status_code == 401


@pytest.mark.asyncio
async def test_support_reply_emails_the_owner_only_and_unsubscribe_is_scoped(
    client, student_auth, admin_auth, monkeypatch
):
    headers, _email = student_auth
    user_id = await _user_id(client, headers)
    _enable(monkeypatch, enabled=True)
    description = "Private ticket description that must not be emailed."
    reply = "Private admin reply that must not be emailed."
    opened = await client.post("/api/v1/support/tickets", json=_ticket(description), headers=headers)
    assert opened.status_code == 200, opened.text
    ticket_id = opened.json()["id"]
    request_id = uuid.uuid4().hex
    admin_reply = await client.post(
        f"/api/v1/admin/support/tickets/{ticket_id}/replies",
        json={"body": reply, "client_request_id": request_id},
        headers=admin_auth,
    )
    assert admin_reply.status_code == 200, admin_reply.text
    repeated = await client.post(
        f"/api/v1/admin/support/tickets/{ticket_id}/replies",
        json={"body": reply, "client_request_id": request_id},
        headers=admin_auth,
    )
    assert repeated.status_code == 200, repeated.text
    student_reply = await client.post(
        f"/api/v1/support/tickets/{ticket_id}/replies",
        json={"body": "Student follow-up that must not email anyone.", "client_request_id": uuid.uuid4().hex},
        headers=headers,
    )
    assert student_reply.status_code == 200, student_reply.text
    status = await client.patch(
        f"/api/v1/admin/support/tickets/{ticket_id}",
        json={"status": "in_review", "client_request_id": uuid.uuid4().hex},
        headers=admin_auth,
    )
    assert status.status_code == 200, status.text
    rows = await _rows(user_id)
    assert len(rows) == 1
    assert rows[0]["event_type"] == "support_reply"
    assert rows[0]["status"] == "queued"
    assert description not in rows[0]["text"]
    assert reply not in rows[0]["text"]
    assert "http://localhost:5173/support/requests/" in rows[0]["text"]

    other = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"mail_{uuid.uuid4().hex[:8]}@example.com",
            "username": f"mail_{uuid.uuid4().hex[:8]}",
            "full_name": "Mail Other",
            "password": "Student123!",
        },
    )
    other_headers = {"Authorization": f"Bearer {other.json()['access_token']}"}
    other_id = await _user_id(client, other_headers)
    token = make_unsubscribe_token(uuid.UUID(user_id), "support_reply")
    stopped = await client.post("/api/v1/notifications/email-unsubscribe", json={"token": token})
    assert stopped.status_code == 200, stopped.text
    assert stopped.json()["support_reply_enabled"] is False
    owner = await client.get("/api/v1/notifications/email-preferences", headers=headers)
    assert owner.json()["support_reply_enabled"] is False
    assert owner.json()["assignment_review_enabled"] is True
    untouched = await client.get("/api/v1/notifications/email-preferences", headers=other_headers)
    assert untouched.json()["support_reply_enabled"] is True
    assert await _notification_count(other_id) == 0
    bad = await client.post("/api/v1/notifications/email-unsubscribe", json={"token": "not-a-token"})
    assert bad.status_code == 400


def test_provider_errors_keep_only_reason_codes(monkeypatch):
    sentinel = "SECRET-SENTINEL"
    assert safe_reason(f"api-key={sentinel}") == "provider_error"
    assert sentinel not in safe_reason(f"api-key={sentinel}")
    _enable(monkeypatch, enabled=True, key=sentinel)

    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["key"] = request.headers.get("api-key")
        body = request.content.decode()
        seen["body"] = body
        assert "private review note" not in body
        assert sentinel not in body
        return httpx.Response(201, json={"messageId": "<mock-id@example.test>"})

    message = OutboundEmail(
        outbox_id=str(uuid.uuid4()),
        recipient_email="student@example.com",
        recipient_name="Student",
        subject="Your assignment has been reviewed",
        text_body="Your assignment has been reviewed.",
        html_body="<p>Your assignment has been reviewed.</p>",
    )

    async def _send(transport):
        return await BrevoClient(transport=transport).send(message)

    sent = asyncio.run(_send(httpx.MockTransport(handler)))
    assert sent.outcome == "accepted"
    assert sent.message_id == "<mock-id@example.test>"
    assert seen["key"] == sentinel
    assert sentinel not in seen["body"]

    def timeout(_request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timed out")

    timed = asyncio.run(_send(httpx.MockTransport(timeout)))
    assert timed.outcome == "ambiguous"
    assert timed.reason == "provider_timeout"
    assert sentinel not in timed.reason

    def rejected(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"message": sentinel})

    denied = asyncio.run(_send(httpx.MockTransport(rejected)))
    assert denied.outcome == "rejected"
    assert denied.reason == "http_400"
    assert sentinel not in denied.reason
