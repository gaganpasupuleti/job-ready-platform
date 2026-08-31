"""Build 8 interview session engine tests."""

from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.seed.build8_seed import seed_build8_content


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _headers(auth):
    return auth[0] if isinstance(auth, tuple) else auth


@pytest.fixture(autouse=True)
async def _seed_build8():
    await seed_build8_content()


@pytest.mark.asyncio
async def test_hub_and_pack_detail(client, student_auth):
    headers = _headers(student_auth)
    hub = await client.get("/api/v1/interviews/hub", headers=headers)
    assert hub.status_code == 200, hub.text
    body = hub.json()
    assert "packs" in body
    assert "progress" in body
    packs = await client.get("/api/v1/interview/packs", headers=headers)
    assert packs.status_code == 200
    assert len(packs.json()) >= 1
    slug = packs.json()[0]["slug"]
    detail = await client.get(f"/api/v1/interviews/packs/{slug}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["slug"] == slug


@pytest.mark.asyncio
async def test_study_session_flow(client, student_auth):
    headers = _headers(student_auth)
    created = await client.post(
        "/api/v1/interviews/sessions",
        headers=headers,
        json={
            "mode": "study",
            "source_type": "pack",
            "pack_slug": "sql-interview-essentials",
            "deterministic": True,
        },
    )
    assert created.status_code == 200, created.text
    session_id = created.json()["session"]["id"]
    q1 = created.json()["current"]
    assert q1 is not None
    assert q1["expected_answer"]  # study reveals
    assert q1["key_points"]

    notes = await client.post(
        f"/api/v1/interviews/sessions/{session_id}/questions/1/notes",
        headers=headers,
        json={"answer_text": "Window functions keep rows.", "private_notes": "review RANK"},
    )
    assert notes.status_code == 200
    assert notes.json()["answer_text"]

    kp = [p["id"] for p in q1["key_points"][:2]]
    review = await client.post(
        f"/api/v1/interviews/sessions/{session_id}/questions/1/review",
        headers=headers,
        json={
            "key_point_ids": kp,
            "confidence": "medium",
            "self_rating": "good",
            "time_spent_seconds": 40,
        },
    )
    assert review.status_code == 200, review.text
    assert review.json()["self_rating"] == "good"
    assert review.json()["key_point_coverage"] is not None

    complete = await client.post(f"/api/v1/interviews/sessions/{session_id}/complete", headers=headers)
    assert complete.status_code == 200
    assert complete.json()["label"] == "Self-Review Summary"
    results = await client.get(f"/api/v1/interviews/sessions/{session_id}/results", headers=headers)
    assert results.status_code == 200
    assert results.json()["reviewed_count"] >= 1


@pytest.mark.asyncio
async def test_mock_hides_answer_until_reveal(client, student_auth):
    headers = _headers(student_auth)
    created = await client.post(
        "/api/v1/interviews/sessions",
        headers=headers,
        json={
            "mode": "mock",
            "source_type": "pack",
            "pack_slug": "behavioral-essentials",
            "deterministic": True,
        },
    )
    assert created.status_code == 200, created.text
    session_id = created.json()["session"]["id"]
    current = created.json()["current"]
    assert current["expected_answer"] is None
    assert current["key_points"] == []
    assert current["answer_revealed"] is False

    leaked = await client.get(f"/api/v1/interviews/sessions/{session_id}/questions/1", headers=headers)
    assert leaked.status_code == 200
    assert leaked.json()["expected_answer"] is None

    revealed = await client.post(
        f"/api/v1/interviews/sessions/{session_id}/questions/1/reveal",
        headers=headers,
    )
    assert revealed.status_code == 200
    assert revealed.json()["expected_answer"]
    assert revealed.json()["key_points"]


@pytest.mark.asyncio
async def test_session_ownership(client, student_auth):
    headers = _headers(student_auth)
    created = await client.post(
        "/api/v1/interviews/sessions",
        headers=headers,
        json={
            "mode": "rapid_review",
            "source_type": "pack",
            "pack_slug": "hr-final-round",
        },
    )
    session_id = created.json()["session"]["id"]

    suffix = uuid.uuid4().hex[:8]
    other = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"other_{suffix}@example.com",
            "username": f"other_{suffix}",
            "full_name": "Other",
            "password": "Student123!",
        },
    )
    assert other.status_code == 200
    other_headers = {"Authorization": f"Bearer {other.json()['access_token']}"}
    denied = await client.get(f"/api/v1/interviews/sessions/{session_id}", headers=other_headers)
    assert denied.status_code == 404


@pytest.mark.asyncio
async def test_custom_filter_and_no_duplicates(client, student_auth):
    headers = _headers(student_auth)
    created = await client.post(
        "/api/v1/interviews/sessions",
        headers=headers,
        json={
            "mode": "study",
            "source_type": "custom_filter",
            "skill": "SQL",
            "question_count": 20,
            "deterministic": True,
        },
    )
    assert created.status_code == 200, created.text
    nav = created.json()["navigator"]
    assert len(nav) >= 1
    assert len(nav) <= 20


@pytest.mark.asyncio
async def test_admin_pack_validation(client, admin_auth, student_auth):
    student_headers = _headers(student_auth)
    blocked = await client.get("/api/v1/admin/interviews/packs", headers=student_headers)
    assert blocked.status_code == 403

    admin_headers = admin_auth
    listed = await client.get("/api/v1/admin/interviews/packs", headers=admin_headers)
    assert listed.status_code == 200
    qs = await client.get("/api/v1/interview/questions?limit=1", headers=student_headers)
    assert qs.status_code == 200
    assert qs.json()["items"]
    qid = qs.json()["items"][0]["id"]
    bad = await client.post(
        "/api/v1/admin/interviews/packs",
        headers=admin_headers,
        json={
            "title": "Too Small Pack",
            "description": "Should fail activation",
            "is_active": True,
            "question_ids": [qid],
        },
    )
    assert bad.status_code == 400


@pytest.mark.asyncio
async def test_company_prep(client, student_auth):
    headers = _headers(student_auth)
    listed = await client.get("/api/v1/interviews/company-prep", headers=headers)
    assert listed.status_code == 200
    assert isinstance(listed.json(), list)
    if listed.json():
        slug = listed.json()[0]["slug"]
        detail = await client.get(f"/api/v1/interviews/company-prep/{slug}", headers=headers)
        assert detail.status_code == 200
        assert "not affiliated" in detail.json()["disclaimer"].lower()


@pytest.mark.asyncio
async def test_needs_review_and_history(client, student_auth):
    headers = _headers(student_auth)
    created = await client.post(
        "/api/v1/interviews/sessions",
        headers=headers,
        json={"mode": "study", "source_type": "pack", "pack_slug": "soc-analyst-essentials"},
    )
    session_id = created.json()["session"]["id"]
    current = created.json()["current"]
    await client.post(
        f"/api/v1/interviews/sessions/{session_id}/questions/1/review",
        headers=headers,
        json={
            "key_point_ids": [],
            "confidence": "low",
            "self_rating": "needs_review",
            "needs_review": True,
        },
    )
    queue = await client.get("/api/v1/interviews/review", headers=headers)
    assert queue.status_code == 200
    assert any(i["question_id"] == current["question_id"] for i in queue.json())
    hist = await client.get("/api/v1/interviews/history", headers=headers)
    assert hist.status_code == 200
    assert len(hist.json()) >= 1
    progress = await client.get("/api/v1/interviews/progress", headers=headers)
    assert progress.status_code == 200
    assert progress.json()["questions_reviewed"] >= 1
