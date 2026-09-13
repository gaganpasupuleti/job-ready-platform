"""Ensure SQL sandbox admin/runner role split exists (local Docker + Railway).

Admin connects with elevated privileges and creates/updates the non-superuser
runner role. Student queries always use the runner DSN (see pools.runner_dsn).
"""

from __future__ import annotations

import logging
from urllib.parse import urlparse

import asyncpg

from app.core.config import settings
from app.services.sql_execution.pools import admin_dsn, to_asyncpg_dsn

logger = logging.getLogger(__name__)


def _quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _quote_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


async def ensure_sandbox_roles() -> None:
    """Idempotently create/update the restricted runner role on the sandbox DB."""
    if not settings.sql_execution_enabled:
        logger.info("SQL execution disabled — skipping sandbox role bootstrap")
        return

    role = settings.sql_sandbox_runner_role
    password = settings.sql_sandbox_runner_password
    if not role or not password:
        logger.warning("SQL sandbox runner role/password unset — skipping role bootstrap")
        return

    dsn = admin_dsn()
    try:
        conn = await asyncpg.connect(dsn)
    except Exception:
        logger.exception("SQL sandbox admin unreachable — role bootstrap skipped")
        return

    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_roles WHERE rolname = $1",
            role,
        )
        # PASSWORD cannot use asyncpg bind params ($1) — use quoted literals.
        role_sql = _quote_ident(role)
        pwd_sql = _quote_literal(password)
        if exists:
            await conn.execute(
                f"ALTER ROLE {role_sql} WITH LOGIN PASSWORD {pwd_sql} "
                "NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT"
            )
            logger.info("SQL sandbox runner role updated: %s", role)
        else:
            await conn.execute(
                f"CREATE ROLE {role_sql} LOGIN PASSWORD {pwd_sql} "
                "NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT"
            )
            logger.info("SQL sandbox runner role created: %s", role)

        db_name = await conn.fetchval("SELECT current_database()")
        await conn.execute(
            f"GRANT CONNECT ON DATABASE {_quote_ident(db_name)} TO {role_sql}"
        )

        # Public schema: usage only, no CREATE
        await conn.execute("REVOKE CREATE ON SCHEMA public FROM PUBLIC")
        await conn.execute(f"REVOKE CREATE ON SCHEMA public FROM {role_sql}")
        await conn.execute(f"GRANT USAGE ON SCHEMA public TO {role_sql}")

        # No schema creation on this database
        await conn.execute(
            f"REVOKE CREATE ON DATABASE {_quote_ident(db_name)} FROM PUBLIC"
        )
        await conn.execute(
            f"REVOKE CREATE ON DATABASE {_quote_ident(db_name)} FROM {role_sql}"
        )
        timeout_ms = max(1, int(settings.sql_query_timeout_ms))
        await conn.execute(
            f"ALTER ROLE {role_sql} SET statement_timeout = {_quote_literal(str(timeout_ms))}"
        )
    except Exception:
        logger.exception("SQL sandbox role bootstrap failed")
        raise
    finally:
        await conn.close()


def _database_name(url: str) -> str:
    return urlparse(to_asyncpg_dsn(url)).path.lstrip("/").split("?")[0]


async def restrict_runner_from_app_database() -> None:
    """Deny the sandbox runner CONNECT on the application database.

    Native Postgres hosts both databases in one cluster, so a role created
    for the sandbox can otherwise inherit PUBLIC CONNECT on jobready_db.
    Docker-isolated sandboxes do not contain the app database; this is a
    no-op when the two DSNs name the same database.
    """
    if not settings.sql_execution_enabled:
        return
    role = settings.sql_sandbox_runner_role
    if not role:
        return
    app_db = _database_name(settings.database_url)
    sandbox_db = _database_name(admin_dsn())
    if not app_db or app_db == sandbox_db:
        logger.info("App and sandbox databases are not distinct; skip CONNECT revoke")
        return

    try:
        conn = await asyncpg.connect(to_asyncpg_dsn(settings.database_url))
    except Exception:
        logger.exception("App database unreachable — cannot restrict runner CONNECT")
        return

    role_sql = _quote_ident(role)
    db_sql = _quote_ident(app_db)
    try:
        await conn.execute(f"REVOKE CONNECT ON DATABASE {db_sql} FROM PUBLIC")
        await conn.execute(f"REVOKE CONNECT ON DATABASE {db_sql} FROM {role_sql}")
        owner = await conn.fetchval("SELECT current_user")
        if owner:
            await conn.execute(
                f"GRANT CONNECT ON DATABASE {db_sql} TO {_quote_ident(str(owner))}"
            )
        logger.info("Revoked sandbox runner CONNECT on application database %s", app_db)
    except Exception:
        logger.exception("Failed to revoke runner CONNECT on %s", app_db)
        raise
    finally:
        await conn.close()


async def _run() -> None:
    await ensure_sandbox_roles()


def run() -> None:
    import asyncio

    asyncio.run(_run())


if __name__ == "__main__":
    run()
