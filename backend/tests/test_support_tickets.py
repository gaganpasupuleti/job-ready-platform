import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import update

from app.db.session import AsyncSessionLocal
from app.models.enums import UserRole
from app.models.user import User
from app.services.support_ticket_service import HOURLY_TICKET_LIMIT


def _ticket(page_path="/practice/sql", **overrides):
    payload = {
        "category": "bug",
        "title": "SQL results do not refresh",
        "description": "The results panel stays on the previous query after I submit again.",
        "page_path": page_path,
        "client_request_id": uuid.uuid4().hex,
    }
    payload.update(overrides)
    return payload


async def _register(client, role_name="student"):
    suffix = uuid.uuid4().hex[:8]
    email = f"{role_name}_{suffix}@example.com"
    password = "Student123!"
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": f"{role_name}_{suffix}",
            "full_name": f"{role_name.title()} Person",
            "password": password,
        },
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}, email, password


@pytest.mark.asyncio
async def test_student_ticket_persists_for_owner_only(client, student_auth):
    headers, _email = student_auth
    other, _other_email, _password = await _register(client)
    created = await client.post("/api/v1/support/tickets", json=_ticket(), headers=headers)
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["reference"].startswith("SF-")
    assert body["page_path"] == "/practice/sql"
    assert body["status"] == "new"
    assert "token" not in body["page_path"]

    listed = await client.get("/api/v1/support/tickets", headers=headers)
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [body["id"]]

    detail = await client.get(f"/api/v1/support/tickets/{body['id']}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["description"] == _ticket()["description"]

    hidden = await client.get(f"/api/v1/support/tickets/{body['id']}", headers=other)
    assert hidden.status_code == 404
    other_list = await client.get("/api/v1/support/tickets", headers=other)
    assert other_list.json() == []
    foreign_reply = await client.post(
        f"/api/v1/support/tickets/{body['id']}/replies",
        json={"body": "This is not my ticket.", "client_request_id": uuid.uuid4().hex},
        headers=other,
    )
    assert foreign_reply.status_code == 404


@pytest.mark.asyncio
async def test_duplicate_create_returns_the_same_ticket(client, student_auth):
    headers, _email = student_auth
    payload = _ticket()
    first = await client.post("/api/v1/support/tickets", json=payload, headers=headers)
    second = await client.post("/api/v1/support/tickets", json=payload, headers=headers)
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    listed = await client.get("/api/v1/support/tickets", headers=headers)
    assert len(listed.json()) == 1


@pytest.mark.asyncio
async def test_duplicate_create_conflicts_when_details_change(client, student_auth):
    headers, _email = student_auth
    payload = _ticket()
    first = await client.post("/api/v1/support/tickets", json=payload, headers=headers)
    assert first.status_code == 200
    changed = {**payload, "title": "A different title for the same key"}
    second = await client.post("/api/v1/support/tickets", json=changed, headers=headers)
    assert second.status_code == 409
    listed = await client.get("/api/v1/support/tickets", headers=headers)
    assert len(listed.json()) == 1


@pytest.mark.asyncio
async def test_validation_rejects_length_category_and_sensitive_paths(client, student_auth):
    headers, _email = student_auth
    short = await client.post("/api/v1/support/tickets", json=_ticket(title="No"), headers=headers)
    assert short.status_code == 422
    blank = await client.post(
        "/api/v1/support/tickets",
        json=_ticket(description="   short   "),
        headers=headers,
    )
    assert blank.status_code == 422
    category = await client.post(
        "/api/v1/support/tickets",
        json=_ticket(category="complaint"),
        headers=headers,
    )
    assert category.status_code == 422
    for page_path in (
        "/practice/sql?token=abc",
        "/practice/sql#access_token",
        "https://example.com/secret",
        "/practice/sql/bearer-token",
    ):
        rejected = await client.post(
            "/api/v1/support/tickets",
            json=_ticket(page_path=page_path),
            headers=headers,
        )
        assert rejected.status_code == 422, page_path
    listed = await client.get("/api/v1/support/tickets", headers=headers)
    assert listed.json() == []


@pytest.mark.asyncio
async def test_student_cannot_use_the_admin_queue(client, student_auth):
    headers, _email = student_auth
    listing = await client.get("/api/v1/admin/support/tickets", headers=headers)
    assert listing.status_code == 403
    created = await client.post("/api/v1/support/tickets", json=_ticket(), headers=headers)
    ticket_id = created.json()["id"]
    reply = await client.post(
        f"/api/v1/admin/support/tickets/{ticket_id}/replies",
        json={"body": "Students cannot use the admin reply route.", "client_request_id": uuid.uuid4().hex},
        headers=headers,
    )
    status = await client.patch(
        f"/api/v1/admin/support/tickets/{ticket_id}",
        json={"status": "closed", "client_request_id": uuid.uuid4().hex},
        headers=headers,
    )
    assert reply.status_code == 403
    assert status.status_code == 403


@pytest.mark.asyncio
async def test_trainer_can_view_tickets_and_change_status(client):
    student, _email, _password = await _register(client)
    trainer, trainer_email, trainer_password = await _register(client, "trainer")
    async with AsyncSessionLocal() as session:
        await session.execute(update(User).where(User.email == trainer_email).values(role=UserRole.TRAINER))
        await session.commit()
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": trainer_email, "password": trainer_password},
    )
    assert login.status_code == 200, login.text
    trainer = {"Authorization": f"Bearer {login.json()['access_token']}"}

    created = await client.post("/api/v1/support/tickets", json=_ticket(category="improvement"), headers=student)
    ticket_id = created.json()["id"]
    queue = await client.get("/api/v1/admin/support/tickets?category=improvement", headers=trainer)
    assert queue.status_code == 200
    assert any(item["id"] == ticket_id for item in queue.json())
    changed = await client.patch(
        f"/api/v1/admin/support/tickets/{ticket_id}",
        json={"status": "planned", "client_request_id": "trainerstatus01"},
        headers=trainer,
    )
    assert changed.status_code == 200, changed.text
    assert changed.json()["status"] == "planned"
    again = await client.patch(
        f"/api/v1/admin/support/tickets/{ticket_id}",
        json={"status": "planned", "client_request_id": "trainerstatus01"},
        headers=trainer,
    )
    assert again.status_code == 200
    status_events = [item for item in again.json()["timeline"] if item["kind"] == "status"]
    assert len(status_events) == 1
    assert status_events[0]["author_name"] == "Trainer Person"
    assert status_events[0]["from_status"] == "new"
    assert status_events[0]["to_status"] == "planned"


