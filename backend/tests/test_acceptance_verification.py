"""Focused proofs for the original audit failure cases.

Live SQL and CONNECT checks use the configured sandbox/app databases.
They fail closed when those checks are requested and the setup is unavailable.
"""

from __future__ import annotations

import asyncio
import os
import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from sqlalchemy import select

from app.core.config import settings
from app.core.exceptions import AppException
from app.db.session import AsyncSessionLocal
from app.models.enums import SessionStatus
from app.models.practice import PracticeSession
from app.schemas.coding import PlaygroundRunRequest
from app.services.code_execution.interface import ExecutionResult
from app.services.skill_evidence_service import SkillEvidenceService, SourceBreakdown
from app.services.sql_execution.executor import SqlSandboxExecutor
from app.services.sql_execution.safety import validate_sql_query


def _headers(student_auth):
    headers, _email = student_auth
    return headers


async def _start_exam(client, headers, *, question_count=1, duration_minutes=30):
    catalog = await client.get("/api/v1/practice/catalog", headers=headers)
    assert catalog.status_code == 200, catalog.text
    topic = catalog.json()["domains"][0]["categories"][0]["topics"][0]
    session_resp = await client.post(
        "/api/v1/practice/sessions",
        headers=headers,
        json={
            "category_id": catalog.json()["domains"][0]["categories"][0]["id"],
            "topic_id": topic["id"],
            "question_count": question_count,
            "mode": "exam",
            "duration_minutes": duration_minutes,
        },
    )
    assert session_resp.status_code == 200, session_resp.text
    return session_resp.json()


def _autosave(client, headers, session_id, option_ids):
    return client.post(
        f"/api/v1/practice/sessions/{session_id}/questions/1/autosave",
        headers=headers,
        json={
            "selected_option_ids": option_ids,
            "marked_for_review": False,
            "time_spent_seconds": 2,
        },
    )


# --- SQL set operations -----------------------------------------------------


def test_readonly_set_operations_are_allowed_and_still_bounded():
    assert validate_sql_query("SELECT 1 AS n UNION ALL SELECT 2") is None
    assert validate_sql_query("SELECT 1 EXCEPT SELECT 2") is None
    assert validate_sql_query("SELECT 1 INTERSECT SELECT 1") is None
    assert validate_sql_query(
        "WITH x AS (SELECT 1 AS n) SELECT n FROM x UNION ALL SELECT 2"
    ) is None

    qualified = validate_sql_query("SELECT id FROM public.items UNION SELECT id FROM items")
    assert qualified and "Schema-qualified" in qualified
    mutating = validate_sql_query("SELECT 1; DELETE FROM items")
    assert mutating and "Multiple SQL" in mutating
    dml = validate_sql_query("WITH u AS (INSERT INTO items(id) VALUES (1) RETURNING id) SELECT id FROM u")
    assert dml and "INSERT" in dml


# --- Real SQL executor ------------------------------------------------------


_TABLES = [
    {
        "table_name": "items",
        "columns": [
            {"column_name": "id", "data_type": "INTEGER", "is_nullable": False},
            {"column_name": "name", "data_type": "TEXT", "is_nullable": True},
        ],
        "rows": [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}],
    }
]


@pytest.mark.asyncio
async def test_real_executor_empty_metadata_overflow_and_set_ops():
    executor = SqlSandboxExecutor()
    if not executor.is_available():
        pytest.fail("SQL execution is disabled; empty-result and overflow were not proven")

    empty = await executor.execute(
        "SELECT id, name FROM items WHERE id < 0",
        _TABLES,
        for_submit=True,
        max_rows=10,
    )
    assert empty.error is None, empty.error
    assert empty.disabled is False
    assert empty.columns == ["id", "name"]
    assert empty.rows == []
    assert empty.row_count == 0

    overflow = await executor.execute(
        "SELECT id, name FROM items",
        _TABLES,
        for_submit=True,
        max_rows=1,
    )
    assert overflow.error is not None
    assert "maximum allowed row count" in overflow.error

    truncated = await executor.execute(
        "SELECT id, name FROM items",
        _TABLES,
        for_submit=False,
        max_rows=1,
    )
    assert truncated.error is None, truncated.error
    assert truncated.truncated is True
    assert truncated.row_count == 1
    assert truncated.columns == ["id", "name"]

    combined = await executor.execute(
        "SELECT id, name FROM items WHERE id = 1 UNION ALL SELECT id, name FROM items WHERE id = 2",
        _TABLES,
        for_submit=True,
        max_rows=10,
    )
    assert combined.error is None, combined.error
    assert combined.columns == ["id", "name"]
    assert combined.row_count == 2


