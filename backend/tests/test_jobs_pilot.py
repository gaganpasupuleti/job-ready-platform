"""Jobs-first preferences and one answer row per session question."""

import asyncio
import uuid

import pytest
from sqlalchemy import func, select

from app.db.session import AsyncSessionLocal
from app.models.practice import PracticeAnswer


@pytest.mark.asyncio
async def test_job_preferences_roundtrip(client, student_auth):
    headers, _ = student_auth
    current = await client.get("/api/v1/jobs/preferences", headers=headers)
    assert current.status_code == 200, current.text
    body = current.json()
    assert body["completed"] is False
    assert isinstance(body["roles"], list)
    assert body["roles"]

    saved = await client.put(
        "/api/v1/jobs/preferences",
        headers=headers,
        json={
            "target_role_slug": body["roles"][0]["slug"],
            "preferred_locations": ["Hyderabad"],
            "remote_preference": "remote",
        },
    )
    assert saved.status_code == 204, saved.text

    again = await client.get("/api/v1/jobs/preferences", headers=headers)
    assert again.status_code == 200
    stored = again.json()
    assert stored["completed"] is True
    assert stored["target_role_slug"] == body["roles"][0]["slug"]
    assert stored["preferred_locations"] == ["Hyderabad"]
    assert stored["remote_preference"] == "remote"


@pytest.mark.asyncio
async def test_saved_job_is_not_visible_to_another_account(client, student_auth):
    headers, _ = student_auth
    listing = await client.get("/api/v1/jobs?limit=1", headers=headers)
    assert listing.status_code == 200, listing.text
    job_id = listing.json()["items"][0]["id"]

    saved = await client.post(f"/api/v1/jobs/{job_id}/save", headers=headers)
    assert saved.status_code == 204, saved.text

    suffix = uuid.uuid4().hex[:8]
    other = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"jobs_iso_{suffix}@example.com",
            "username": f"jobsiso{suffix}",
            "full_name": "Jobs Isolate",
            "password": "Student123!",
        },
    )
    assert other.status_code == 200, other.text
    other_headers = {"Authorization": f"Bearer {other.json()['access_token']}"}
    other_saved = await client.get("/api/v1/jobs/saved", headers=other_headers)
    assert other_saved.status_code == 200
    assert all(item["job_id"] != job_id for item in other_saved.json())

    detail = await client.get(f"/api/v1/jobs/{job_id}", headers=other_headers)
    assert detail.status_code == 200
    assert detail.json()["is_saved"] is False
    assert detail.json()["application_status"] is None


@pytest.mark.asyncio
async def test_opening_job_detail_does_not_mark_applied(client, student_auth):
    headers, _ = student_auth
    listing = await client.get("/api/v1/jobs?limit=5", headers=headers)
    job_id = listing.json()["items"][0]["id"]
    detail = await client.get(f"/api/v1/jobs/{job_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["application_status"] is None


@pytest.mark.asyncio
async def test_concurrent_autosave_keeps_one_answer_row(client, student_auth):
    headers, _ = student_auth
    catalog = await client.get("/api/v1/practice/catalog", headers=headers)
    aptitude = next(domain for domain in catalog.json()["domains"] if domain["slug"] == "placement")
    category = next(cat for cat in aptitude["categories"] if cat["slug"] == "aptitude")
    topic = category["topics"][0]
    created = await client.post(
        "/api/v1/practice/sessions",
        headers=headers,
        json={
            "category_id": category["id"],
            "topic_id": topic["id"],
            "difficulty": "easy",
            "question_count": 1,
            "mode": "practice",
        },
    )
    assert created.status_code == 200, created.text
    session_id = created.json()["id"]
    question = await client.get(
        f"/api/v1/practice/sessions/{session_id}/questions/1",
        headers=headers,
    )
    option_id = question.json()["question"]["options"][0]["id"]

    async def autosave(option: str):
        return await client.post(
            f"/api/v1/practice/sessions/{session_id}/questions/1/autosave",
            headers=headers,
            json={
                "selected_option_ids": [option],
                "marked_for_review": False,
                "time_spent_seconds": 3,
            },
        )

    first, second = await asyncio.gather(autosave(option_id), autosave(option_id))
    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text

    async with AsyncSessionLocal() as db:
        count = await db.scalar(
            select(func.count())
            .select_from(PracticeAnswer)
            .where(PracticeAnswer.session_id == uuid.UUID(session_id))
        )
    assert count == 1
