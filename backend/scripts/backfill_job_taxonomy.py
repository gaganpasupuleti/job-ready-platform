"""Copy source taxonomy onto existing application jobs.

Read-only against the Jobs source. Refuses a non-local application database.
Does not change job ids, saves, applications, or publication decisions.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.services.jobs_source_reader import fetch_source_jobs
from app.services.jobs_source_sync import backfill_source_taxonomy


def _identity(database_url: str) -> tuple[str, int, str]:
    raw = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    raw = raw.replace("postgres://", "postgresql://", 1)
    parsed = urlparse(raw)
    database = (parsed.path or "").lstrip("/").split("?")[0]
    return ((parsed.hostname or "").lower(), parsed.port or 5432, database)


def _source_url() -> str:
    value = os.environ.get("JOBS_SOURCE_DATABASE_URL", "").strip()
    if not value:
        raise SystemExit("BACKFILL_REFUSED source is not configured")
    return value


async def main() -> int:
    target = os.environ.get("DATABASE_URL", "").strip()
    if not target:
        print("BACKFILL_REFUSED application database is not configured")
        return 2
    host, _port, database = _identity(target)
    if host not in {"localhost", "127.0.0.1"} or database in {"railway", "postgres"}:
        print("BACKFILL_REFUSED target is not a local application database")
        return 2
    source = _source_url()
    if _identity(source) == _identity(target):
        print("BACKFILL_REFUSED target is the Jobs source database")
        return 2
    try:
        rows = await fetch_source_jobs(source)
    except Exception as exc:
        print("FETCH_FAILED", type(exc).__name__)
        return 1
    if not rows:
        print("NO_WRITES empty source snapshot")
        return 1
    engine = create_async_engine(target, echo=False, hide_parameters=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_factory() as db:
            updated = await backfill_source_taxonomy(db, rows)
    except Exception as exc:
        print("BACKFILL_FAILED", type(exc).__name__)
        return 1
    finally:
        await engine.dispose()
    print("SEEN", len(rows))
    print("UPDATED", updated)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))
    except SystemExit:
        raise
    except Exception:
        print("FAILED unexpected error")
        raise SystemExit(1) from None
