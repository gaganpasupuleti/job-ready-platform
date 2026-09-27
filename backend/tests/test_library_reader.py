"""Library PDF access, last page, and private object keys."""

import uuid
from datetime import datetime, timezone

import pytest

from app.core.config import settings
from app.library.fixtures import LOCAL_FIXTURE_KEY, fixture_pdf_bytes
from app.library.r2 import R2Config, presign_get

FIXTURE_URL = "https://example.com/jobready-local-library-fixture"


def _pdf(**overrides):
    payload = {
        "title": "Local PDF fixture",
        "author": "Local test author",
        "description": "Clearly identified local test fixture. Not a production catalog.",
        "category": "Local fixtures",
        "status": "draft",
    }
    payload.update(overrides)
    return payload


async def _create(client, headers, **overrides):
    status = overrides.pop("status", "draft")
    response = await client.post("/api/v1/admin/library/books", headers=headers, json=_pdf(**overrides))
    assert response.status_code == 201, response.text
    created = response.json()
    uploaded = await client.post(
        f"/api/v1/admin/library/books/{created['id']}/file",
        headers=headers,
        files={"file": ("local-fixture.pdf", fixture_pdf_bytes(), "application/pdf")},
    )
    assert uploaded.status_code == 200, uploaded.text
    if status != "draft":
        published = await client.patch(
            f"/api/v1/admin/library/books/{created['id']}",
            headers=headers,
            json={"status": status},
        )
        assert published.status_code == 200, published.text
        return published.json()
    return uploaded.json()


def test_presign_builds_an_https_url_without_a_network_call():
    url = presign_get(
        R2Config("abc123", "jobready-library", "access-key", "secret-key"),
        LOCAL_FIXTURE_KEY,
        datetime(2026, 9, 27, tzinfo=timezone.utc),
        expires=300,
    )
    assert url.startswith("https://abc123.r2.cloudflarestorage.com/")
    assert "X-Amz-Signature=" in url
    assert "X-Amz-Expires=300" in url


def test_placeholder_storage_settings_are_not_configured():
    assert settings.library_storage_configured is False


@pytest.mark.asyncio
async def test_students_cannot_read_a_draft_or_unconfigured_pdf(client, admin_auth, student_auth):
    headers, _email = student_auth
    created = await _create(client, admin_auth)
    book_id = created["id"]
    assert created["storage_key"].startswith(f"library/books/{book_id}/")
    assert created["storage_key"].endswith(".pdf")
    assert "local-fixture.pdf" not in created["storage_key"]
    assert "storage_key" not in (await client.get("/api/v1/library/books", headers=headers)).json()["items"].__repr__()

    for path in (f"/api/v1/library/books/{book_id}/read-link", f"/api/v1/library/books/{book_id}/file"):
        denied = await client.get(path, headers=headers)
        assert denied.status_code == 404
        assert LOCAL_FIXTURE_KEY not in denied.text
        assert "X-Amz-Signature" not in denied.text

    rejected = await client.post(
        "/api/v1/admin/library/books",
        headers=admin_auth,
        json=_pdf(storage_key="local-fixtures/missing.pdf", title="Missing PDF fixture"),
    )
    assert rejected.status_code == 422
    assert "object key" in rejected.text
    assert "id" not in rejected.json()

    anonymous = await client.get(f"/api/v1/library/books/{book_id}/read-link")
    assert anonymous.status_code == 401


@pytest.mark.asyncio
async def test_last_page_is_personal_and_opening_does_not_save_it(client, admin_auth, student_auth):
    owner, _email = student_auth
    suffix = uuid.uuid4().hex[:8]
    other = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"library_pdf_{suffix}@example.com",
            "username": f"library_pdf_{suffix}",
            "full_name": "Other Student",
            "password": "Student123!",
        },
    )
    assert other.status_code == 200, other.text
    other_headers = {"Authorization": f"Bearer {other.json()['access_token']}"}
    created = await _create(client, admin_auth, status="published")
    book_id = created["id"]

    opened = await client.get(f"/api/v1/library/books/{book_id}", headers=owner)
    assert opened.status_code == 200
    assert opened.json()["last_page"] is None
    assert opened.json()["reading_status"] is None
    assert opened.json()["has_file"] is True
    assert "storage_key" not in opened.json()

    link = await client.get(f"/api/v1/library/books/{book_id}/read-link", headers=owner)
    assert link.status_code == 200
    assert link.json()["url"] == f"/api/v1/library/books/{book_id}/file"
    assert LOCAL_FIXTURE_KEY not in link.text
    file_response = await client.get(f"/api/v1/library/books/{book_id}/file", headers=owner)
    assert file_response.status_code == 200
    assert file_response.headers["content-type"].startswith("application/pdf")
    assert file_response.content.startswith(b"%PDF")
    assert LOCAL_FIXTURE_KEY.encode() not in file_response.content

    after_open = await client.get(f"/api/v1/library/books/{book_id}", headers=owner)
    assert after_open.json()["last_page"] is None
    assert after_open.json()["reading_status"] is None

    saved = await client.put(
        f"/api/v1/library/books/{book_id}/progress",
        headers=owner,
        json={"last_page": 2},
    )
    assert saved.status_code == 200
    assert saved.json()["last_page"] == 2
    assert saved.json()["reading_status"] is None

    status = await client.put(
        f"/api/v1/library/books/{book_id}/reading-status",
        headers=owner,
        json={"status": "reading"},
    )
    assert status.json()["reading_status"] == "reading"
    assert status.json()["last_page"] == 2

    other_view = await client.get(f"/api/v1/library/books/{book_id}", headers=other_headers)
    assert other_view.json()["last_page"] is None
    assert other_view.json()["reading_status"] is None

    archived = await client.patch(
        f"/api/v1/admin/library/books/{book_id}",
        headers=admin_auth,
        json={"status": "archived"},
    )
    assert archived.status_code == 200
    hidden = await client.get(f"/api/v1/library/books/{book_id}", headers=owner)
    assert hidden.json()["available"] is False
    assert hidden.json()["external_url"] is None
    assert hidden.json()["last_page"] == 2
    assert "storage_key" not in hidden.json()
    blocked = await client.get(f"/api/v1/library/books/{book_id}/read-link", headers=owner)
    assert blocked.status_code == 404
    assert LOCAL_FIXTURE_KEY not in blocked.text
    assert FIXTURE_URL not in blocked.text
    other_blocked = await client.get(f"/api/v1/library/books/{book_id}/file", headers=other_headers)
    assert other_blocked.status_code == 404
    assert LOCAL_FIXTURE_KEY not in other_blocked.text
