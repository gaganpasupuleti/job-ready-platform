"""Standalone SQL playground. Reuses the sandbox executor and writes no grades."""

from __future__ import annotations

from app.core.config import settings
from app.core.exceptions import AppException
from app.models.user import User
from app.services.code_execution.rate_limit import concurrency_slot, enforce_rate_limit
from app.services.sql_execution.executor import SqlSandboxExecutor
from app.services.sql_execution.safety import validate_sql_query
from app.services.sql_playground.catalog import dataset_payload, get_dataset, list_datasets

PLAYGROUND_NOTE = "This run is not graded and does not create a submission, completion credit, or readiness evidence."


class SqlPlaygroundService:
    def __init__(self, executor: SqlSandboxExecutor) -> None:
        self.executor = executor

    def catalog(self) -> dict:
        return {
            "language": "sql",
            "assessed": False,
            "row_limit": settings.sql_max_rows,
            "timeout_ms": settings.sql_query_timeout_ms,
            "note": PLAYGROUND_NOTE,
            "datasets": list_datasets(),
        }

    def dataset(self, dataset_id: str) -> dict:
        row = get_dataset(dataset_id)
        if row is None:
            raise AppException("Dataset not found", status_code=404)
        row["row_limit"] = settings.sql_max_rows
        row["timeout_ms"] = settings.sql_query_timeout_ms
        return row

    async def run(self, user: User, dataset_id: str, query: str) -> dict:
        tables = dataset_payload(dataset_id)
        if tables is None:
            raise AppException("Dataset not found", status_code=404)
        if not self.executor.is_available():
            raise AppException("SQL execution is currently unavailable.", status_code=503)

        await enforce_rate_limit(user.id, kind="run", namespace="sql")
        safety = validate_sql_query(query, max_length=settings.sql_max_query_length)
        if safety:
            return self._payload(error=safety, status="sql_error")

        async with concurrency_slot(user.id, namespace="sql"):
            result = await self.executor.execute(query, tables)
        if result.disabled:
            raise AppException(result.error or "SQL execution unavailable", status_code=503)
        if result.timed_out:
            return self._payload(
                error=result.error or "Query timed out.",
                status="timeout",
                execution_time_ms=result.execution_time_ms,
            )
        if result.error:
            return self._payload(
                error=result.error,
                status="sql_error",
                execution_time_ms=result.execution_time_ms,
            )
        return self._payload(
            columns=result.columns,
            rows=result.rows,
            row_count=result.row_count,
            execution_time_ms=result.execution_time_ms,
            truncated=result.truncated,
            status="ok",
        )

    def _payload(self, **fields) -> dict:
        payload = {
            "columns": [],
            "rows": [],
            "row_count": 0,
            "execution_time_ms": None,
            "truncated": False,
            "error": None,
            "status": "ok",
            "assessed": False,
            "row_limit": settings.sql_max_rows,
            "timeout_ms": settings.sql_query_timeout_ms,
            "note": PLAYGROUND_NOTE,
        }
        payload.update(fields)
        return payload
