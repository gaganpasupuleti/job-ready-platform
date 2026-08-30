# SQL Practice Engine (Build 4 / 4.1)

## Overview

The SQL Practice module is a dedicated domain separate from MCQ practice and Judge0 coding execution.

See `docs/PRACTICE_WORKSPACES.md` for the student SQL workspace (navigator, Run vs Submit, stuck Running... prevention, solution tab).

## Three security boundaries

```
┌─────────────────────────┐
│ 1. Application DB       │  jobready_db
│    Auth, problems meta, │  Never executes student SQL
│    submissions, progress│
└───────────┬─────────────┘
            │ metadata only
            ▼
┌─────────────────────────┐
│ 2. SQL Sandbox Admin    │  jobready_sql_admin @ jobready_sql_sandbox
│    CREATE SCHEMA        │  Seed tables / GRANT SELECT
│    DROP SCHEMA CASCADE  │  Never runs student SQL
└───────────┬─────────────┘
            │ grants read access
            ▼
┌─────────────────────────┐
│ 3. SQL Sandbox Runner   │  jobready_sql_runner @ jobready_sql_sandbox
│    READ ONLY SELECT     │  No CREATE/INSERT/UPDATE/DELETE
│    statement_timeout    │  search_path = challenge schema only
└─────────────────────────┘
```

## Execution flow (Build 4.1)

```
Student Query
    ↓
AST Validation (sqlglot / PostgreSQL dialect)
    ↓
Sandbox Admin: CREATE SCHEMA sql_p_<hex> + seed + GRANT SELECT
    ↓
Sandbox Runner: SET search_path + statement_timeout + BEGIN READ ONLY
    ↓
Execute SELECT / WITH … SELECT
    ↓
Timeout / row limits / result
    ↓
Sandbox Admin: DROP SCHEMA CASCADE (always, via finally)
```

## AST validation

`app/services/sql_execution/safety.py` uses **sqlglot** to parse PostgreSQL SQL into an AST.

Allowed:

- Single `SELECT`
- Read-only `WITH` (CTE) trees whose leaves are also `SELECT`
- Joins, aggregates, subqueries, windows, CASE, string/date functions

Rejected (including inside CTEs):

- INSERT / UPDATE / DELETE / MERGE / DROP / ALTER / CREATE / TRUNCATE
- COPY / GRANT / REVOKE / CALL / DO / SET
- Multiple statements
- Schema-qualified tables (`pg_catalog.*`, `other.schema`, etc.)
- Reconnaissance tables (`pg_roles`, `pg_user`, `pg_authid`, …)
- Dangerous functions (`pg_read_file`, `current_setting`, `dblink`, …)
- Modifying CTEs such as `WITH t AS (DELETE … RETURNING *) SELECT …`

Parsing is the **first** layer. Database permissions and read-only transactions are the **final** layer.

## Environment

```
# Application
DATABASE_URL=postgresql+asyncpg://jobready:…@localhost:5432/jobready_db

# Sandbox admin (schema lifecycle only)
SQL_SANDBOX_ADMIN_DATABASE_URL=postgresql+asyncpg://jobready_sql_admin:jobready_sql_admin_dev@localhost:5433/jobready_sql_sandbox

# Sandbox runner (student queries only)
SQL_SANDBOX_RUNNER_DATABASE_URL=postgresql+asyncpg://jobready_sql_runner:jobready_sql_dev@localhost:5433/jobready_sql_sandbox
SQL_SANDBOX_DATABASE_URL=…  # alias for runner (backward compatible)

SQL_SANDBOX_RUNNER_ROLE=jobready_sql_runner
SQL_SANDBOX_RUNNER_PASSWORD=jobready_sql_dev
SQL_EXECUTION_ENABLED=true
SQL_QUERY_TIMEOUT_MS=3000
SQL_MAX_ROWS=500
SQL_SUBMIT_MAX_ROWS=10000
```

Docker Compose service `postgres_sql_sandbox` (host port **5433**) initializes both roles via `infra/docker/init-sql-sandbox.sh`.

On **Railway** (managed Postgres, no init script): the backend bootstraps `jobready_sql_runner` at startup (`ensure_sandbox_roles`). When admin and runner URLs share the same credentials, the runner DSN is derived from `SQL_SANDBOX_ADMIN_DATABASE_URL` + `SQL_SANDBOX_RUNNER_ROLE` + `SQL_SANDBOX_RUNNER_PASSWORD`.

**Note:** If the sandbox volume was created before Build 4.1, recreate it so the init script runs:

```bash
docker compose -f infra/docker-compose.yml down
docker volume rm <project>_postgres_sql_sandbox_data
docker compose -f infra/docker-compose.yml up -d postgres postgres_sql_sandbox redis
```

## Row limits

| Mode | Behavior |
|------|----------|
| **Run** | Outer `LIMIT SQL_MAX_ROWS+1` for display truncation (`truncated: true`) |
| **Submit** | Evaluates up to `SQL_SUBMIT_MAX_ROWS` without truncating for comparison; exceeding fails safely |

Limits are applied via a wrapping subquery so student SQL text is not rewritten with an injected LIMIT that could change meaning for ordered partial results used in grading. Submit uses a high ceiling intended to cover challenge datasets.

## Timeouts & cleanup

- `SET statement_timeout` on the **runner** session (database-enforced)
- Ephemeral schema dropped in `finally` after success, SQL error, timeout, or unexpected exception
- Cleanup failures are logged; schema names are never returned to the client

## Error sanitization

Student-visible errors may include useful SQL messages (unknown column, syntax). Stripped:

- hosts / ports
- database names
- usernames / passwords
- internal schema ids (`sql_p_<hex>`)
- filesystem paths

## Live permission tests

```bash
set SQL_SANDBOX_LIVE_TESTS=1
pytest tests/test_sql_practice.py -k live_runner
```

## Student routes / APIs

Unchanged from Build 4 — see README. Prefix: `/api/v1/sql`.
