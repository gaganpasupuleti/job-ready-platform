"""Rehearse alembic 020 -> 021/022 on a disposable local database."""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import asyncpg
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import settings


DISPOSABLE = "jobready_accept_021"


def _admin_url(database: str) -> str:
    parsed = urlparse(settings.database_url.replace("+asyncpg", ""))
    return urlunparse(parsed._replace(path=f"/{database}"))


async def _connect_admin(app_parsed) -> asyncpg.Connection:
    admin_parsed = urlparse(settings.sql_sandbox_admin_database_url.replace("+asyncpg", ""))
    candidates = (
        {
            "host": admin_parsed.hostname or app_parsed.hostname,
            "port": admin_parsed.port or app_parsed.port or 5432,
            "user": admin_parsed.username or "jobready_sql_admin",
            "password": admin_parsed.password,
            "database": "postgres",
        },
        {
            "host": app_parsed.hostname,
            "port": app_parsed.port or 5432,
            "user": app_parsed.username,
            "password": app_parsed.password,
            "database": "postgres",
        },
    )
    last_error: Exception | None = None
    for kwargs in candidates:
        if not kwargs["user"]:
            continue
        try:
            return await asyncpg.connect(**kwargs)
        except Exception as exc:  # noqa: BLE001 — try next admin candidate
            last_error = exc
    raise last_error or RuntimeError("No postgres admin connection available for rehearsal DB")


async def _ensure_db() -> None:
    app_url = settings.database_url.replace("+asyncpg", "")
    parsed = urlparse(app_url)
    conn = await _connect_admin(parsed)
    try:
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname=$1", DISPOSABLE)
        if exists:
            await conn.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                f"WHERE datname = '{DISPOSABLE}' AND pid <> pg_backend_pid()"
            )
            await conn.execute(f'DROP DATABASE "{DISPOSABLE}"')
        owner = parsed.username or "jobready"
        await conn.execute(f'CREATE DATABASE "{DISPOSABLE}" OWNER "{owner}"')
    finally:
        await conn.close()


async def _seed_min() -> None:
    url = settings.database_url
    parsed = urlparse(url.replace("+asyncpg", ""))
    disposable = urlunparse(parsed._replace(path=f"/{DISPOSABLE}")).replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(disposable)
    async with engine.begin() as conn:
        # Reach 020 only first via alembic; this helper just verifies connectivity.
        await conn.execute(text("SELECT 1"))
    await engine.dispose()


def _alembic(database_url: str, *args: str) -> None:
    env = os.environ.copy()
    env["DATABASE_URL"] = database_url
    subprocess.check_call([sys.executable, "-m", "alembic", *args], cwd=str(ROOT), env=env)


async def main() -> None:
    await _ensure_db()
    parsed = urlparse(settings.database_url.replace("+asyncpg", ""))
    sync_url = urlunparse(parsed._replace(path=f"/{DISPOSABLE}"))
    async_url = sync_url.replace("postgresql://", "postgresql+asyncpg://")

    # Upgrade only through 020 first.
    _alembic(async_url, "upgrade", "020_content_version_history")

    # Create a stub row that must survive 021/022.
    conn = await asyncpg.connect(dsn=sync_url)
    try:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS _accept_probe (
              id serial primary key,
              note text not null
            )
            """
        )
        await conn.execute("INSERT INTO _accept_probe(note) VALUES ('before-021')")
        # Minimal assignments table may already exist from migrations; if so, leave it.
        has_assignments = await conn.fetchval(
            "SELECT to_regclass('public.assignments') IS NOT NULL"
        )
        print("at_020_assignments", bool(has_assignments))
        probe = await conn.fetchval("SELECT note FROM _accept_probe ORDER BY id DESC LIMIT 1")
        print("probe_before", probe)
    finally:
        await conn.close()

    _alembic(async_url, "upgrade", "head")

    conn = await asyncpg.connect(dsn=sync_url)
    try:
        probe = await conn.fetchval("SELECT note FROM _accept_probe ORDER BY id DESC LIMIT 1")
        has_runtime = await conn.fetchval(
            """
            SELECT EXISTS (
              SELECT 1 FROM information_schema.columns
              WHERE table_name='assignments' AND column_name='requires_runtime'
            )
            """
        )
        has_syllabus = await conn.fetchval("SELECT to_regclass('public.learning_syllabus_entries') IS NOT NULL")
        version = await conn.fetchval("SELECT version_num FROM alembic_version")
        print("probe_after", probe)
        print("requires_runtime_column", has_runtime)
        print("syllabus_table", has_syllabus)
        print("alembic_version", version)
        assert probe == "before-021"
        assert has_runtime
        assert has_syllabus
        assert version == "022_python_runtime_backfill"
    finally:
        await conn.close()

    print("MIGRATION_REHEARSAL_OK")


if __name__ == "__main__":
    asyncio.run(main())
