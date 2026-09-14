"""SQL playground and Python assignment lock checks."""

from __future__ import annotations

import uuid

import pytest

from app.services.runtime_lock import assignment_requires_python


def test_python_lock_uses_explicit_metadata():
    assert assignment_requires_python("local_python", None) is True
    assert assignment_requires_python("manual_review", "python") is True
    assert assignment_requires_python("manual_review", None) is False
    assert assignment_requires_python("sql_evidence", None) is False


@pytest.mark.asyncio
async def test_sql_playground_catalog_and_run_are_not_assessed(client, student_auth):
    catalog = await client.get("/api/v1/sql/playground", headers=student_auth[0])
    assert catalog.status_code == 200, catalog.text
    body = catalog.json()
    assert body["assessed"] is False
    assert body["language"] == "sql"
    assert any(row["id"] == "campus-bookstore" for row in body["datasets"])

    dataset = await client.get("/api/v1/sql/playground/datasets/campus-bookstore", headers=student_auth[0])
    assert dataset.status_code == 200, dataset.text
    detail = dataset.json()
    assert detail["assessed"] is False
    assert detail["tables"]
    assert detail["tables"][0]["columns"]
    assert detail["tables"][0]["sample_rows"]

    before = await client.get("/api/v1/sql/progress", headers=student_auth[0])
    assert before.status_code == 200
    before_solved = before.json().get("solved_count") or 0

    run = await client.post(
        "/api/v1/sql/playground/datasets/campus-bookstore/run",
        headers=student_auth[0],
        json={"query": "SELECT title FROM books WHERE in_stock = true ORDER BY title"},
    )
    assert run.status_code in {200, 503}, run.text
    if run.status_code == 200:
        payload = run.json()
        assert payload["assessed"] is False
        assert "note" in payload
        if payload["status"] == "ok":
            assert payload["row_count"] >= 1

    after = await client.get("/api/v1/sql/progress", headers=student_auth[0])
    assert after.status_code == 200
    after_solved = after.json().get("solved_count") or 0
    assert after_solved == before_solved


@pytest.mark.asyncio
async def test_python_assignment_submit_is_rejected_and_history_stays(client, student_auth, admin_auth):
    detail = await client.get("/api/v1/studio/assignments/py-assign-exceptions", headers=student_auth[0])
    assert detail.status_code == 200, detail.text
    assert detail.json()["unavailable"] is True
    prior = list(detail.json()["submissions"])

    blocked = await client.post(
        "/api/v1/studio/assignments/py-assign-exceptions/submit",
        headers=student_auth[0],
        json={"answer_text": "should not file", "evidence_url": "https://example.com/repo"},
    )
    assert blocked.status_code == 409, blocked.text

    catalog = await client.get("/api/v1/studio/catalog", headers=student_auth[0])
    assert catalog.status_code == 200
    keys = {row["key"] for row in catalog.json()["assignments"]}
    assert "py-assign-exceptions" not in keys
    assert "de-assign-local-validate" not in keys
    assert "da-assign-paid-totals" in keys

    after = await client.get("/api/v1/studio/assignments/py-assign-exceptions", headers=student_auth[0])
    assert after.json()["submissions"] == prior

    sql_submit = await client.post(
        "/api/v1/studio/assignments/da-assign-paid-totals/draft",
        headers=student_auth[0],
        json={"answer_text": f"draft-{uuid.uuid4().hex[:6]}", "evidence_url": "https://example.com/note"},
    )
    assert sql_submit.status_code == 200, sql_submit.text
