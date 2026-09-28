"""Acceptance: Python locks, syllabus lessons, Judge0 disabled."""

from __future__ import annotations

import asyncio
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.main import app
from app.models.studio import Assignment, AssignmentReview, AssignmentSubmission
from app.content.version_snapshots import assignment_brief_snapshot


PUBLISHED_LESSONS = [
    "syl-crt-quant-percentages",
    "syl-crt-logical-patterns",
    "syl-crt-verbal-meaning",
    "syl-crt-di-tables",
    "syl-dsa-complexity",
    "syl-dsa-arrays-strings",
]


async def main() -> None:
    assert settings.judge0_enabled is False, "Judge0 must remain disabled"

    transport = ASGITransport(app=app)
    suffix = uuid.uuid4().hex[:8]
    async with AsyncClient(transport=transport, base_url="http://test", timeout=60.0) as client:
        student = await client.post(
            "/api/v1/auth/register",
            json={
                "email": f"py_accept_{suffix}@example.com",
                "username": f"py_accept_{suffix}",
                "full_name": "Python Accept",
                "password": "Student123!",
            },
        )
        assert student.status_code == 200, student.text
        headers = {"Authorization": f"Bearer {student.json()['access_token']}"}

        admin_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@jobready.dev", "password": "Admin123!"},
        )
        assert admin_login.status_code == 200, admin_login.text
        admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

        async with AsyncSessionLocal() as db:
            python_rows = (
                await db.execute(
                    select(Assignment).where(
                        (Assignment.submission_mode == "local_python")
                        | (Assignment.requires_runtime == "python")
                    )
                )
            ).scalars().all()
            untagged = [
                row.content_key
                for row in (
                    await db.execute(select(Assignment).where(Assignment.submission_mode == "local_python"))
                ).scalars().all()
                if not row.requires_runtime
            ]
            print("python_assignments", [row.content_key for row in python_rows])
            print("untagged_local_python_before_fix", untagged)

            py = (
                await db.execute(select(Assignment).where(Assignment.content_key == "py-assign-exceptions"))
            ).scalar_one()
            me = await client.get("/api/v1/auth/me", headers=headers)
            user_id = uuid.UUID(me.json()["id"])
            snapshot = assignment_brief_snapshot(py)
            historical = AssignmentSubmission(
                assignment_id=py.id,
                user_id=user_id,
                assignment_version=snapshot["version"],
                attempt_number=1,
                status="submitted",
                answer_text="historical python submission",
                evidence_url="https://example.com/history",
                submitted_at=datetime.now(UTC),
                brief_snapshot=snapshot,
            )
            db.add(historical)
            await db.flush()
            db.add(
                AssignmentReview(
                    submission_id=historical.id,
                    reviewer_id=None,
                    submission_version=historical.assignment_version,
                    feedback="Kept for lock acceptance",
                    grade="met",
                    rubric_notes=[],
                    reviewed_at=datetime.now(UTC),
                )
            )
            await db.commit()
            history_id = str(historical.id)

        catalog = await client.get("/api/v1/studio/catalog", headers=headers)
        assert catalog.status_code == 200
        keys = {row["key"] for row in catalog.json()["assignments"]}
        assert "py-assign-exceptions" not in keys
        assert "de-assign-local-validate" not in keys
        assert "da-assign-paid-totals" in keys

        detail = await client.get("/api/v1/studio/assignments/py-assign-exceptions", headers=headers)
        assert detail.status_code == 200
        body = detail.json()
        assert body["unavailable"] is True
        assert any(row["id"] == history_id for row in body["submissions"])
        assert body["submissions"][0]["reviews"]

        for path in (
            "/api/v1/studio/assignments/py-assign-exceptions/draft",
            "/api/v1/studio/assignments/py-assign-exceptions/submit",
        ):
            blocked = await client.post(
                path,
                headers=headers,
                json={"answer_text": "bypass", "evidence_url": "https://example.com/x"},
            )
            assert blocked.status_code == 409, (path, blocked.text)

        after = await client.get("/api/v1/studio/assignments/py-assign-exceptions", headers=headers)
        assert len(after.json()["submissions"]) == 1
        assert after.json()["submissions"][0]["answer_text"] == "historical python submission"

        # Non-Python assignment still accepts drafts/submissions.
        ok = await client.post(
            "/api/v1/studio/assignments/da-assign-paid-totals/draft",
            headers=headers,
            json={"answer_text": "sql draft note", "evidence_url": "https://example.com/sql"},
        )
        assert ok.status_code == 200, ok.text

        # Python reading material remains readable.
        materials = await client.get("/api/v1/studio/catalog", headers=headers)
        material_keys = {row["key"] for row in materials.json()["materials"]}
        py_materials = [key for key in material_keys if key.startswith("py-") or "python" in key]
        for key in py_materials:
            mat = await client.get(f"/api/v1/studio/materials/{key}", headers=headers)
            assert mat.status_code == 200, key

        # Coding playground Python remains locked.
        playground = await client.post(
            "/api/v1/coding/playground/run",
            headers=headers,
            json={"source_code": "print(1)", "language_id": 71, "stdin": ""},
        )
        assert playground.status_code == 200, playground.text
        assert playground.json().get("available") is False

        exec_status = await client.get("/api/v1/coding/execution-status", headers=headers)
        assert exec_status.status_code == 200
        assert exec_status.json().get("available") is False

        # Syllabus journey
        syl = await client.get("/api/v1/studio/syllabus", headers=headers)
        assert syl.status_code == 200
        tracks = {track["id"]: track for track in syl.json()["tracks"]}
        assert "crt" in tracks and "dsa" in tracks
        crt_units = {unit["id"] for unit in tracks["crt"]["units"]}
        assert crt_units >= {"quantitative", "logical", "verbal", "data-interpretation"}
        dsa_units = [unit["id"] for unit in sorted(tracks["dsa"]["units"], key=lambda row: row["position"])]
        assert dsa_units == [
            "complexity",
            "arrays-strings",
            "searching-sorting",
            "hashing",
            "linked-lists",
            "stacks-queues",
            "recursion",
            "trees",
            "heaps",
            "graphs",
            "dynamic-programming",
        ]

        for key in PUBLISHED_LESSONS:
            lesson = await client.get(f"/api/v1/studio/syllabus/{key}", headers=headers)
            assert lesson.status_code == 200, key
            payload = lesson.json()
            assert payload["status"] == "published"
            assert payload["material"]
            assert "body_md" in payload["material"]
            assert payload["practice"]
            q = payload["practice"][0]
            # Answer keys must not be present before checking.
            assert all("correct" not in opt for opt in q["options"])
            wrong = await client.post(
                f"/api/v1/studio/syllabus/{key}/practice/{q['key']}",
                headers=headers,
                json={"selected": ["1"]},
            )
            assert wrong.status_code == 200
            checked = wrong.json()
            assert "correct_keys" in checked
            assert checked["competence"] is False
            assert checked.get("explanation")
            read = await client.post(f"/api/v1/studio/materials/{payload['material_key']}/read", headers=headers)
            assert read.status_code == 200
            assert read.json().get("competence") is False

        coming = await client.get("/api/v1/studio/syllabus/syl-dsa-graphs", headers=headers)
        assert coming.status_code == 200
        assert coming.json()["status"] == "coming_soon"
        assert coming.json()["material"] is None

        # Locked python project milestone completion (explicit metadata)
        async with AsyncSessionLocal() as db:
            from app.models.learn import Project, ProjectModule, ProjectTask
            from app.models.learn_enums import PathAvailability, PracticePathDifficulty, ProjectTaskType

            project = Project(
                slug=f"py-lock-{suffix}",
                title="Mixed lock project",
                short_description="SQL plus locked Python",
                description="Acceptance fixture",
                difficulty=PracticePathDifficulty.BEGINNER,
                technology="mixed",
                category_key="mixed",
                estimated_minutes=30,
                is_published=True,
                availability=PathAvailability.AVAILABLE,
                prerequisites=[],
                skills=["sql"],
                final_objective="Do not complete while Python is locked",
                reference_json={},
            )
            db.add(project)
            await db.flush()
            module = ProjectModule(project_id=project.id, title="Module", sort_order=0)
            db.add(module)
            await db.flush()
            open_task = ProjectTask(
                module_id=module.id,
                title="Review note",
                sort_order=0,
                task_type=ProjectTaskType.REVIEW,
                summary="Writable",
                body_json={"note": "open"},
                checklist_json=[],
            )
            locked_task = ProjectTask(
                module_id=module.id,
                title="Python milestone",
                sort_order=1,
                task_type=ProjectTaskType.REVIEW,
                summary="Locked python work",
                body_json={"requires_runtime": "python", "note": "locked"},
                checklist_json=[],
            )
            db.add_all([open_task, locked_task])
            await db.commit()
            project_id = str(project.id)
            locked_id = str(locked_task.id)
            open_id = str(open_task.id)
            project_slug = project.slug

        detail_project = await client.get(f"/api/v1/projects/{project_slug}", headers=headers)
        assert detail_project.status_code == 200, detail_project.text
        assert detail_project.json().get("completion_blocked") is True
        locked_rows = [
            task
            for module in detail_project.json()["modules"]
            for task in module["tasks"]
            if task["id"] == locked_id
        ]
        assert locked_rows and locked_rows[0]["locked"] is True

        blocked_complete = await client.post(
            f"/api/v1/projects/{project_id}/tasks/{locked_id}/complete",
            headers=headers,
        )
        assert blocked_complete.status_code == 409, blocked_complete.text

        open_complete = await client.post(
            f"/api/v1/projects/{project_id}/tasks/{open_id}/complete",
            headers=headers,
        )
        assert open_complete.status_code == 200, open_complete.text

        print("PYTHON_SYLLABUS_ACCEPTANCE_OK")


if __name__ == "__main__":
    asyncio.run(main())