# --- Enabled playground provider --------------------------------------------


class _EnabledProvider:
    def __init__(self, *, fail=False):
        self.calls = 0
        self.fail = fail

    async def execute(self, _request):
        self.calls += 1
        if self.fail:
            raise RuntimeError("provider body failed")
        return ExecutionResult(stdout="ok", stderr="", status="accepted", time=0.01, memory=8)


class _Redis:
    def __init__(self):
        self.store: dict[str, int] = {}

    async def incr(self, key):
        self.store[key] = int(self.store.get(key, 0)) + 1
        return self.store[key]

    async def decr(self, key):
        self.store[key] = int(self.store.get(key, 0)) - 1
        return self.store[key]

    async def expire(self, _key, _ttl):
        return True


def _user():
    return SimpleNamespace(id=uuid.uuid4())


@pytest.mark.asyncio
async def test_enabled_playground_quota_concurrency_and_release(monkeypatch):
    from app.services import coding_service as coding_mod
    from app.services.code_execution import rate_limit as rate_mod

    redis = _Redis()

    async def _get_redis():
        return redis

    monkeypatch.setattr(settings, "judge0_enabled", True)
    monkeypatch.setattr(settings, "coding_runs_per_minute", 2)
    monkeypatch.setattr(settings, "coding_max_concurrent_executions_per_user", 1)
    monkeypatch.setattr(rate_mod, "get_redis", _get_redis)

    provider = _EnabledProvider()
    service = coding_mod.CodingService(db=None, executor=provider)
    assert service.is_execution_available() is True
    user = _user()
    payload = PlaygroundRunRequest(source_code="print(1)", language_id=71, stdin="")

    first = await service.playground_run(user, payload)
    second = await service.playground_run(user, payload)
    assert first.available is True and second.available is True
    assert provider.calls == 2
    concurrent_key = f"coding:concurrent:{user.id}"
    assert redis.store[concurrent_key] == 0

    with pytest.raises(AppException) as quota:
        await service.playground_run(user, payload)
    assert quota.value.status_code == 429
    assert provider.calls == 2
    assert redis.store[concurrent_key] == 0

    # Cap: an already-held slot must reject without leaking the increment.
    capped_user = _user()
    capped_key = f"coding:concurrent:{capped_user.id}"
    redis.store[f"coding:rate:run:{capped_user.id}"] = 0
    redis.store[capped_key] = 1
    with pytest.raises(AppException) as capped:
        await service.playground_run(capped_user, payload)
    assert capped.value.status_code == 429
    assert redis.store[capped_key] == 1

    failing = _EnabledProvider(fail=True)
    failing_service = coding_mod.CodingService(db=None, executor=failing)
    boom_user = _user()
    with pytest.raises(RuntimeError, match="provider body failed"):
        await failing_service.playground_run(boom_user, payload)
    assert redis.store[f"coding:concurrent:{boom_user.id}"] == 0
    assert failing.calls == 1


# --- Readiness: self-reported activity --------------------------------------


