"""Isolated SQL sandbox executor — admin manages schemas; runner executes student SQL."""

from __future__ import annotations

import logging
import re
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

import asyncpg

from app.core.config import settings
from app.services.sql_execution.pools import get_admin_pool, get_runner_pool
from app.services.sql_execution.safety import validate_sql_query

logger = logging.getLogger(__name__)


@dataclass
class SqlRunResult:
    columns: list[str] = field(default_factory=list)
    rows: list[list[Any]] = field(default_factory=list)
    row_count: int = 0
    execution_time_ms: float = 0.0
    truncated: bool = False
    error: str | None = None
    timed_out: bool = False
    disabled: bool = False


def sanitize_sql_error(message: str) -> str:
    """Strip hosts, DB names, schemas, credentials, and paths from errors."""
    text = message
    text = re.sub(r"jobready[^\s]*", "[db]", text, flags=re.IGNORECASE)
    text = re.sub(r"sql_p_[a-f0-9]+", "[challenge]", text, flags=re.IGNORECASE)
    text = re.sub(r"localhost(:\d+)?", "[host]", text, flags=re.IGNORECASE)
    text = re.sub(r"\d{1,3}(\.\d{1,3}){3}(:\d+)?", "[host]", text)
    text = re.sub(r"password[=:]\S+", "password=[redacted]", text, flags=re.IGNORECASE)
    text = re.sub(r"[A-Za-z]:\\[^\s]+", "[path]", text)
    text = re.sub(r"(/[^\s]+)+", lambda m: "[path]" if len(m.group(0)) > 3 else m.group(0), text)
    line_match = re.search(r"LINE\s+(\d+)", text, flags=re.IGNORECASE)
    line_hint = f" (Line: {line_match.group(1)})" if line_match else ""
    first = text.strip().splitlines()[0] if text.strip() else "SQL error"
    return f"{first}{line_hint}"


def _quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _pg_type(data_type: str) -> str:
    mapping = {
        "integer": "INTEGER",
        "int": "INTEGER",
        "bigint": "BIGINT",
        "smallint": "SMALLINT",
        "numeric": "NUMERIC",
        "decimal": "NUMERIC",
        "float": "DOUBLE PRECISION",
        "double": "DOUBLE PRECISION",
        "real": "REAL",
        "boolean": "BOOLEAN",
        "bool": "BOOLEAN",
        "text": "TEXT",
        "varchar": "VARCHAR",
        "string": "TEXT",
        "date": "DATE",
        "timestamp": "TIMESTAMP",
        "timestamptz": "TIMESTAMPTZ",
        "json": "JSONB",
        "jsonb": "JSONB",
    }
    key = data_type.strip().lower()
    if key.startswith("varchar"):
        return data_type.upper()
    return mapping.get(key, "TEXT")


def _coerce_seed_value(value: Any, data_type: str) -> Any:
    if value is None or not isinstance(value, str):
        return value
    key = data_type.strip().lower()
    if key == "date":
        from datetime import date

        return date.fromisoformat(value[:10])
    if key in {"timestamp", "timestamptz"}:
        from datetime import datetime

        return datetime.fromisoformat(value)
    return value


def _serialize(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "isoformat"):
        return value.isoformat()
    from decimal import Decimal

    if isinstance(value, Decimal):
        return float(value) if value == value.to_integral_value() else str(value)
    if isinstance(value, uuid.UUID):
        return str(value)
    return str(value)


