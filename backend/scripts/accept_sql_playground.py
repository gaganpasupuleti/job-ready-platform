"""Acceptance: real SQL playground execution against the local sandbox.

Fails on HTTP 503. Does not mock the executor.
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path
from typing import Any

# Running as `python scripts/...` puts scripts/ first on sys.path; keep backend root first.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from app.db.session import AsyncSessionLocal
from app.main import app
from app.models.readiness import MistakeItem, UserRoleReadinessSnapshot
from app.models.sql_practice import SqlProblemProgress, SqlSubmission
from app.models.studio import AssignmentSubmission


DATASETS = {
    "campus-bookstore": {
        "valid": "SELECT title FROM books WHERE in_stock = true ORDER BY title",
        "expect_titles": ["City Maps", "Ledger Basics", "Quiet Algorithms"],
        "invalid": "SELECT missing_column FROM books",
        "blocked": "DELETE FROM books",
    },
    "clinic-visits": {
        "valid": "SELECT patient_name FROM visits ORDER BY id",
        "expect_names": ["Meera", "Omar", "Meera", "Lila"],
        "invalid": "SELECT nope FROM visits",
        "blocked": "UPDATE visits SET fee_rupees = 0",
    },
    "course-enrollments": {
        "valid": "SELECT name FROM students WHERE year = 1 ORDER BY name",
        "expect_names": ["Anil", "Chitra"],
        "invalid": "SELECT bad FROM students",
        "blocked": "INSERT INTO students(id, name, year, major) VALUES (99, 'X', 1, 'x')",
    },
}


async def _counts(user_id) -> dict[str, int]:
    async with AsyncSessionLocal() as db:
        sql_subs = (
            await db.execute(select(func.count()).select_from(SqlSubmission).where(SqlSubmission.user_id == user_id))
        ).scalar_one()
        progress = (
            await db.execute(
                select(func.count()).select_from(SqlProblemProgress).where(SqlProblemProgress.user_id == user_id)
            )
        ).scalar_one()
        assigns = (
            await db.execute(
                select(func.count()).select_from(AssignmentSubmission).where(AssignmentSubmission.user_id == user_id)
            )
        ).scalar_one()
        readiness = (
            await db.execute(
                select(func.count())
                .select_from(UserRoleReadinessSnapshot)
                .where(UserRoleReadinessSnapshot.user_id == user_id)
            )
        ).scalar_one()
        mistakes = (
            await db.execute(select(func.count()).select_from(MistakeItem).where(MistakeItem.user_id == user_id))
        ).scalar_one()
    return {
        "sql_submissions": int(sql_subs),
        "sql_progress": int(progress),
        "assignment_submissions": int(assigns),
        "readiness": int(readiness),
        "mistakes": int(mistakes),
    }


async def main() -> None:
    transport = ASGITransport(app=app)
    suffix = uuid.uuid4().hex[:8]
    async with AsyncClient(transport=transport, base_url="http://test", timeout=60.0) as client:
        register = await client.post(
            "/api/v1/auth/register",
            json={
                "email": f"pg_accept_{suffix}@example.com",
                "username": f"pg_accept_{suffix}",
                "full_name": "Playground Accept",
                "password": "Student123!",
            },
        )
        assert register.status_code == 200, register.text
        token = register.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        me = await client.get("/api/v1/auth/me", headers=headers)
        assert me.status_code == 200, me.text
        user_id = uuid.UUID(me.json()["id"])

        status = await client.get("/api/v1/sql/execution-status", headers=headers)
        assert status.status_code == 200, status.text
        assert status.json().get("available") is True, status.json()

        catalog = await client.get("/api/v1/sql/playground/", headers=headers)
        if catalog.status_code != 200:
            catalog = await client.get("/api/v1/sql/playground", headers=headers)
        assert catalog.status_code == 200, catalog.text
        body = catalog.json()
        assert body["assessed"] is False
        assert {row["id"] for row in body["datasets"]} >= set(DATASETS)

        before = await _counts(user_id)

        report: list[dict[str, Any]] = []
        for dataset_id, cases in DATASETS.items():
            detail = await client.get(f"/api/v1/sql/playground/datasets/{dataset_id}", headers=headers)
            assert detail.status_code == 200, detail.text
            payload = detail.json()
            assert payload["tables"], dataset_id
            assert payload["tables"][0]["columns"], dataset_id
            assert payload["tables"][0]["sample_rows"], dataset_id

            valid = await client.post(
                f"/api/v1/sql/playground/datasets/{dataset_id}/run",
                headers=headers,
                json={"query": cases["valid"]},
            )
            assert valid.status_code == 200, f"{dataset_id} valid {valid.status_code} {valid.text}"
            assert valid.status_code != 503
            v = valid.json()
            assert v["status"] == "ok", v
            assert v["assessed"] is False
            assert v["row_count"] >= 1
            assert v.get("error") in (None, "")
            rows = [row[0] for row in v["rows"]]
            if "expect_titles" in cases:
                assert rows == cases["expect_titles"], rows
            if "expect_names" in cases:
                assert rows == cases["expect_names"], rows

            invalid = await client.post(
                f"/api/v1/sql/playground/datasets/{dataset_id}/run",
                headers=headers,
                json={"query": cases["invalid"]},
            )
            assert invalid.status_code == 200, invalid.text
            inv = invalid.json()
            assert inv["status"] == "sql_error"
            assert inv.get("error"), inv

            blocked = await client.post(
                f"/api/v1/sql/playground/datasets/{dataset_id}/run",
                headers=headers,
                json={"query": cases["blocked"]},
            )
            assert blocked.status_code == 200, blocked.text
            blk = blocked.json()
            assert blk["status"] == "sql_error"
            assert blk.get("error"), blk

            report.append(
                {
                    "dataset": dataset_id,
                    "valid_rows": v["row_count"],
                    "valid_ms": v.get("execution_time_ms"),
                    "invalid_error": inv["error"][:120],
                    "blocked_error": blk["error"][:120],
                }
            )

        after = await _counts(user_id)
        assert after == before, {"before": before, "after": after}

        print("PLAYGROUND_ACCEPTANCE_OK")
        for row in report:
            print(row)
        print("counts_unchanged", after)


if __name__ == "__main__":
    asyncio.run(main())
