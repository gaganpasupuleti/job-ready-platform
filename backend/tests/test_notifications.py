import asyncio
import uuid

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.manual_assignment import ManualAssignmentSubmission
from app.models.notification import (
    ASSIGNMENT_REVIEW_MESSAGE,
    SUPPORT_REPLY_MESSAGE,
    Notification,
)
from app.models.user import User


def _assignment():
    return {
        "title": "Catalog filters",
        "link": "https://github.com/example/catalog-filters",
        "note": "The filter chips are in the repository README.",
    }


def _ticket():
    return {
        "category": "bug",
        "title": "SQL results do not refresh",
        "description": "The results panel stays on the previous query after I submit again.",
        "page_path": "/practice/sql",
        "client_request_id": uuid.uuid4().hex,
    }


async def _user_id(client, headers) -> str:
    me = await client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200, me.text
    return me.json()["id"]


async def _notifications(client, headers) -> dict:
    response = await client.get("/api/v1/notifications?limit=20", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


async def _count_rows(user_id: str) -> int:
    async with AsyncSessionLocal() as session:
        count = await session.scalar(
            select(func.count()).select_from(Notification).where(Notification.recipient_user_id == uuid.UUID(user_id))
        )
        return int(count or 0)


@pytest.mark.asyncio
async def test_assignment_review_notifies_owner_once_and_hides_the_note(client, student_auth, admin_auth):
    headers, _email = student_auth
    user_id = await _user_id(client, headers)
    created = await client.post("/api/v1/assignments", json=_assignment(), headers=headers)
    assert created.status_code == 201, created.text
    submission_id = created.json()["id"]
    note = "Looks complete. The private review note stays on the submission."

    first = await client.patch(
        f"/api/v1/admin/assignments/{submission_id}",
        json={"review_note": note},
        headers=admin_auth,
    )
    second = await client.patch(
        f"/api/v1/admin/assignments/{submission_id}",
        json={"review_note": note},
        headers=admin_auth,
    )
    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert await _count_rows(user_id) == 1

    page = await _notifications(client, headers)
    assert len(page["items"]) == 1
    item = page["items"][0]
    assert item["event_type"] == "assignment_review"
    assert item["message"] == ASSIGNMENT_REVIEW_MESSAGE
    assert note not in item["message"]
    assert item["destination_path"] == f"/practice/projects#submission-{submission_id}"
    assert item["read_at"] is None
    unread = await client.get("/api/v1/notifications/unread-count", headers=headers)
    assert unread.json()["count"] == 1
    admin_page = await _notifications(client, admin_auth)
    assert all(entry["id"] != item["id"] for entry in admin_page["items"])


@pytest.mark.asyncio
async def test_changed_review_creates_another_notification(client, student_auth, admin_auth):
    headers, _email = student_auth
    created = await client.post("/api/v1/assignments", json=_assignment(), headers=headers)
    submission_id = created.json()["id"]
    first_note = "First review of the repository layout."
    second_note = "Updated review after the student pushed a fix."
    await client.patch(
        f"/api/v1/admin/assignments/{submission_id}",
        json={"review_note": first_note},
        headers=admin_auth,
    )
    changed = await client.patch(
        f"/api/v1/admin/assignments/{submission_id}",
        json={"review_note": second_note},
        headers=admin_auth,
    )
    assert changed.status_code == 200, changed.text
    page = await _notifications(client, headers)
    assert len(page["items"]) == 2
    assert {item["message"] for item in page["items"]} == {ASSIGNMENT_REVIEW_MESSAGE}
    joined = " ".join(item["message"] for item in page["items"])
    assert first_note not in joined
    assert second_note not in joined


@pytest.mark.asyncio
async def test_concurrent_same_review_creates_one_notification(client, student_auth, admin_auth):
    headers, _email = student_auth
    user_id = await _user_id(client, headers)
    created = await client.post("/api/v1/assignments", json=_assignment(), headers=headers)
    submission_id = created.json()["id"]
    note = "Concurrent review should stay a single notification."
    results = await asyncio.gather(
        client.patch(
            f"/api/v1/admin/assignments/{submission_id}",
            json={"review_note": note},
            headers=admin_auth,
        ),
        client.patch(
            f"/api/v1/admin/assignments/{submission_id}",
            json={"review_note": note},
            headers=admin_auth,
        ),
    )
    assert [result.status_code for result in results] == [200, 200]
    assert await _count_rows(user_id) == 1


@pytest.mark.asyncio
async def test_failed_review_does_not_create_a_notification(client, student_auth, admin_auth, monkeypatch):
    headers, _email = student_auth
    user_id = await _user_id(client, headers)
    created = await client.post("/api/v1/assignments", json=_assignment(), headers=headers)
    submission_id = created.json()["id"]
    rejected = await client.patch(
        f"/api/v1/admin/assignments/{submission_id}",
        json={"review_note": "no"},
        headers=admin_auth,
    )
    assert rejected.status_code == 422
    assert await _count_rows(user_id) == 0
    mine = await client.get("/api/v1/assignments", headers=headers)
    saved = next(item for item in mine.json() if item["id"] == submission_id)
    assert saved["status"] == "awaiting_review"
    assert saved["review_note"] is None

    async def fail_commit(self):
        raise RuntimeError("review commit failed")

    monkeypatch.setattr(AsyncSession, "commit", fail_commit)
    try:
        failed = await client.patch(
            f"/api/v1/admin/assignments/{submission_id}",
            json={"review_note": "This note must roll back with its notification."},
            headers=admin_auth,
        )
    except RuntimeError as exc:
        assert "review commit failed" in str(exc)
    else:
        assert failed.status_code == 500, failed.text
    finally:
        monkeypatch.undo()
    assert await _count_rows(user_id) == 0
    mine = await client.get("/api/v1/assignments", headers=headers)
    saved = next(item for item in mine.json() if item["id"] == submission_id)
    assert saved["status"] == "awaiting_review"
    assert saved["review_note"] is None


@pytest.mark.asyncio
async def test_historical_review_is_not_backfilled(client, student_auth):
    headers, _email = student_auth
    user_id = await _user_id(client, headers)
    async with AsyncSessionLocal() as session:
        session.add(
            ManualAssignmentSubmission(
                user_id=uuid.UUID(user_id),
                title="Historical submission",
                link="https://github.com/example/historical",
                status="reviewed",
                review_note="This review existed before notifications.",
            )
        )
        await session.commit()
    page = await _notifications(client, headers)
    assert page["items"] == []
    assert await _count_rows(user_id) == 0


@pytest.mark.asyncio
async def test_admin_reply_notifies_the_owner_once(client, student_auth, admin_auth):
    headers, _email = student_auth
    user_id = await _user_id(client, headers)
    created = await client.post("/api/v1/support/tickets", json=_ticket(), headers=headers)
    assert created.status_code == 200, created.text
    ticket_id = created.json()["id"]
    body = "Thanks. The private reply text stays on the ticket."
    request_id = uuid.uuid4().hex
    first = await client.post(
        f"/api/v1/admin/support/tickets/{ticket_id}/replies",
        json={"body": body, "client_request_id": request_id},
        headers=admin_auth,
    )
    second = await client.post(
        f"/api/v1/admin/support/tickets/{ticket_id}/replies",
        json={"body": body, "client_request_id": request_id},
        headers=admin_auth,
    )
    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert await _count_rows(user_id) == 1
    page = await _notifications(client, headers)
    assert len(page["items"]) == 1
    item = page["items"][0]
    assert item["event_type"] == "support_reply"
    assert item["message"] == SUPPORT_REPLY_MESSAGE
    assert body not in item["message"]
    assert item["destination_path"] == f"/support/requests/{ticket_id}"

    follow = await client.post(
        f"/api/v1/support/tickets/{ticket_id}/replies",
        json={"body": "I tried the page again.", "client_request_id": uuid.uuid4().hex},
        headers=headers,
    )
    assert follow.status_code == 200, follow.text
    status = await client.patch(
        f"/api/v1/admin/support/tickets/{ticket_id}",
        json={"status": "in_review", "client_request_id": uuid.uuid4().hex},
        headers=admin_auth,
    )
    assert status.status_code == 200, status.text
    assert await _count_rows(user_id) == 1


@pytest.mark.asyncio
async def test_notification_reads_are_scoped_and_idempotent(client, student_auth, admin_auth):
    headers, _email = student_auth
    other_email = f"other_{uuid.uuid4().hex[:8]}@example.com"
    registered = await client.post(
        "/api/v1/auth/register",
        json={
            "email": other_email,
            "username": f"other_{uuid.uuid4().hex[:8]}",
            "full_name": "Other Student",
            "password": "Student123!",
        },
    )
    assert registered.status_code == 200, registered.text
    other = {"Authorization": f"Bearer {registered.json()['access_token']}"}

    created = await client.post("/api/v1/assignments", json=_assignment(), headers=headers)
    submission_id = created.json()["id"]
    for note in (
        "Review one for pagination.",
        "Review two for pagination.",
        "Review three for pagination.",
    ):
        saved = await client.patch(
            f"/api/v1/admin/assignments/{submission_id}",
            json={"review_note": note},
            headers=admin_auth,
        )
        assert saved.status_code == 200, saved.text

    first_page = await client.get("/api/v1/notifications?limit=2", headers=headers)
    assert first_page.status_code == 200, first_page.text
    body = first_page.json()
    assert len(body["items"]) == 2
    assert body["next_cursor"]
    second_page = await client.get(
        "/api/v1/notifications",
        params={"limit": 2, "cursor": body["next_cursor"]},
        headers=headers,
    )
    assert second_page.status_code == 200, second_page.text
    assert len(second_page.json()["items"]) == 1
    assert second_page.json()["next_cursor"] is None
    seen = {item["id"] for item in body["items"] + second_page.json()["items"]}
    assert len(seen) == 3

    hidden = await client.get("/api/v1/notifications", headers=other)
    assert hidden.json()["items"] == []
    foreign = await client.post(f"/api/v1/notifications/{body['items'][0]['id']}/read", headers=other)
    assert foreign.status_code == 404
    other_unread = await client.get("/api/v1/notifications/unread-count", headers=other)
    assert other_unread.json()["count"] == 0

    marked = await client.post(f"/api/v1/notifications/{body['items'][0]['id']}/read", headers=headers)
    assert marked.status_code == 200, marked.text
    assert marked.json()["read_at"]
    again = await client.post(f"/api/v1/notifications/{body['items'][0]['id']}/read", headers=headers)
    assert again.status_code == 200
    assert again.json()["read_at"] == marked.json()["read_at"]
    unread = await client.get("/api/v1/notifications/unread-count", headers=headers)
    assert unread.json()["count"] == 2

    cleared = await client.post("/api/v1/notifications/read-all", headers=headers)
    assert cleared.status_code == 200, cleared.text
    assert cleared.json()["count"] == 0
    cleared_again = await client.post("/api/v1/notifications/read-all", headers=headers)
    assert cleared_again.json()["count"] == 0
    unread = await client.get("/api/v1/notifications/unread-count", headers=headers)
    assert unread.json()["count"] == 0


@pytest.mark.asyncio
async def test_notifications_require_auth_and_reject_a_bad_cursor(client, student_auth):
    anonymous = await client.get("/api/v1/notifications")
    assert anonymous.status_code == 401
    bad = await client.get("/api/v1/notifications?cursor=not-a-cursor", headers=student_auth[0])
    assert bad.status_code == 400
