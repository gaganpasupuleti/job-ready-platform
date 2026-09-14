"""Focused checks for the Saturday batch and assignment isolation."""

import uuid
from pathlib import Path

import pytest

from app.content.studio_batch import load_batch, plan


BATCH = Path(__file__).resolve().parents[1] / "content" / "batches" / "2026-09-19-saturday-001"


def test_saturday_batch_is_complete_and_rejects_hash_drift(tmp_path):
    batch = load_batch(BATCH)
    assert batch["rejected"] == []
    assert len(batch["materials"]) == 6
    assert len(batch["assignments"]) == 3
    assert len(batch["questions"]) == 50
    assert len(batch["packs"]) == 4
    assert len(batch["project"]["milestones"]) == 4 
    modes = {row["mode"] for row in batch["questions"]}
    assert modes <= {"single", "multi"}
    first = plan(batch, {})
    assert first["counts"]["question"]["create"] == 50
    stored = {}
    class _Item:
        def __init__(self, action):
            self.content_hash = action["hash"]
            self.version = action["version"]
    for action in first["actions"]:
        stored[action["key"]] = _Item(action)
    second = plan(batch, stored)
    assert second["counts"]["question"]["unchanged"] == 50
    assert second["rejected"] == []
    stored["da-q01"].content_hash = "changed"
    third = plan(batch, stored)
    assert any("da-q01" in item for item in third["rejected"])
    assert any(row["key"] == "da-q02" and row["mode"] == "multi" for row in batch["questions"])


@pytest.mark.asyncio
async def test_assignment_is_private_and_reviewable(client, student_auth, admin_auth):
    token = uuid.uuid4().hex[:8]
    other = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"studio_other_{token}@example.com",
            "username": f"studio_other_{token}",
            "full_name": "Other Student",
            "password": "Student123!",
        },
    )
    assert other.status_code == 200, other.text
    other_headers = {"Authorization": f"Bearer {other.json()['access_token']}"}
    submit = await client.post(
        "/api/v1/studio/assignments/py-assign-exceptions/submit",
        headers=student_auth[0],
        json={"answer_text": "def parse_amount(text):\n    return int(text)\n", "evidence_url": "https://example.com/repo"},
    )
    assert submit.status_code == 200, submit.text
    hidden = await client.get("/api/v1/studio/assignments/py-assign-exceptions", headers=other_headers)
    assert hidden.status_code == 200
    assert hidden.json()["submissions"] == []
    mine = await client.get("/api/v1/studio/assignments/py-assign-exceptions", headers=student_auth[0])
    submission = mine.json()["submissions"][-1]
    blocked = await client.get("/api/v1/admin/studio/submissions", headers=student_auth[0])
    assert blocked.status_code == 403
    review = await client.post(
        f"/api/v1/admin/studio/submissions/{submission['id']}/review",
        headers=admin_auth,
        json={"feedback": "Local function is readable.", "grade": "met"},
    )
    assert review.status_code == 200, review.text
    after = await client.get("/api/v1/studio/assignments/py-assign-exceptions", headers=student_auth[0])
    reviewed = next(item for item in after.json()["submissions"] if item["id"] == submission["id"])
    assert reviewed["version"] == submission["version"]
    assert reviewed["answer_text"].startswith("def parse_amount")
    assert reviewed["reviews"][0]["feedback"] == "Local function is readable."
    assert reviewed["reviews"][0]["reviewed_at"]
    resubmit = await client.post(
        "/api/v1/studio/assignments/py-assign-exceptions/submit",
        headers=student_auth[0],
        json={"answer_text": "second attempt keeps the first row", "evidence_url": "https://example.com/repo-2"},
    )
    assert resubmit.status_code == 200, resubmit.text
    history = await client.get("/api/v1/studio/assignments/py-assign-exceptions", headers=student_auth[0])
    rows = history.json()["submissions"]
    original = next(item for item in rows if item["id"] == submission["id"])
    assert original["answer_text"].startswith("def parse_amount")
    assert original["version"] == submission["version"]
    assert any(item["answer_text"] == "second attempt keeps the first row" for item in rows)
    assert len(rows) >= 2