@pytest.mark.asyncio
async def test_admin_reply_status_and_student_follow_up(client, student_auth, admin_auth):
    headers, _email = student_auth
    created = await client.post("/api/v1/support/tickets", json=_ticket(category="feature_request"), headers=headers)
    assert created.status_code == 200, created.text
    ticket_id = created.json()["id"]
    me = await client.get("/api/v1/auth/me", headers=admin_auth)
    admin_name = me.json()["full_name"] or me.json()["username"]

    reply = await client.post(
        f"/api/v1/admin/support/tickets/{ticket_id}/replies",
        json={"body": "Thanks. We will look at this page.", "client_request_id": "adminreply0001"},
        headers=admin_auth,
    )
    assert reply.status_code == 200, reply.text
    repeated = await client.post(
        f"/api/v1/admin/support/tickets/{ticket_id}/replies",
        json={"body": "Thanks. We will look at this page.", "client_request_id": "adminreply0001"},
        headers=admin_auth,
    )
    assert repeated.status_code == 200
    conflict = await client.post(
        f"/api/v1/admin/support/tickets/{ticket_id}/replies",
        json={"body": "A different reply for the same key.", "client_request_id": "adminreply0001"},
        headers=admin_auth,
    )
    assert conflict.status_code == 409

    status = await client.patch(
        f"/api/v1/admin/support/tickets/{ticket_id}",
        json={"status": "in_review", "client_request_id": "adminstatus0001"},
        headers=admin_auth,
    )
    assert status.status_code == 200
    event = next(item for item in status.json()["timeline"] if item["kind"] == "status")
    assert event["author_name"] == admin_name
    assert event["author_role"] == "admin"
    assert event["created_at"]

    student_view = await client.get(f"/api/v1/support/tickets/{ticket_id}", headers=headers)
    assert student_view.json()["status"] == "in_review"
    assert any(item["body"] == "Thanks. We will look at this page." for item in student_view.json()["timeline"])

    follow = await client.post(
        f"/api/v1/support/tickets/{ticket_id}/replies",
        json={"body": "It still happens after a refresh.", "client_request_id": "studentfollow01"},
        headers=headers,
    )
    assert follow.status_code == 200, follow.text
    follow_again = await client.post(
        f"/api/v1/support/tickets/{ticket_id}/replies",
        json={"body": "It still happens after a refresh.", "client_request_id": "studentfollow01"},
        headers=headers,
    )
    assert follow_again.status_code == 200
    replies = [item for item in follow_again.json()["timeline"] if item["kind"] == "reply"]
    assert len(replies) == 2
    assert replies[-1]["author_role"] == "student"

    admin_view = await client.get(f"/api/v1/admin/support/tickets/{ticket_id}", headers=admin_auth)
    assert admin_view.status_code == 200
    assert admin_view.json()["student_email"]
    assert admin_view.json()["page_path"] == "/practice/sql"
    assert any(item["body"] == "It still happens after a refresh." for item in admin_view.json()["timeline"])


