"""Build 4.1 — AST safety, bypass attempts, and optional live permission tests."""

import os
import uuid

import pytest

from app.main import app
from app.services.sql_execution.compare import compare_results
from app.services.sql_execution.executor import MockSqlSandboxExecutor, SqlRunResult, get_sql_executor
from app.services.sql_execution.safety import validate_sql_query


def _headers(auth_fixture):
    headers, *_ = auth_fixture
    return headers


@pytest.fixture(autouse=True)
def mock_sql_executor():
    mock = MockSqlSandboxExecutor()
    app.dependency_overrides[get_sql_executor] = lambda: mock
    yield mock
    app.dependency_overrides.pop(get_sql_executor, None)


# --- Allowed AST cases ---


@pytest.mark.parametrize(
    "query",
    [
        "SELECT 1",
        "SELECT id, name FROM customers WHERE city = 'Pune'",
        "SELECT c.id FROM customers c JOIN orders o ON c.id = o.customer_id",
        "SELECT department, COUNT(*) FROM employees GROUP BY department HAVING COUNT(*) > 1",
        "SELECT * FROM customers WHERE id IN (SELECT customer_id FROM orders)",
        "WITH cte AS (SELECT 1 AS x) SELECT * FROM cte",
        "WITH a AS (SELECT 1 AS x), b AS (SELECT * FROM a) SELECT * FROM b",
        "SELECT id, ROW_NUMBER() OVER (ORDER BY id) AS rn FROM customers",
        "SELECT CASE WHEN amount > 100 THEN 'high' ELSE 'low' END FROM orders",
        "SELECT LOWER(name), UPPER(city), TRIM(name) FROM customers",
        "SELECT DATE_TRUNC('month', order_date), SUM(amount) FROM orders GROUP BY 1",
        "SeLeCt * FrOm customers",
        "/* DROP TABLE customers; */ SELECT 1",
        "SELECT 1 -- DROP TABLE customers",
    ],
)
def test_allowed_read_only_queries(query):
    assert validate_sql_query(query) is None


# --- Rejected bypass / mutation cases ---


@pytest.mark.parametrize(
    "query",
    [
        "INSERT INTO customers VALUES (1)",
        "UPDATE customers SET city='x'",
        "DELETE FROM customers",
        "MERGE INTO customers t USING customers s ON t.id=s.id WHEN MATCHED THEN UPDATE SET city=s.city",
        "DROP TABLE customers",
        "ALTER TABLE customers ADD COLUMN x INT",
        "CREATE TABLE foo (id INT)",
        "TRUNCATE customers",
        "COPY customers TO STDOUT",
        "CALL foo()",
        "DO $$ BEGIN NULL; END $$",
        "GRANT SELECT ON customers TO public",
        "REVOKE ALL ON customers FROM public",
        "SELECT 1; SELECT 2",
        "SELECT 1; DROP TABLE customers",
        "WITH removed AS (DELETE FROM customers RETURNING *) SELECT * FROM removed",
        "WITH added AS (INSERT INTO customers VALUES (99) RETURNING *) SELECT * FROM added",
        "WITH updated AS (UPDATE customers SET city='x' RETURNING *) SELECT * FROM updated",
        "WITH t AS (DELETE FROM customers RETURNING *) SELECT * FROM t",
        "SELECT * FROM pg_roles",
        "SELECT * FROM pg_user",
        "SELECT * FROM pg_authid",
        "SELECT * FROM pg_catalog.pg_tables",
        "SELECT * FROM information_schema.tables",
        "SELECT * FROM other_schema.customers",
        "SELECT * FROM sql_p_abc123.customers",
        "SET search_path TO public",
        "SET ROLE postgres",
        "SET SESSION AUTHORIZATION postgres",
        "SELECT pg_read_file('/etc/passwd')",
        "SELECT current_setting('data_directory')",
        "iNsErT InTo customers VALUES (1)",
        "With x As (DeLeTe From customers Returning *) Select * From x",
    ],
)
def test_dangerous_and_bypass_queries_rejected(query):
    assert validate_sql_query(query) is not None


def test_empty_and_oversized_rejected():
    assert validate_sql_query("") is not None
    assert validate_sql_query("   ") is not None
    assert validate_sql_query("SELECT 1", max_length=5) is not None


def test_sanitize_hides_schema_and_host():
    from app.services.sql_execution.executor import sanitize_sql_error

    msg = sanitize_sql_error(
        'relation "sql_p_abcdef0123456789.customers" does not exist on localhost:5433'
    )
    assert "sql_p_" not in msg
    assert "localhost" not in msg
    assert "[challenge]" in msg or "[host]" in msg


# --- Comparison (unchanged behavior) ---