@pytest.mark.asyncio
async def test_self_reported_only_activity_never_qualifies_as_assessed():
    service = SkillEvidenceService(db=MagicMock())
    skill = SimpleNamespace(id=uuid.uuid4(), name="Python", slug="python")

    async def skills():
        return {"python": skill, "sql": skill}

    async def empty(_user_id):
        return {}

    async def projects(_user_id):
        return {
            "python": SourceBreakdown(source="project", score=100, activity_count=4),
        }

    async def courses(_user_id):
        return {
            "python": SourceBreakdown(source="course", score=80, activity_count=2),
        }

    async def sql_only(_user_id):
        return {"sql": SourceBreakdown(source="sql", score=70, activity_count=3)}

    service._skills_by_slug = skills
    for name in (
        "_mcq_by_skill",
        "_sql_by_skill",
        "_coding_by_skill",
        "_prompt_by_skill",
        "_scenario_by_skill",
        "_interview_by_skill",
        "_project_by_skill",
        "_course_by_skill",
    ):
        setattr(service, name, empty)
    service._project_by_skill = projects
    service._course_by_skill = courses

    only_self = await service.collect_all(uuid.uuid4())
    assert "python" not in only_self

    service._sql_by_skill = sql_only
    mixed = await service.collect_all(uuid.uuid4())
    assert "python" not in mixed
    assert "sql" in mixed
    assert mixed["sql"].counts_toward_competence is True
    assert [s.source for s in mixed["sql"].sources] == ["sql"]
    assert mixed["sql"].activity_count == 3


# --- MCQ sessions -----------------------------------------------------------


@pytest.mark.asyncio
async def test_active_exam_keeps_intended_answer_edits(client, student_auth):
    headers = _headers(student_auth)
    session = await _start_exam(client, headers)
    session_id = session["id"]
    question = await client.get(
        f"/api/v1/practice/sessions/{session_id}/questions/1", headers=headers
    )
    options = question.json()["question"]["options"]
    assert len(options) >= 2
    first_id, second_id = options[0]["id"], options[1]["id"]

    saved = await _autosave(client, headers, session_id, [first_id])
    edited = await _autosave(client, headers, session_id, [second_id])
    assert saved.status_code == 200, saved.text
    assert edited.status_code == 200, edited.text

    restored = await client.get(
        f"/api/v1/practice/sessions/{session_id}/questions/1", headers=headers
    )
    assert restored.json()["selected_option_ids"] == [second_id]
    detail = await client.get(f"/api/v1/practice/sessions/{session_id}", headers=headers)
    assert detail.json()["status"] == "active"
    blocked = await client.get(
        f"/api/v1/practice/sessions/{session_id}/results", headers=headers
    )
    assert blocked.status_code == 400


@pytest.mark.asyncio
async def test_exam_save_complete_and_expiry_across_separate_sessions(client, student_auth):
    headers = _headers(student_auth)
    session = await _start_exam(client, headers)
    session_id = session["id"]
    question = await client.get(
        f"/api/v1/practice/sessions/{session_id}/questions/1", headers=headers
    )
    options = question.json()["question"]["options"]
    option_a, option_b = options[0]["id"], options[1]["id"]
    seeded = await _autosave(client, headers, session_id, [option_a])
    assert seeded.status_code == 200, seeded.text

    save_resp, complete_resp = await asyncio.gather(
        _autosave(client, headers, session_id, [option_b]),
        client.post(f"/api/v1/practice/sessions/{session_id}/complete", headers=headers),
    )
    assert save_resp.status_code in {200, 400, 409}, save_resp.text
    if complete_resp.status_code != 200:
        complete_resp = await client.post(
            f"/api/v1/practice/sessions/{session_id}/complete", headers=headers
        )
    assert complete_resp.status_code == 200, complete_resp.text

    late = await _autosave(client, headers, session_id, [option_a])
    assert late.status_code in {400, 409}
    results = await client.get(
        f"/api/v1/practice/sessions/{session_id}/results", headers=headers
    )
    assert results.status_code == 200, results.text
    selected = results.json()["questions"][0]["selected_option_ids"]
    assert selected in ([option_a], [option_b])

    # A second exam: expiry committed on one connection, writes issued on others.
    other = await _start_exam(client, headers)
    other_id = other["id"]
    other_q = await client.get(
        f"/api/v1/practice/sessions/{other_id}/questions/1", headers=headers
    )
    other_option = other_q.json()["question"]["options"][0]["id"]
    async with AsyncSessionLocal() as db:
        row = (
            await db.execute(select(PracticeSession).where(PracticeSession.id == UUID(other_id)))
        ).scalar_one()
        row.expires_at = datetime.now(UTC) - timedelta(seconds=5)
        await db.commit()

    late_save, late_complete = await asyncio.gather(
        _autosave(client, headers, other_id, [other_option]),
        client.post(f"/api/v1/practice/sessions/{other_id}/complete", headers=headers),
    )
    assert late_save.status_code in {200, 400, 409}
    assert late_complete.status_code == 200
    after = await client.get(f"/api/v1/practice/sessions/{other_id}", headers=headers)
    assert after.json()["status"] == SessionStatus.COMPLETED.value
    rejected = await _autosave(client, headers, other_id, [other_option])
    assert rejected.status_code in {400, 409}


