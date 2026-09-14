"""SQL content versions grade new attempts only. Old results stay stored."""

import copy
import uuid

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.content.studio_batch import refresh_sql_problem, shop_dataset
from app.db.session import AsyncSessionLocal
from app.models.sql_practice import SqlProblem, SqlProblemTable, SqlSubmission
from app.models.taxonomy import Topic

PAID = "SELECT COUNT(*) AS paid_orders, SUM(amount) AS paid_amount FROM orders WHERE status = 'paid'"
WRONG = "SELECT COUNT(*) AS paid_orders, SUM(amount) AS paid_amount FROM orders"


async def _topic(db):
    return (await db.execute(select(Topic).where(Topic.slug == "studio-saturday-001"))).scalar_one()


@pytest.mark.asyncio
async def test_sql_version_changes_grading_without_rewriting_history(client, student_auth):
    slug = f"sql-version-probe-{uuid.uuid4().hex[:8]}"
    v1 = {
        "title": "Paid order totals",
        "task": "Return paid_orders and paid_amount for status = 'paid'.",
        "solution": PAID,
        "columns": ["paid_orders", "paid_amount"],
        "rows": [[2, 1800]],
        "order_sensitive": False,
    }
    tables_v1 = shop_dataset()
    async with AsyncSessionLocal() as db:
        topic = await _topic(db)
        await refresh_sql_problem(db, topic, slug, v1, tables_v1, 1, replace=False)
        await db.commit()

    detail = await client.get(f"/api/v1/sql/problems/{slug}", headers=student_auth[0])
    assert detail.status_code == 200, detail.text
    body = detail.json()
    assert body["content_version"] == 1
    assert body["sample_expected_rows"] == []
    assert [2, 1800] not in body["sample_expected_rows"]

    run = await client.post(
        f"/api/v1/sql/problems/{body['id']}/run",
        headers=student_auth[0],
        json={"query": PAID},
    )
    assert run.status_code == 200, run.text
    assert run.json()["status"] == "ok"
    assert run.json()["rows"] == [[2, 1800]]

    accepted = await client.post(
        f"/api/v1/sql/problems/{body['id']}/submit",
        headers=student_auth[0],
        json={"query": PAID},
    )
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["status"] == "accepted"
    first_id = accepted.json()["submission_id"]

    rejected = await client.post(
        f"/api/v1/sql/problems/{body['id']}/submit",
        headers=student_auth[0],
        json={"query": WRONG},
    )
    assert rejected.status_code == 200, rejected.text
    assert rejected.json()["status"] == "wrong_answer"

    tables_v2 = copy.deepcopy(tables_v1)
    tables_v2[1]["rows"].append(
        {"id": 6, "customer_id": 1, "status": "paid", "amount": 200, "ordered_on": "2026-01-07"}
    )
    tables_v2[2]["rows"].append({"id": 3, "order_id": 6, "amount": 200, "paid_on": "2026-01-07"})
    v2 = {**v1, "task": "Return paid totals after the new paid order.", "rows": [[3, 2000]]}
    async with AsyncSessionLocal() as db:
        topic = await _topic(db)
        before = (
            await db.execute(select(func.count()).select_from(SqlProblem).where(SqlProblem.slug == slug))
        ).scalar_one()
        await refresh_sql_problem(db, topic, slug, v2, tables_v2, 2, replace=True)
        await db.commit()
        after = (
            await db.execute(select(func.count()).select_from(SqlProblem).where(SqlProblem.slug == slug))
        ).scalar_one()
        assert before == after == 1

    published = await client.get(f"/api/v1/sql/problems/{slug}", headers=student_auth[0])
    assert published.json()["content_version"] == 2
    assert published.json()["task_description"] == v2["task"]
    assert published.json()["sample_expected_rows"] == []
    assert published.json()["solution_unlocked"] is False

    run_v2 = await client.post(
        f"/api/v1/sql/problems/{body['id']}/run",
        headers=student_auth[0],
        json={"query": PAID},
    )
    assert run_v2.json()["rows"] == [[3, 2000]]

    now_wrong = await client.post(
        f"/api/v1/sql/problems/{body['id']}/submit",
        headers=student_auth[0],
        json={"query": "SELECT 2 AS paid_orders, 1800 AS paid_amount"},
    )
    assert now_wrong.json()["status"] == "wrong_answer"
    still_accepted = await client.post(
        f"/api/v1/sql/problems/{body['id']}/submit",
        headers=student_auth[0],
        json={"query": PAID},
    )
    assert still_accepted.json()["status"] == "accepted"
    assert still_accepted.json()["content_version"] == 2

    async with AsyncSessionLocal() as db:
        topic = await _topic(db)
        first = await db.get(SqlSubmission, uuid.UUID(first_id))
        assert first.status.value == "accepted"
        assert first.content_version == 1
        problem = (
            await db.execute(
                select(SqlProblem)
                .options(
                    selectinload(SqlProblem.expected_result),
                    selectinload(SqlProblem.tables).selectinload(SqlProblemTable.seed_rows),
                )
                .where(SqlProblem.slug == slug)
            )
        ).scalar_one()
        table_ids = sorted(table.id for table in problem.tables)
        seed_count = sum(len(table.seed_rows) for table in problem.tables)
        await refresh_sql_problem(db, topic, slug, v2, tables_v2, 2, replace=False)
        await db.commit()
        again_problem = (
            await db.execute(
                select(SqlProblem)
                .options(
                    selectinload(SqlProblem.expected_result),
                    selectinload(SqlProblem.tables).selectinload(SqlProblemTable.seed_rows),
                )
                .where(SqlProblem.slug == slug)
            )
        ).scalar_one()
        assert again_problem.content_version == 2
        assert sorted(table.id for table in again_problem.tables) == table_ids
        assert sum(len(table.seed_rows) for table in again_problem.tables) == seed_count
        assert again_problem.expected_result.rows == [[3, 2000]]
        again = await db.get(SqlSubmission, uuid.UUID(first_id))
        assert again.status.value == "accepted"
        assert again.content_version == 1
        await db.delete(again_problem)
        await db.commit()