def test_compare_order_insensitive_and_nulls():
    assert compare_results(
        expected_columns=["a"],
        expected_rows=[[2], [None]],
        actual_columns=["a"],
        actual_rows=[[None], [2]],
        order_sensitive=False,
    )["matched"]


# --- API smoke ---


async def _sql_problems_or_skip(client, headers):
    try:
        listed = await client.get("/api/v1/sql/problems", headers=headers)
    except Exception as exc:
        pytest.skip(f"SQL API unavailable: {exc}")
    if listed.status_code >= 500:
        pytest.skip("SQL schema not migrated (run alembic upgrade head)")
    if listed.status_code != 200:
        pytest.skip(f"SQL list failed: {listed.status_code}")
    if listed.json().get("total", 0) == 0:
        pytest.skip("No SQL problems seeded")
    return listed


@pytest.mark.asyncio
async def test_sql_list_requires_auth(client):
    assert (await client.get("/api/v1/sql/problems")).status_code == 401


@pytest.mark.asyncio
async def test_sql_execution_status(client, student_auth):
    response = await client.get("/api/v1/sql/execution-status", headers=_headers(student_auth))
    assert response.status_code == 200
    body = response.json()
    assert "available" in body
    assert body["status"] in {"available", "disabled", "sandbox_unavailable"}
    assert "password" not in str(body).lower()
    assert "postgresql://" not in str(body).lower()


@pytest.mark.asyncio
async def test_sql_run_blocks_drop_via_api(client, student_auth, mock_sql_executor):
    headers = _headers(student_auth)
    listed = await _sql_problems_or_skip(client, headers)
    problem_id = listed.json()["items"][0]["id"]
    blocked = await client.post(
        f"/api/v1/sql/problems/{problem_id}/run",
        headers=headers,
        json={"query": "DROP TABLE customers"},
    )
    assert blocked.status_code == 200
    assert blocked.json()["error"]


@pytest.mark.asyncio
async def test_sql_run_blocks_modifying_cte_via_api(client, student_auth):
    headers = _headers(student_auth)
    listed = await _sql_problems_or_skip(client, headers)
    problem_id = listed.json()["items"][0]["id"]
    blocked = await client.post(
        f"/api/v1/sql/problems/{problem_id}/run",
        headers=headers,
        json={
            "query": "WITH t AS (DELETE FROM customers RETURNING *) SELECT * FROM t",
        },
    )
    assert blocked.status_code == 200
    assert blocked.json()["error"]


@pytest.mark.asyncio
async def test_sql_list_and_detail(client, student_auth):
    headers = _headers(student_auth)
    listed = await _sql_problems_or_skip(client, headers)
    slug = listed.json()["items"][0]["slug"]
    detail = await client.get(f"/api/v1/sql/problems/{slug}", headers=headers)
    assert detail.status_code == 200
    assert "solution_query" not in detail.json()


@pytest.mark.asyncio
async def test_sql_run_and_submit_with_mock(client, student_auth, mock_sql_executor):
    headers = _headers(student_auth)
    listed = await _sql_problems_or_skip(client, headers)
    problem_id = listed.json()["items"][0]["id"]
    mock_sql_executor._results["SELECT 1 AS n"] = SqlRunResult(
        columns=["n"], rows=[[1]], row_count=1, execution_time_ms=2.0
    )
    run = await client.post(
        f"/api/v1/sql/problems/{problem_id}/run",
        headers=headers,
        json={"query": "SELECT 1 AS n"},
    )
    assert run.status_code == 200
    assert run.json()["columns"] == ["n"]


@pytest.mark.asyncio
async def test_sql_solution_locked_until_accepted(client, student_auth):
    headers = _headers(student_auth)
    listed = await _sql_problems_or_skip(client, headers)
    problem_id = listed.json()["items"][0]["id"]
    assert (
        await client.get(f"/api/v1/sql/problems/{problem_id}/solution", headers=headers)
    ).status_code == 403


@pytest.mark.asyncio
async def test_sql_bookmark(client, student_auth):
    headers = _headers(student_auth)
    listed = await _sql_problems_or_skip(client, headers)
    problem_id = listed.json()["items"][0]["id"]
    toggle = await client.post(f"/api/v1/sql/problems/{problem_id}/bookmark", headers=headers)
    assert toggle.status_code == 200
    assert toggle.json()["bookmarked"] is True


@pytest.mark.asyncio
async def test_sql_cross_user_submission_denied(client, student_auth):
    headers = _headers(student_auth)
    fake_id = str(uuid.uuid4())
    try:
        resp = await client.get(f"/api/v1/sql/submissions/{fake_id}", headers=headers)
    except Exception as exc:
        pytest.skip(f"SQL API unavailable: {exc}")
    if resp.status_code >= 500:
        pytest.skip("SQL schema not migrated")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_sql_admin_requires_admin(client, student_auth):
    assert (
        await client.get("/api/v1/admin/sql/problems", headers=_headers(student_auth))
    ).status_code == 403