# --- CONNECT restriction ----------------------------------------------------


@pytest.mark.asyncio
async def test_connect_restriction_is_repeatable(monkeypatch):
    from app.services.sql_execution import roles as roles_mod

    executed: list[str] = []

    class _Conn:
        async def execute(self, sql):
            executed.append(sql)

        async def fetchval(self, _sql):
            return "jobready"

        async def close(self):
            return None

    async def _connect(_dsn):
        return _Conn()

    monkeypatch.setattr(settings, "sql_execution_enabled", True)
    monkeypatch.setattr(settings, "sql_sandbox_runner_role", "jobready_sql_runner")
    monkeypatch.setattr(
        settings,
        "database_url",
        "postgresql+asyncpg://jobready:secret@localhost:5432/jobready_db",
    )
    monkeypatch.setattr(
        roles_mod,
        "admin_dsn",
        lambda: "postgresql://jobready_sql_admin:secret@localhost:5432/jobready_sql_sandbox",
    )
    monkeypatch.setattr(roles_mod.asyncpg, "connect", _connect)

    await roles_mod.restrict_runner_from_app_database()
    await roles_mod.restrict_runner_from_app_database()
    assert len(executed) == 6
    assert executed[0] == executed[3]
    assert "REVOKE CONNECT ON DATABASE" in executed[0]
    assert "GRANT CONNECT ON DATABASE" in executed[2]


@pytest.mark.asyncio
async def test_live_connect_role_access_after_repeat_restriction():
    if os.environ.get("JOBREADY_LIVE_PRIVILEGE_CHECK") != "1":
        pytest.skip("Set JOBREADY_LIVE_PRIVILEGE_CHECK=1 to apply and verify live CONNECT grants")

    import asyncpg
    from urllib.parse import urlparse

    from app.services.sql_execution.pools import admin_dsn, to_asyncpg_dsn
    from app.services.sql_execution.roles import restrict_runner_from_app_database

    await restrict_runner_from_app_database()
    await restrict_runner_from_app_database()

    app_conn = await asyncpg.connect(to_asyncpg_dsn(settings.database_url))
    await app_conn.execute("SELECT 1")
    await app_conn.close()

    app = urlparse(to_asyncpg_dsn(settings.database_url))
    with pytest.raises(asyncpg.PostgresError) as denied:
        await asyncpg.connect(
            user=settings.sql_sandbox_runner_role,
            password=settings.sql_sandbox_runner_password,
            host=app.hostname or "localhost",
            port=app.port or 5432,
            database=app.path.lstrip("/"),
        )
    assert "permission denied" in str(denied.value).lower()

    sandbox = urlparse(to_asyncpg_dsn(admin_dsn()))
    runner = await asyncpg.connect(
        user=settings.sql_sandbox_runner_role,
        password=settings.sql_sandbox_runner_password,
        host=sandbox.hostname or "localhost",
        port=sandbox.port or 5432,
        database=sandbox.path.lstrip("/"),
    )
    await runner.execute("SELECT 1")
    await runner.close()
