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