@pytest.mark.asyncio
async def test_sql_progress(client, student_auth):
    try:
        response = await client.get("/api/v1/sql/progress", headers=_headers(student_auth))
    except Exception as exc:
        pytest.skip(f"SQL API unavailable: {exc}")
    if response.status_code >= 500:
        pytest.skip("SQL schema not migrated")
    assert response.status_code == 200
    assert "total_problems" in response.json()


def _sandbox_live_enabled() -> bool:
    return os.environ.get("SQL_SANDBOX_LIVE_TESTS", "").lower() in {"1", "true", "yes"}


@pytest.mark.asyncio
@pytest.mark.skipif(not _sandbox_live_enabled(), reason="Set SQL_SANDBOX_LIVE_TESTS=1 with Docker sandbox")
async def test_live_runner_permissions():
    """Prove runner cannot mutate; admin can provision; runner can SELECT."""
    import asyncpg

    from app.core.config import settings
    from app.services.sql_execution.executor import SqlSandboxExecutor
    from app.services.sql_execution.pools import admin_dsn, runner_dsn, to_asyncpg_dsn

    # Runner cannot create schema/table or write
    runner = await asyncpg.connect(runner_dsn())
    try:
        with pytest.raises(asyncpg.PostgresError):
            await runner.execute("CREATE SCHEMA live_perm_test")
        with pytest.raises(asyncpg.PostgresError):
            await runner.execute("CREATE TABLE public.live_perm_t (id INT)")
        with pytest.raises(asyncpg.PostgresError):
            await runner.execute("INSERT INTO pg_catalog.pg_type SELECT * FROM pg_catalog.pg_type LIMIT 0")
    finally:
        await runner.close()

    # Admin has no access to application DB host credentials (different DSN path)
    app_dsn = to_asyncpg_dsn(settings.database_url)
    assert "jobready_db" in app_dsn
    assert "jobready_sql_sandbox" in admin_dsn()
    assert admin_dsn() != app_dsn

    # End-to-end: executor SELECT works with dual roles
    executor = SqlSandboxExecutor()
    if not executor.is_available():
        pytest.skip("SQL execution disabled")
    tables = [
        {
            "table_name": "t",
            "columns": [{"column_name": "id", "data_type": "INTEGER", "is_nullable": False}],
            "rows": [{"id": 1}, {"id": 2}],
        }
    ]
    result = await executor.execute("SELECT id FROM t ORDER BY id", tables)
    assert result.error is None, result.error
    assert result.rows == [[1], [2]]

    # Modifying CTE rejected before DB
    bad = await executor.execute(
        "WITH x AS (DELETE FROM t RETURNING *) SELECT * FROM x", tables
    )
    assert bad.error is not None


def test_runner_dsn_derives_when_admin_credentials_shared(monkeypatch):
    """Railway: admin and runner URLs identical → derive restricted role DSN."""
    from app.core.config import settings
    from app.services.sql_execution.pools import runner_dsn, with_role_password

    shared = "postgresql://postgres:secret@sql.internal:5432/railway"
    monkeypatch.setattr(settings, "sql_sandbox_admin_database_url", shared)
    monkeypatch.setattr(settings, "sql_sandbox_runner_database_url", shared)
    monkeypatch.setattr(settings, "sql_sandbox_database_url", shared)
    monkeypatch.setattr(settings, "sql_sandbox_runner_role", "jobready_sql_runner")
    monkeypatch.setattr(settings, "sql_sandbox_runner_password", "runner-pass")

    dsn = runner_dsn()
    assert dsn == with_role_password(shared, "jobready_sql_runner", "runner-pass")
    assert "jobready_sql_runner" in dsn
    assert "runner-pass" in dsn
    assert "postgres:secret" not in dsn


def test_runner_dsn_keeps_explicit_local_url(monkeypatch):
    from app.core.config import settings
    from app.services.sql_execution.pools import runner_dsn, to_asyncpg_dsn

    admin = "postgresql://jobready_sql_admin:admin@localhost:5433/jobready_sql_sandbox"
    runner = "postgresql://jobready_sql_runner:dev@localhost:5433/jobready_sql_sandbox"
    monkeypatch.setattr(settings, "sql_sandbox_admin_database_url", admin)
    monkeypatch.setattr(settings, "sql_sandbox_runner_database_url", runner)
    monkeypatch.setattr(settings, "sql_sandbox_database_url", runner)

    assert runner_dsn() == to_asyncpg_dsn(runner)
