"""Audit remediation: bootstrap promotion, project evidence, readiness split, SQL metadata."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.config import settings
from app.models.enums import UserRole
from app.readiness.formulas import DEFAULT_SOURCE_WEIGHTS, FORMULA_VERSION
from app.seed.runner import ensure_seed_admin
from app.services.sql_execution.executor import MockSqlSandboxExecutor


@pytest.mark.asyncio
async def test_bootstrap_does_not_promote_existing_student(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    email = "student.bootstrap@example.com"
    monkeypatch.setattr(settings, "admin_bootstrap_email", email)
    monkeypatch.setattr(settings, "admin_bootstrap_password", "SecureBootstrap1!")

    student = MagicMock()
    student.email = email
    student.role = UserRole.STUDENT

    session = MagicMock()
    no_admin = MagicMock()
    no_admin.scalar_one_or_none.return_value = None
    existing = MagicMock()
    existing.scalar_one_or_none.return_value = student
    session.execute = AsyncMock(side_effect=[no_admin, existing])
    session.add = MagicMock()
    session.flush = AsyncMock()

    result = await ensure_seed_admin(session)
    assert result is None
    assert student.role == UserRole.STUDENT
    session.add.assert_not_called()
    session.flush.assert_not_called()


def test_self_reported_sources_do_not_weight_competence():
    assert DEFAULT_SOURCE_WEIGHTS["project"] == 0.0
    assert DEFAULT_SOURCE_WEIGHTS["course"] == 0.0
    assert DEFAULT_SOURCE_WEIGHTS["sql"] > 0
    assert FORMULA_VERSION == "2.1.0"


@pytest.mark.asyncio
async def test_mock_executor_keeps_columns_on_empty_result_and_detects_overflow():
    executor = MockSqlSandboxExecutor()
    empty = await executor.execute(
        "SELECT id FROM products WHERE false",
        [{"columns": [{"column_name": "id"}], "rows": []}],
        for_submit=True,
        max_rows=2,
    )
    assert empty.columns == ["id"]
    assert empty.rows == []
    assert empty.error is None

    overflow = await executor.execute(
        "SELECT id FROM products",
        [
            {
                "columns": [{"column_name": "id"}],
                "rows": [{"id": 1}, {"id": 2}, {"id": 3}],
            }
        ],
        for_submit=True,
        max_rows=2,
    )
    assert overflow.error is not None
    assert "maximum allowed row count" in overflow.error
    assert overflow.columns == ["id"]


@pytest.mark.asyncio
async def test_sql_linked_project_task_rejects_manual_complete(client, student_auth):
    from sqlalchemy import select

    from app.db.session import AsyncSessionLocal
    from app.models.learn import ProjectTask
    from app.models.sql_practice import SqlProblem

    headers = student_auth[0] if isinstance(student_auth, tuple) else student_auth
    listing = await client.get("/api/v1/projects", headers=headers)
    if listing.status_code != 200 or not listing.json():
        pytest.skip("No published project seeded")
    slug = listing.json()[0]["slug"]
    detail = await client.get(f"/api/v1/projects/{slug}", headers=headers)
    assert detail.status_code == 200
    body = detail.json()
    task = body["modules"][0]["tasks"][0]
    task_id = uuid.UUID(task["id"])
    project_id = body["id"]

    async with AsyncSessionLocal() as session:
        sql_problem = (await session.execute(select(SqlProblem).limit(1))).scalar_one_or_none()
        if sql_problem is None:
            pytest.skip("No SQL problem seeded")
        row = await session.get(ProjectTask, task_id)
        assert row is not None
        original_sql = row.sql_problem_id
        original_type = row.task_type
        row.sql_problem_id = sql_problem.id
        await session.commit()

    try:
        done = await client.post(
            f"/api/v1/projects/{project_id}/tasks/{task_id}/complete",
            headers=headers,
        )
        assert done.status_code == 409, done.text
        assert "sql" in done.json()["detail"].lower()
    finally:
        async with AsyncSessionLocal() as session:
            row = await session.get(ProjectTask, task_id)
            if row is not None:
                row.sql_problem_id = original_sql
                row.task_type = original_type
                await session.commit()


@pytest.mark.asyncio
async def test_concurrency_slot_does_not_swallow_body_exceptions(monkeypatch):
    from app.services.code_execution.rate_limit import concurrency_slot

    class _Redis:
        async def incr(self, _key):
            return 1

        async def expire(self, _key, _ttl):
            return True

        async def decr(self, _key):
            return 0

    async def _redis():
        return _Redis()

    monkeypatch.setattr(settings, "coding_max_concurrent_executions_per_user", 1)
    monkeypatch.setattr("app.services.code_execution.rate_limit.get_redis", _redis)

    with pytest.raises(RuntimeError, match="executor failed"):
        async with concurrency_slot(uuid.uuid4()):
            raise RuntimeError("executor failed")