@pytest.mark.asyncio
async def test_admin_filters_by_category_status_and_date(client, student_auth, admin_auth):
    headers, _email = student_auth
    bug = await client.post("/api/v1/support/tickets", json=_ticket(category="bug"), headers=headers)
    general = await client.post(
        "/api/v1/support/tickets",
        json=_ticket(category="general", title="General note about the jobs page"),
        headers=headers,
    )
    assert bug.status_code == 200 and general.status_code == 200
    bug_id = bug.json()["id"]
    await client.patch(
        f"/api/v1/admin/support/tickets/{bug_id}",
        json={"status": "resolved", "client_request_id": "filterstatus01"},
        headers=admin_auth,
    )
    today = datetime.now(timezone.utc).date().isoformat()
    yesterday = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
    by_category = await client.get("/api/v1/admin/support/tickets?category=bug", headers=admin_auth)
    by_status = await client.get("/api/v1/admin/support/tickets?status=resolved", headers=admin_auth)
    by_date = await client.get(
        f"/api/v1/admin/support/tickets?date_from={today}&date_to={today}",
        headers=admin_auth,
    )
    outside = await client.get(
        f"/api/v1/admin/support/tickets?date_from={yesterday}&date_to={yesterday}",
        headers=admin_auth,
    )
    assert any(item["id"] == bug_id for item in by_category.json())
    assert all(item["category"] == "bug" for item in by_category.json())
    assert any(item["id"] == bug_id for item in by_status.json())
    assert all(item["status"] == "resolved" for item in by_status.json())
    assert any(item["id"] == bug_id for item in by_date.json())
    assert all(item["id"] != bug_id for item in outside.json())


@pytest.mark.asyncio
async def test_hourly_ticket_limit(client, student_auth):
    headers, _email = student_auth
    for index in range(HOURLY_TICKET_LIMIT):
        created = await client.post(
            "/api/v1/support/tickets",
            json=_ticket(title=f"Limit ticket number {index} is long enough"),
            headers=headers,
        )
        assert created.status_code == 200, created.text
    blocked = await client.post(
        "/api/v1/support/tickets",
        json=_ticket(title="One more ticket should be rejected now"),
        headers=headers,
    )
    assert blocked.status_code == 429
