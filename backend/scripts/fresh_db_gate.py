"""Create fresh DB, migrate, seed, and verify backfill idempotency."""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys

import asyncpg

FRESH_DB = "jobready_fresh_b10"
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _default_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://jobready:jobready_dev@localhost:5432/jobready_db",
    )


async def reset_public_schema() -> None:
    dsn = _default_url().replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(dsn)
    await conn.execute("DROP SCHEMA IF EXISTS public CASCADE")
    await conn.execute("CREATE SCHEMA public")
    await conn.execute("GRANT ALL ON SCHEMA public TO jobready")
    await conn.execute("GRANT ALL ON SCHEMA public TO public")
    await conn.close()
    print("reset public schema on", dsn.split("@")[-1])


async def recreate_db() -> str | None:
    admin = "postgresql://jobready:jobready_dev@localhost:5432/postgres"
    try:
        conn = await asyncpg.connect(admin)
        try:
            await conn.fetch(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = $1 AND pid <> pg_backend_pid()",
                FRESH_DB,
            )
        except Exception:
            pass
        await conn.execute(f'DROP DATABASE IF EXISTS "{FRESH_DB}"')
        await conn.execute(f'CREATE DATABASE "{FRESH_DB}"')
        await conn.close()
        return f"postgresql+asyncpg://jobready:jobready_dev@localhost:5432/{FRESH_DB}"
    except asyncpg.exceptions.InsufficientPrivilegeError:
        print("Cannot CREATE DATABASE — resetting public schema instead")
        await reset_public_schema()
        return None


def run(cmd: list[str], env: dict[str, str]) -> None:
    print("$", " ".join(cmd))
    subprocess.run(cmd, cwd=BASE, env=env, check=True)


async def main() -> None:
    env = os.environ.copy()
    env["E2E_ALLOW_SEED"] = "1"
    fresh_url = await recreate_db()
    if fresh_url:
        env["DATABASE_URL"] = fresh_url
    py = sys.executable
    run([py, "-m", "alembic", "upgrade", "head"], env)
    run([py, "-m", "app.seed.runner"], env)
    run([py, "-m", "app.seed.e2e_users", "../frontend/e2e/fixtures/manifest.json"], env)
    run([py, "-m", "app.readiness.backfill"], env)
    run([py, "-m", "app.readiness.backfill"], env)
    print("fresh_db_gate_ok")


if __name__ == "__main__":
    asyncio.run(main())