class SqlSandboxManager:
    """Admin-only: create/seed/drop ephemeral challenge schemas. Never runs student SQL."""

    async def provision(
        self, schema: str, tables: list[dict[str, Any]]
    ) -> None:
        pool = await get_admin_pool()
        async with pool.acquire() as conn:
            await conn.execute(f"CREATE SCHEMA {_quote_ident(schema)}")
            await conn.execute(f"SET search_path TO {_quote_ident(schema)}")
            for table in tables:
                await self._create_and_seed(conn, table)
            # Grant runner read-only access to this schema only
            runner_role = settings.sql_sandbox_runner_role
            await conn.execute(
                f"GRANT USAGE ON SCHEMA {_quote_ident(schema)} TO {_quote_ident(runner_role)}"
            )
            await conn.execute(
                f"GRANT SELECT ON ALL TABLES IN SCHEMA {_quote_ident(schema)} "
                f"TO {_quote_ident(runner_role)}"
            )

    async def cleanup(self, schema: str) -> None:
        try:
            pool = await get_admin_pool()
            async with pool.acquire() as conn:
                await conn.execute(
                    f"DROP SCHEMA IF EXISTS {_quote_ident(schema)} CASCADE"
                )
        except Exception:
            logger.exception("Failed to clean up SQL sandbox schema")

    async def _create_and_seed(self, conn: asyncpg.Connection, table: dict[str, Any]) -> None:
        name = table["table_name"]
        columns = table["columns"]
        col_types = {c["column_name"]: c["data_type"] for c in columns}
        col_defs = []
        for col in columns:
            nullable = "" if col.get("is_nullable", True) else " NOT NULL"
            col_defs.append(
                f"{_quote_ident(col['column_name'])} {_pg_type(col['data_type'])}{nullable}"
            )
        await conn.execute(f"CREATE TABLE {_quote_ident(name)} ({', '.join(col_defs)})")

        for row in table.get("rows", []):
            if not isinstance(row, dict):
                continue
            keys = list(row.keys())
            if not keys:
                continue
            placeholders = ", ".join(f"${i + 1}" for i in range(len(keys)))
            col_list = ", ".join(_quote_ident(k) for k in keys)
            values = [_coerce_seed_value(row[k], col_types.get(k, "TEXT")) for k in keys]
            await conn.execute(
                f"INSERT INTO {_quote_ident(name)} ({col_list}) VALUES ({placeholders})",
                *values,
            )


