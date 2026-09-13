"""MCQ exam reliability: autosave finalize, expiry, leakage, multi-select."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.enums import SessionStatus
from app.models.practice import PracticeSession


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _start_exam(client, headers, *, question_count=3, duration_minutes=30):
    catalog = await client.get("/api/v1/practice/catalog", headers=headers)
    assert catalog.status_code == 200
    category = catalog.json()["domains"][0]["categories"][0]
    topic = category["topics"][0]
    session_resp = await client.post(
        "/api/v1/practice/sessions",
        headers=headers,
        json={
            "category_id": category["id"],
            "topic_id": topic["id"],
            "question_count": question_count,
            "mode": "exam",
            "duration_minutes": duration_minutes,
        },
    )
    assert session_resp.status_code == 200, session_resp.text
    return session_resp.json()


@pytest.mark.asyncio
async def test_exam_autosave_finalize_scores_on_complete(client, student_auth):
    headers, _ = student_auth
    session = await _start_exam(client, headers, question_count=2)
    session_id = session["id"]

    q1 = await client.get(f"/api/v1/practice/sessions/{session_id}/questions/1", headers=headers)
    assert q1.status_code == 200
    body = q1.json()
    assert all("is_correct" not in opt for opt in body["question"]["options"])
    option_ids = [opt["id"] for opt in body["question"]["options"]]

    autosave = await client.post(
        f"/api/v1/practice/sessions/{session_id}/questions/1/autosave",
        headers=headers,
        json={
            "selected_option_ids": [option_ids[0]],
            "marked_for_review": False,
            "time_spent_seconds": 4,
        },
    )
    assert autosave.status_code == 200

    nav = await client.get(f"/api/v1/practice/sessions/{session_id}/navigator", headers=headers)
    assert nav.json()["items"][0]["answered"] is True

    restored = await client.get(
        f"/api/v1/practice/sessions/{session_id}/questions/1", headers=headers
    )
    assert restored.json()["selected_option_ids"] == [option_ids[0]]
    assert restored.json()["answered"] is True

    # Exam answer endpoint must not leak feedback
    submit = await client.post(
        f"/api/v1/practice/sessions/{session_id}/questions/1/answer",
        headers=headers,
        json={
            "selected_option_ids": [option_ids[0]],
            "time_spent_seconds": 5,
        },
    )
    assert submit.status_code == 200
    assert submit.json()["feedback"] is None

    results_blocked = await client.get(
        f"/api/v1/practice/sessions/{session_id}/results", headers=headers
    )
    assert results_blocked.status_code == 400

    complete = await client.post(
        f"/api/v1/practice/sessions/{session_id}/complete", headers=headers
    )
    assert complete.status_code == 200, complete.text
    results = complete.json()
    assert results["session"]["status"] == "completed"
    assert results["session"]["unanswered_count"] <= 1
    assert len(results["questions"]) == 2
    assert results["questions"][0]["selected_option_ids"]

    # Idempotent finalization
    again = await client.post(
        f"/api/v1/practice/sessions/{session_id}/complete", headers=headers
    )
    assert again.status_code == 200
    assert again.json()["session"]["id"] == session_id
    assert again.json()["session"]["score"] == results["session"]["score"]


@pytest.mark.asyncio
async def test_exam_multi_select_autosave_restore(client, student_auth):
    headers, _ = student_auth
    session = await _start_exam(client, headers, question_count=1)
    session_id = session["id"]
    q = await client.get(f"/api/v1/practice/sessions/{session_id}/questions/1", headers=headers)
    options = q.json()["question"]["options"]
    if len(options) < 2:
        pytest.skip("Need at least two options for multi-select restore coverage")
    selected = [options[0]["id"], options[1]["id"]]
    save = await client.post(
        f"/api/v1/practice/sessions/{session_id}/questions/1/autosave",
        headers=headers,
        json={
            "selected_option_ids": selected,
            "marked_for_review": True,
            "time_spent_seconds": 3,
        },
    )
    assert save.status_code == 200
    restored = await client.get(
        f"/api/v1/practice/sessions/{session_id}/questions/1", headers=headers
    )
    assert set(restored.json()["selected_option_ids"]) == set(selected)
    assert restored.json()["marked_for_review"] is True


@pytest.mark.asyncio
async def test_exam_expiry_rejects_late_writes_and_preserves_deadline(client, student_auth):
    headers, _ = student_auth
    session = await _start_exam(client, headers, question_count=1, duration_minutes=30)
    session_id = session["id"]
    expires_at = session["expires_at"]
    assert expires_at

    # Resume/get must not rewrite expires_at
    again = await client.get(f"/api/v1/practice/sessions/{session_id}", headers=headers)
    assert again.status_code == 200
    assert again.json()["expires_at"] == expires_at

    q = await client.get(f"/api/v1/practice/sessions/{session_id}/questions/1", headers=headers)
    option_id = q.json()["question"]["options"][0]["id"]

    # Force expiry in DB (mutates expires_at for the test only)
    async with AsyncSessionLocal() as db:
        row = (
            await db.execute(select(PracticeSession).where(PracticeSession.id == UUID(session_id)))
        ).scalar_one()
        row.expires_at = datetime.now(UTC) - timedelta(seconds=5)
        await db.commit()

    late = await client.post(
        f"/api/v1/practice/sessions/{session_id}/questions/1/autosave",
        headers=headers,
        json={
            "selected_option_ids": [option_id],
            "marked_for_review": False,
            "time_spent_seconds": 1,
        },
    )
    assert late.status_code == 400
    detail_body = late.json()["detail"]
    assert "not active" in str(detail_body).lower()

    detail = await client.get(f"/api/v1/practice/sessions/{session_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["status"] == SessionStatus.COMPLETED.value
    # Late writes remain rejected after finalization
    late2 = await client.post(
        f"/api/v1/practice/sessions/{session_id}/questions/1/autosave",
        headers=headers,
        json={
            "selected_option_ids": [option_id],
            "marked_for_review": False,
            "time_spent_seconds": 1,
        },
    )
    assert late2.status_code == 400
