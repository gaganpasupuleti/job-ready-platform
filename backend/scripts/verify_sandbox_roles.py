"""One-off: verify sandbox runner role on Railway (railway run)."""
import asyncio
import os
from urllib.parse import quote, urlparse, urlunparse

import asyncpg


def to_pg(url: str) -> str:
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    return url


def with_user(url: str, user: str, password: str) -> str:
    p = urlparse(to_pg(url))
    host = p.hostname or "localhost"
    port = f":{p.port}" if p.port else ""
    auth = f"{quote(user, safe='')}:{quote(password, safe='')}"
    return urlunparse(("postgresql", f"{auth}@{host}{port}", p.path, "", p.query, ""))


async def main() -> None:
    admin = to_pg(os.environ["SQL_SANDBOX_ADMIN_DATABASE_URL"])
    role = os.environ.get("SQL_SANDBOX_RUNNER_ROLE", "jobready_sql_runner")
    password = os.environ["SQL_SANDBOX_RUNNER_PASSWORD"]
    runner = with_user(admin, role, password)

    a = await asyncpg.connect(admin)
    try:
        exists = await a.fetchval("SELECT 1 FROM pg_roles WHERE rolname = $1", role)
        print("role_exists", bool(exists))
        can_create = await a.fetchval(
            "SELECT has_database_privilege($1, current_database(), 'CREATE')",
            role,
        )
        print("runner_db_create", can_create)
    finally:
        await a.close()

    r = await asyncpg.connect(runner)
    try:
        try:
            await r.execute("CREATE SCHEMA harden_probe")
            print("CREATE_SCHEMA ALLOWED_BAD")
        except Exception as exc:
            print("CREATE_SCHEMA denied_ok", type(exc).__name__)
        try:
            await r.execute("CREATE TABLE public.harden_probe_t (id int)")
            print("CREATE_TABLE ALLOWED_BAD")
        except Exception as exc:
            print("CREATE_TABLE denied_ok", type(exc).__name__)
        print("SELECT", await r.fetchval("SELECT 1"))
    finally:
        await r.close()


if __name__ == "__main__":
    asyncio.run(main())
