"""Build 10 readiness, job match, mistakes tests."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.readiness_enums import EvidenceStrength
from app.readiness.formulas import (
    effective_score,
    evidence_strength_from_signals,
    weighted_average,
)
from app.seed.build10_seed import seed_build10


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _headers(auth):
    return auth[0] if isinstance(auth, tuple) else auth


@pytest.fixture(autouse=True)
async def _seed_build10():
    await seed_build10()


def test_effective_score_low_evidence_penalty():
    assert effective_score(90, EvidenceStrength.LOW) == 67.5
    assert effective_score(90, EvidenceStrength.HIGH) == 90.0


def test_evidence_strength_thresholds():
    assert evidence_strength_from_signals(1, 0) == EvidenceStrength.LOW
    assert evidence_strength_from_signals(3, 1) == EvidenceStrength.MEDIUM
    assert evidence_strength_from_signals(8, 2) == EvidenceStrength.HIGH


def test_weighted_average():
    assert weighted_average([(100, 1), (0, 1)]) == 50.0
    assert weighted_average([]) == 0.0


@pytest.mark.asyncio
async def test_readiness_overview_no_target_role(client, student_auth):
    headers = _headers(student_auth)
    resp = await client.get("/api/v1/readiness", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "has_minimum_evidence" in body
    assert body.get("message") is not None or body.get("target_role") is not None


@pytest.mark.asyncio
async def test_mistakes_list_and_summary(client, student_auth):
    headers = _headers(student_auth)
    summary = await client.get("/api/v1/mistakes/summary", headers=headers)
    assert summary.status_code == 200
    assert "open_count" in summary.json()
    items = await client.get("/api/v1/mistakes", headers=headers)
    assert items.status_code == 200
    assert isinstance(items.json(), list)


@pytest.mark.asyncio
async def test_job_match_endpoint(client, student_auth):
    headers = _headers(student_auth)
    jobs = await client.get("/api/v1/jobs", headers=headers, params={"limit": 1})
    job_id = jobs.json()["items"][0]["id"]
    match = await client.get(f"/api/v1/jobs/{job_id}/match", headers=headers)
    assert match.status_code == 200
    body = match.json()
    assert "has_sufficient_mapping" in body


@pytest.mark.asyncio
async def test_admin_readiness_requires_admin(client, student_auth, admin_auth):
    student = await client.get("/api/v1/admin/readiness/roles", headers=_headers(student_auth))
    assert student.status_code == 403
    admin = await client.get("/api/v1/admin/readiness/roles", headers=_headers(admin_auth))
    assert admin.status_code == 200


@pytest.mark.asyncio
async def test_mistake_isolation(client, student_auth, admin_auth):
    """User cannot access another user's mistakes by ID guessing."""
    headers_a = _headers(student_auth)
    headers_b = _headers(admin_auth)
    await client.get("/api/v1/mistakes", headers=headers_a)
    items_b = await client.get("/api/v1/mistakes", headers=headers_b)
    ids_a = {i["id"] for i in (await client.get("/api/v1/mistakes", headers=headers_a)).json()}
    for item in items_b.json():
        if item["id"] not in ids_a:
            patch = await client.patch(f"/api/v1/mistakes/{item['id']}", headers=headers_a)
            assert patch.status_code == 404
            break
