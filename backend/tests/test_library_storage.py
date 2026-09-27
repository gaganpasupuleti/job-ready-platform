"""Admin PDF upload and private storage. R2 is not contacted."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.library.fixtures import fixture_pdf_bytes
from app.library.storage import DevDiskStorage, StorageError

PDF = fixture_pdf_bytes()


def _meta(**overrides):
    payload = {
        "title": "Upload fixture",
        "author": "Local test author",
        "description": "Clearly identified local test fixture. Not a production catalog.",
        "category": "Local fixtures",
        "status": "draft",
    }
    payload.update(overrides)
    return payload


async def _draft(client, headers, **overrides):
    response = await client.post("/api/v1/admin/library/books", headers=headers, json=_meta(**overrides))
    assert response.status_code == 201, response.text
    return response.json()


def _file(name="notes.pdf", body=PDF, content_type="application/pdf"):
    return {"file": (name, body, content_type)}


@pytest.mark.asyncio
async def test_students_cannot_upload_and_client_keys_are_rejected(client, admin_auth, student_auth):
    headers, _email = student_auth
    created = await _draft(client, admin_auth)
    denied = await client.post(
        f"/api/v1/admin/library/books/{created['id']}/file",
        headers=headers,
        files=_file(),
    )
    assert denied.status_code == 403
    rejected = await client.post(
        "/api/v1/admin/library/books",
        headers=admin_auth,
        json=_meta(storage_key="library/books/chosen-by-client.pdf"),
    )
    assert rejected.status_code == 422
    assert "object key" in rejected.text


@pytest.mark.asyncio
async def test_pdf_upload_validates_type_size_and_replaces_safely(client, admin_auth, student_auth, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "library_dev_object_dir", str(tmp_path))
    monkeypatch.setattr(settings, "library_pdf_max_bytes", 20 * 1024 * 1024)
    owner, _email = student_auth
    created = await _draft(client, admin_auth, external_url="https://example.com/jobready-local-library-fixture")
    book_id = created["id"]

    bad_name = await client.post(
        f"/api/v1/admin/library/books/{book_id}/file",
        headers=admin_auth,
        files=_file(name="notes.txt"),
    )
    assert bad_name.status_code == 422
    assert "pdf" in bad_name.text.lower()

    bad_type = await client.post(
        f"/api/v1/admin/library/books/{book_id}/file",
        headers=admin_auth,
        files=_file(content_type="text/plain"),
    )
    assert bad_type.status_code == 422
    assert "Only PDF files" in bad_type.text

    empty = await client.post(
        f"/api/v1/admin/library/books/{book_id}/file",
        headers=admin_auth,
        files=_file(body=b""),
    )
    assert empty.status_code == 422
    assert "empty" in empty.text

    monkeypatch.setattr(settings, "library_pdf_max_bytes", 8)
    oversized = await client.post(
        f"/api/v1/admin/library/books/{book_id}/file",
        headers=admin_auth,
        files=_file(),
    )
    assert oversized.status_code == 422
    assert "too large" in oversized.text
    monkeypatch.setattr(settings, "library_pdf_max_bytes", 20 * 1024 * 1024)

    uploaded = await client.post(
        f"/api/v1/admin/library/books/{book_id}/file",
        headers=admin_auth,
        files=_file(name="original-name.pdf"),
    )
    assert uploaded.status_code == 200, uploaded.text
    first = uploaded.json()
    assert first["external_url"] is None
    assert first["storage_key"].startswith(f"library/books/{book_id}/")
    assert "original-name" not in first["storage_key"]
    assert first["has_file"] is True

    replaced = await client.post(
        f"/api/v1/admin/library/books/{book_id}/file",
        headers=admin_auth,
        files=_file(name="other.pdf", body=PDF + b"\n"),
    )
    assert replaced.status_code == 200, replaced.text
    second = replaced.json()
    assert second["storage_key"] != first["storage_key"]
    assert not (tmp_path / first["storage_key"]).exists()
    assert (tmp_path / second["storage_key"]).is_file()

    published = await client.patch(
        f"/api/v1/admin/library/books/{book_id}",
        headers=admin_auth,
        json={"status": "published"},
    )
    assert published.status_code == 200
    link = await client.get(f"/api/v1/library/books/{book_id}/read-link", headers=owner)
    assert link.status_code == 200
    assert link.json()["expires_in"] == 300
    assert link.json()["url"] == f"/api/v1/library/books/{book_id}/file"
    assert second["storage_key"] not in link.text
    student = await client.get(f"/api/v1/library/books/{book_id}", headers=owner)
    assert "storage_key" not in student.json()
    assert student.json()["has_file"] is True
    assert student.json()["last_page"] is None

    blocked = await client.delete(f"/api/v1/admin/library/books/{book_id}/file", headers=admin_auth)
    assert blocked.status_code == 422

    switched = await client.patch(
        f"/api/v1/admin/library/books/{book_id}",
        headers=admin_auth,
        json={"external_url": "https://example.com/jobready-switched-link"},
    )
    assert switched.status_code == 200
    assert switched.json()["storage_key"] is None
    assert switched.json()["external_url"].startswith("https://")
    assert not (tmp_path / second["storage_key"]).exists()

    back = await client.post(
        f"/api/v1/admin/library/books/{book_id}/file",
        headers=admin_auth,
        files=_file(),
    )
    assert back.status_code == 200
    assert back.json()["external_url"] is None
    assert back.json()["has_file"] is True

    archived = await client.patch(
        f"/api/v1/admin/library/books/{book_id}",
        headers=admin_auth,
        json={"status": "archived"},
    )
    assert archived.status_code == 200
    hidden = await client.get(f"/api/v1/library/books/{book_id}/read-link", headers=owner)
    assert hidden.status_code == 404
    assert back.json()["storage_key"] not in hidden.text
    removed = await client.delete(f"/api/v1/admin/library/books/{book_id}/file", headers=admin_auth)
    assert removed.status_code == 200
    assert removed.json()["storage_key"] is None
    assert removed.json()["has_file"] is False


@pytest.mark.asyncio
async def test_storage_failures_keep_the_previous_pdf(client, admin_auth, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "library_dev_object_dir", str(tmp_path))
    created = await _draft(client, admin_auth)
    book_id = created["id"]
    uploaded = await client.post(
        f"/api/v1/admin/library/books/{book_id}/file",
        headers=admin_auth,
        files=_file(),
    )
    assert uploaded.status_code == 200, uploaded.text
    original = uploaded.json()["storage_key"]
    calls = {"n": 0}
    real_put = DevDiskStorage.put

    def flaky(self, key, body):
        calls["n"] += 1
        if calls["n"] > 0:
            raise StorageError("PDF storage could not be reached.", 503)
        return real_put(self, key, body)

    monkeypatch.setattr(DevDiskStorage, "put", flaky)
    failed = await client.post(
        f"/api/v1/admin/library/books/{book_id}/file",
        headers=admin_auth,
        files=_file(),
    )
    assert failed.status_code == 503
    assert failed.json()["detail"] == "PDF storage could not be reached."
    monkeypatch.setattr(DevDiskStorage, "put", real_put)
    current = await client.get(f"/api/v1/admin/library/books/{book_id}", headers=admin_auth)
    assert current.json()["storage_key"] == original
    assert (tmp_path / original).is_file()

    real_commit = AsyncSession.commit

    async def fail_commit(self):
        raise RuntimeError("commit failed")

    monkeypatch.setattr(AsyncSession, "commit", fail_commit)
    saved = await client.post(
        f"/api/v1/admin/library/books/{book_id}/file",
        headers=admin_auth,
        files=_file(),
    )
    assert saved.status_code == 503
    assert saved.json()["detail"] == "The PDF could not be saved."
    monkeypatch.setattr(AsyncSession, "commit", real_commit)
    after = await client.get(f"/api/v1/admin/library/books/{book_id}", headers=admin_auth)
    assert after.json()["storage_key"] == original
    leftovers = [path for path in tmp_path.rglob("*.pdf") if path.name != original.rsplit("/", 1)[-1]]
    assert leftovers == []


@pytest.mark.asyncio
async def test_missing_object_and_production_without_r2(client, admin_auth, student_auth, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "library_dev_object_dir", str(tmp_path))
    headers, _email = student_auth
    created = await _draft(client, admin_auth)
    uploaded = await client.post(
        f"/api/v1/admin/library/books/{created['id']}/file",
        headers=admin_auth,
        files=_file(),
    )
    book_id = created["id"]
    key = uploaded.json()["storage_key"]
    await client.patch(
        f"/api/v1/admin/library/books/{book_id}",
        headers=admin_auth,
        json={"status": "published"},
    )
    (tmp_path / key).unlink()
    missing = await client.get(f"/api/v1/library/books/{book_id}/read-link", headers=headers)
    assert missing.status_code == 404
    assert missing.json()["detail"] == "This PDF file is missing."
    assert key not in missing.text

    monkeypatch.setattr(settings, "app_env", "production")
    blocked = await client.get(f"/api/v1/library/books/{book_id}/read-link", headers=headers)
    assert blocked.status_code == 503
    assert blocked.json()["detail"] == "PDF storage is not configured."
    assert key not in blocked.text

    suffix = uuid.uuid4().hex[:8]
    other = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"library_store_{suffix}@example.com",
            "username": f"library_store_{suffix}",
            "full_name": "Other Student",
            "password": "Student123!",
        },
    )
    assert other.status_code == 200, other.text
    monkeypatch.setattr(settings, "app_env", "development")
    (tmp_path / key).write_bytes(PDF)
    owner_page = await client.put(
        f"/api/v1/library/books/{book_id}/progress",
        headers=headers,
        json={"last_page": 2},
    )
    assert owner_page.status_code == 200
    assert owner_page.json()["last_page"] == 2
    assert owner_page.json()["reading_status"] is None
    other_headers = {"Authorization": f"Bearer {other.json()['access_token']}"}
    other_view = await client.get(f"/api/v1/library/books/{book_id}", headers=other_headers)
    assert other_view.json()["last_page"] is None
    assert "storage_key" not in other_view.json()

    draft = await _draft(client, admin_auth, title="Draft upload fixture")
    await client.post(
        f"/api/v1/admin/library/books/{draft['id']}/file",
        headers=admin_auth,
        files=_file(),
    )
    draft_link = await client.get(f"/api/v1/library/books/{draft['id']}/read-link", headers=headers)
    assert draft_link.status_code == 404
    assert "X-Amz-Signature" not in draft_link.text
    archived = await client.patch(
        f"/api/v1/admin/library/books/{book_id}",
        headers=admin_auth,
        json={"status": "archived"},
    )
    assert archived.status_code == 200