class SqlSandboxExecutor:
    """Orchestrates admin provisioning + runner read-only student query execution."""

    def __init__(self) -> None:
        self.enabled = settings.sql_execution_enabled
        self.timeout_ms = settings.sql_query_timeout_ms
        self.max_rows = settings.sql_max_rows
        self.submit_max_rows = settings.sql_submit_max_rows
        self.manager = SqlSandboxManager()

    def is_available(self) -> bool:
        return self.enabled

    async def execute(
        self,
        query: str,
        tables: list[dict[str, Any]],
        *,
        max_rows: int | None = None,
        for_submit: bool = False,
    ) -> SqlRunResult:
        if not self.enabled:
            return SqlRunResult(disabled=True, error="SQL execution is currently unavailable.")

        safety_error = validate_sql_query(query, max_length=settings.sql_max_query_length)
        if safety_error:
            return SqlRunResult(error=safety_error)

        # Run: display cap. Submit: higher safety ceiling without truncating comparison.
        if max_rows is not None:
            row_limit = max_rows
        elif for_submit:
            row_limit = self.submit_max_rows
        else:
            row_limit = self.max_rows

        schema = f"sql_p_{uuid.uuid4().hex[:16]}"
        started = time.perf_counter()
        provisioned = False

        try:
            await self.manager.provision(schema, tables)
            provisioned = True
        except Exception:
            logger.exception("SQL sandbox provision failed")
            await self.manager.cleanup(schema)
            return SqlRunResult(
                error="SQL sandbox is unavailable. Please try again later.",
                disabled=True,
            )

        try:
            return await self._run_as_runner(
                schema=schema,
                query=query,
                row_limit=row_limit,
                for_submit=for_submit,
                started=started,
            )
        finally:
            if provisioned:
                await self.manager.cleanup(schema)

    async def _run_as_runner(
        self,
        *,
        schema: str,
        query: str,
        row_limit: int,
        for_submit: bool,
        started: float,
    ) -> SqlRunResult:
        try:
            pool = await get_runner_pool()
        except Exception:
            logger.exception("SQL sandbox runner pool unavailable")
            return SqlRunResult(
                error="SQL sandbox is unavailable. Please try again later.",
                disabled=True,
            )

        try:
            async with pool.acquire() as conn:
                # Tight session controls — student SQL never uses admin connection
                await conn.execute(f"SET search_path TO {_quote_ident(schema)}")
                await conn.execute(f"SET statement_timeout = {int(self.timeout_ms)}")
                await conn.execute("SET default_transaction_read_only = on")

                async with conn.transaction(readonly=True):
                    # Outer LIMIT only for display truncation on Run.
                    # Submit fetches up to submit_max_rows; exceeding fails safely.
                    fetch_limit = row_limit + (0 if for_submit else 1)
                    wrapped = (
                        f"SELECT * FROM ({query.rstrip().rstrip(';')}) AS _q "
                        f"LIMIT {int(fetch_limit)}"
                    )
                    records = await conn.fetch(wrapped)

                elapsed = (time.perf_counter() - started) * 1000

                if for_submit and len(records) > row_limit:
                    return SqlRunResult(
                        error="Query result exceeds the maximum allowed row count.",
                        execution_time_ms=round(elapsed, 2),
                    )

                truncated = (not for_submit) and len(records) > row_limit
                if not for_submit:
                    records = records[:row_limit]

                columns = list(records[0].keys()) if records else []
                rows = [[_serialize(v) for v in list(r.values())] for r in records]
                return SqlRunResult(
                    columns=columns,
                    rows=rows,
                    row_count=len(rows),
                    execution_time_ms=round(elapsed, 2),
                    truncated=truncated,
                )
        except asyncpg.exceptions.QueryCanceledError:
            return SqlRunResult(
                error="Query timed out.",
                timed_out=True,
                execution_time_ms=(time.perf_counter() - started) * 1000,
            )
        except asyncpg.exceptions.InsufficientPrivilegeError:
            return SqlRunResult(
                error="Permission denied for this operation.",
                execution_time_ms=(time.perf_counter() - started) * 1000,
            )
        except asyncpg.PostgresError as exc:
            return SqlRunResult(
                error=sanitize_sql_error(str(exc)),
                execution_time_ms=(time.perf_counter() - started) * 1000,
            )
        except Exception as exc:
            logger.exception("Unexpected SQL runner error")
            return SqlRunResult(
                error=sanitize_sql_error(str(exc)),
                execution_time_ms=(time.perf_counter() - started) * 1000,
            )


class MockSqlSandboxExecutor:
    """Deterministic executor for unit tests (no real sandbox DB required)."""

    def __init__(self, results: dict[str, SqlRunResult] | None = None) -> None:
        self._results = results or {}
        self.enabled = True

    def is_available(self) -> bool:
        return True

    async def execute(
        self,
        query: str,
        tables: list[dict[str, Any]],
        *,
        max_rows: int | None = None,
        for_submit: bool = False,
    ) -> SqlRunResult:
        err = validate_sql_query(query)
        if err:
            return SqlRunResult(error=err)

        key = query.strip()
        if key in self._results:
            return self._results[key]

        if tables and tables[0].get("rows"):
            cols = [c["column_name"] for c in tables[0]["columns"]]
            rows = [[r.get(c) for c in cols] for r in tables[0]["rows"][: max_rows or 500]]
            return SqlRunResult(columns=cols, rows=rows, row_count=len(rows), execution_time_ms=1.0)

        return SqlRunResult(columns=[], rows=[], row_count=0, execution_time_ms=1.0)


_executor: SqlSandboxExecutor | None = None


def get_sql_executor() -> SqlSandboxExecutor:
    global _executor
    if _executor is None:
        _executor = SqlSandboxExecutor()
    return _executor
