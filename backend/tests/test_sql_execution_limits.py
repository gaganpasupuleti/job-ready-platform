"""SQL run/submit quotas are independent of coding quotas and release slots."""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.config import settings
from app.core.exceptions import AppException
from app.services.sql_execution.executor import SqlRunResult


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


class _Executor:
    def __init__(self, *, fail=False):
        self.calls = 0
        self.fail = fail

    def is_available(self):
        return True

    async def execute(self, _query, _tables, **_kwargs):
        self.calls += 1
        if self.fail:
            raise RuntimeError("executor body failed")
        return SqlRunResult(columns=["id"], rows=[[1]], row_count=1)


def _service(executor, monkeypatch, redis):
    from app.services import sql_practice_service as sql_mod
    from app.services.code_execution import rate_limit as rate_mod

    async def _get_redis():
        return redis

    monkeypatch.setattr(rate_mod, "get_redis", _get_redis)
    monkeypatch.setattr(settings, "sql_runs_per_minute", 2)
    monkeypatch.setattr(settings, "sql_submits_per_minute", 1)
    monkeypatch.setattr(settings, "sql_max_concurrent_executions_per_user", 1)
    service = sql_mod.SqlPracticeService(db=MagicMock(), executor=executor)
    problem = SimpleNamespace(id=uuid.uuid4(), is_active=True, tables=[])
    service.repo = MagicMock()
    service.repo.get_by_id = AsyncMock(return_value=problem)
    service._dataset_payload = lambda _problem: []
    return service


@pytest.mark.asyncio
async def test_sql_run_quota_concurrency_and_release(monkeypatch):
    redis = _Redis()
    executor = _Executor()
    service = _service(executor, monkeypatch, redis)
    user = SimpleNamespace(id=uuid.uuid4())
    problem_id = uuid.uuid4()

    first = await service.run_query(user, problem_id, "SELECT 1")
    second = await service.run_query(user, problem_id, "SELECT 1")
    assert first.status == "ok" and second.status == "ok"
    assert executor.calls == 2
    key = f"sql:concurrent:{user.id}"
    assert redis.store[key] == 0

    with pytest.raises(AppException) as quota:
        await service.run_query(user, problem_id, "SELECT 1")
    assert quota.value.status_code == 429
    assert executor.calls == 2
    assert redis.store[key] == 0

    capped = SimpleNamespace(id=uuid.uuid4())
    capped_key = f"sql:concurrent:{capped.id}"
    redis.store[capped_key] = 1
    with pytest.raises(AppException) as held:
        await service.run_query(capped, problem_id, "SELECT 1")
    assert held.value.status_code == 429
    assert redis.store[capped_key] == 1

    failing = _Executor(fail=True)
    failing_service = _service(failing, monkeypatch, redis)
    boom = SimpleNamespace(id=uuid.uuid4())
    with pytest.raises(RuntimeError, match="executor body failed"):
        await failing_service.run_query(boom, problem_id, "SELECT 1")
    assert redis.store[f"sql:concurrent:{boom.id}"] == 0


@pytest.mark.asyncio
async def test_sql_submit_quota_is_separate_from_run(monkeypatch):
    redis = _Redis()
    executor = _Executor()
    service = _service(executor, monkeypatch, redis)
    user = SimpleNamespace(id=uuid.uuid4())
    problem_id = uuid.uuid4()
    service.repo.save_submission = AsyncMock()
    service.repo.upsert_progress = AsyncMock()
    service.db.commit = AsyncMock()

    # Compare path needs expected results; a timeout/error result is enough to prove the slot.
    executor.execute = AsyncMock(
        return_value=SqlRunResult(error="forced", row_count=0)
    )
    await service.submit_query(user, problem_id, "SELECT 1")
    with pytest.raises(AppException) as quota:
        await service.submit_query(user, problem_id, "SELECT 1")
    assert quota.value.status_code == 429
    assert f"sql:rate:run:{user.id}" not in redis.store
    assert redis.store[f"sql:rate:submit:{user.id}"] == 2
    assert redis.store[f"sql:concurrent:{user.id}"] == 0
