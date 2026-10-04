"""Library metadata visibility, https links, bookmarks, and reading status."""

import uuid

import pytest

FIXTURE_URL = "https://example.com/jobready-local-library-fixture"


def _book(title="Local fixture", status="draft", url=FIXTURE_URL, category="Fixtures"):
    return {
        "title": title,
        "author": "Local test author",
        "description": "Clearly identified local test fixture. Not a production catalog.",
        "category": category,
        "external_url": url,
        "status": status,
    }


async def _create(client, headers, **overrides):
    payload = _book(**overrides)
    response = await client.post("/api/v1/admin/library/books", headers=headers, json=payload)
    assert response.status_code == 201, response.text
    return response.json()


@pytest.mark.asyncio
async def test_students_cannot_administer_books_or_see_draft_urls(client, admin_auth, student_auth):
    headers, _email = student_auth
    denied = await client.post("/api/v1/admin/library/books", headers=headers, json=_book())
    assert denied.status_code == 403

    created = await _create(client, admin_auth)
    listed = await client.get("/api/v1/library/books", headers=headers)
    assert listed.status_code == 200
    assert all(item["id"] != created["id"] for item in listed.json()["items"])
    assert FIXTURE_URL not in listed.text

    direct = await client.get(f"/api/v1/library/books/{created['id']}", headers=headers)
    assert direct.status_code == 404
    assert FIXTURE_URL not in direct.text

    http_url = await client.post(
        "/api/v1/admin/library/books",
        headers=admin_auth,
        json=_book(url="http://example.com/jobready-local-library-fixture"),
    )
    assert http_url.status_code == 422
    script_url = await client.post(
        "/api/v1/admin/library/books",
        headers=admin_auth,
        json=_book(url="javascript:alert(1)"),
    )
    assert script_url.status_code == 422


@pytest.mark.asyncio
async def test_published_books_are_personal_and_opening_does_not_record_reading(
    client, admin_auth, student_auth
):
    owner, _email = student_auth
    suffix = uuid.uuid4().hex[:8]
    other = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"library_other_{suffix}@example.com",
            "username": f"library_other_{suffix}",
            "full_name": "Other Student",
            "password": "Student123!",
        },
    )
    assert other.status_code == 200, other.text
    other_headers = {"Authorization": f"Bearer {other.json()['access_token']}"}

    created = await _create(client, admin_auth, status="published", category="Local fixtures")
    book_id = created["id"]

    before = await client.get(f"/api/v1/library/books/{book_id}", headers=owner)
    assert before.status_code == 200
    assert before.json()["external_url"] == FIXTURE_URL
    assert before.json()["reading_status"] is None
    assert before.json()["bookmarked"] is False
    again = await client.get(f"/api/v1/library/books/{book_id}", headers=owner)
    assert again.json()["reading_status"] is None

    first = await client.post(f"/api/v1/library/books/{book_id}/bookmark", headers=owner)
    second = await client.post(f"/api/v1/library/books/{book_id}/bookmark", headers=owner)
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["bookmarked"] is True

    status = await client.put(
        f"/api/v1/library/books/{book_id}/reading-status",
        headers=owner,
        json={"status": "reading"},
    )
    assert status.status_code == 200
    assert status.json()["reading_status"] == "reading"

    stranger = await client.get(f"/api/v1/library/books/{book_id}", headers=other_headers)
    assert stranger.json()["bookmarked"] is False
    assert stranger.json()["reading_status"] is None

    found = await client.get("/api/v1/library/books", headers=owner, params={"q": "Local fixture", "category": "Local fixtures"})
    assert any(item["id"] == book_id for item in found.json()["items"])
    missed = await client.get("/api/v1/library/books", headers=owner, params={"category": "Missing"})
    assert missed.json()["items"] == []

    archived = await client.patch(
        f"/api/v1/admin/library/books/{book_id}",
        headers=admin_auth,
        json={"status": "archived"},
    )
    assert archived.status_code == 200
    hidden = await client.get("/api/v1/library/books", headers=owner)
    assert all(item["id"] != book_id for item in hidden.json()["items"])
    assert FIXTURE_URL not in hidden.text

    kept = await client.get(f"/api/v1/library/books/{book_id}", headers=owner)
    assert kept.status_code == 200
    body = kept.json()
    assert body["available"] is False
    assert body["external_url"] is None
    assert body["bookmarked"] is True
    assert body["reading_status"] == "reading"
    assert FIXTURE_URL not in kept.text

    stranger_archived = await client.get(f"/api/v1/library/books/{book_id}", headers=other_headers)
    assert stranger_archived.status_code == 404
    assert FIXTURE_URL not in stranger_archived.text

    still_saved = await client.get("/api/v1/library/saved", headers=owner)
    assert any(item["id"] == book_id and item["external_url"] is None for item in still_saved.json())
    other_saved = await client.get("/api/v1/library/saved", headers=other_headers)
    assert other_saved.json() == []