@pytest.mark.asyncio
async def test_question_revision_does_not_rewrite_open_attempt(client, student_auth):
    started = await client.post("/api/v1/studio/packs/pack-python-dev/start", headers=student_auth[0])
    assert started.status_code == 200, started.text
    session_id = started.json()["session_id"]
    before = await client.get(
        f"/api/v1/practice/sessions/{session_id}/questions/1",
        headers=student_auth[0],
    )
    assert before.status_code == 200, before.text
    body = before.json()["question"]
    assert "explanation" not in body
    assert body["options"]
    assert "is_correct" not in body["options"][0]
    stem = body["question_text"]
    from sqlalchemy import select

    from app.db.session import AsyncSessionLocal
    from app.models.question import Question

    async with AsyncSessionLocal() as db:
        question = (await db.execute(select(Question).where(Question.content_key == "py-q01"))).scalar_one()
        original = question.question_text
        question.question_text = "REWRITTEN AFTER THE ATTEMPT STARTED"
        await db.commit()
    try:
        after = await client.get(
            f"/api/v1/practice/sessions/{session_id}/questions/1",
            headers=student_auth[0],
        )
        assert after.status_code == 200, after.text
        assert after.json()["question"]["question_text"] == stem
        assert "REWRITTEN" not in after.json()["question"]["question_text"]
    finally:
        async with AsyncSessionLocal() as db:
            question = (await db.execute(select(Question).where(Question.content_key == "py-q01"))).scalar_one()
            question.question_text = original
            await db.commit()


@pytest.mark.asyncio
async def test_filed_brief_survives_live_assignment_and_milestone_edits(client, student_auth):
    filed = await client.post(
        "/api/v1/studio/assignments/py-assign-exceptions/submit",
        headers=student_auth[0],
        json={"answer_text": "keep this brief", "evidence_url": "https://example.com/repo"},
    )
    assert filed.status_code == 200, filed.text
    detail = await client.get("/api/v1/studio/assignments/py-assign-exceptions", headers=student_auth[0])
    submission = detail.json()["submissions"][-1]
    original_brief = submission["brief"]
    original_rubric = submission["rubric"]
    assert original_brief
    assert original_rubric

    from app.db.session import AsyncSessionLocal
    from app.models.learn import ProjectTask
    from app.models.studio import Assignment
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        assignment = (
            await db.execute(select(Assignment).where(Assignment.content_key == "py-assign-exceptions"))
        ).scalar_one()
        assignment.brief_md = "NEW BRIEF AFTER SUBMISSION"
        assignment.rubric = [{"criterion": "replaced", "points": 1}]
        assignment.version = assignment.version + 1
        await db.commit()
    after = await client.get("/api/v1/studio/assignments/py-assign-exceptions", headers=student_auth[0])
    kept = next(item for item in after.json()["submissions"] if item["id"] == submission["id"])
    assert kept["brief"] == original_brief
    assert kept["rubric"] == original_rubric
    assert "NEW BRIEF" not in kept["brief"]
    assert after.json()["brief_md"] == "NEW BRIEF AFTER SUBMISSION"

    project = await client.get("/api/v1/projects/orders-payment-quality", headers=student_auth[0])
    assert project.status_code == 200, project.text
    review = next(
        task
        for module in project.json()["modules"]
        for task in module["tasks"]
        if task["task_type"] == "review"
    )
    done = await client.post(
        f"/api/v1/projects/{project.json()['id']}/tasks/{review['id']}/complete",
        headers=student_auth[0],
    )
    assert done.status_code == 200, done.text
    async with AsyncSessionLocal() as db:
        task = await db.get(ProjectTask, review["id"])
        task.title = "Rewritten milestone"
        task.summary = "Rewritten deliverable"
        await db.commit()
    again = await client.get("/api/v1/projects/orders-payment-quality", headers=student_auth[0])
    shown = next(
        task
        for module in again.json()["modules"]
        for task in module["tasks"]
        if task["id"] == review["id"]
    )
    assert shown["title"] == review["title"]
    assert shown["summary"] == review["summary"]
    async with AsyncSessionLocal() as db:
        assignment = (
            await db.execute(select(Assignment).where(Assignment.content_key == "py-assign-exceptions"))
        ).scalar_one()
        assignment.brief_md = original_brief
        assignment.rubric = original_rubric
        assignment.version = submission["version"]
        task = await db.get(ProjectTask, review["id"])
        task.title = review["title"]
        task.summary = review["summary"]
        await db.commit()
