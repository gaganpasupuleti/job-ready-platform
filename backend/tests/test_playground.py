"""Phase 2: playground run is distinct from assessed coding and never fakes success."""

from __future__ import annotations


import pytest


@pytest.mark.asyncio
async def test_playground_run_unavailable_when_judge0_disabled(client, student_auth, monkeypatch):
    from app.core import config

    monkeypatch.setattr(config.settings, "judge0_enabled", False)
    headers = student_auth[0]
    resp = await client.post(
        "/api/v1/coding/playground/run",
        headers=headers,
        json={
            "source_code": "print('hello')",
            "language_id": 71,
            "stdin": "",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["available"] is False
    assert body["status"] == "service_unavailable"
    assert body["stdout"] == ""
    assert "unavailable" in (body.get("message") or "").lower()


@pytest.mark.asyncio
async def test_playground_run_requires_auth(client):
    resp = await client.post(
        "/api/v1/coding/playground/run",
        json={"source_code": "print(1)", "language_id": 71},
    )
    assert resp.status_code in (401, 403)
