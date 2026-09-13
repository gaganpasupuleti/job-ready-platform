"""Dry-run the Jobs server catalog. Source access stays read-only.

Production apply is disabled. A local disposable apply requires an explicit
target database name and a localhost application URL. It never writes the source.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.models.job import Job
from app.services.jobs_source_reader import fetch_source_jobs, public_proxy_dsn
from app.services.jobs_source_sync import EXTERNAL_PREFIX, apply_plan, plan_sync

DISPOSABLE_DATABASE = "jobready_sync_disposable"


def _source_dsn() -> str:
    dedicated = os.environ.get("JOBS_SOURCE_DATABASE_URL", "").strip()
    if dedicated:
        return dedicated
    raw = os.environ.get("DATABASE_URL", "").strip()
    host = os.environ.get("JOBS_SOURCE_PUBLIC_HOST", "").strip()
    port = os.environ.get("JOBS_SOURCE_PUBLIC_PORT", "").strip()
    if raw and host and port:
        return public_proxy_dsn(raw, host, int(port))
    raise SystemExit("Jobs source DSN is not configured")


def describe_target(database_url: str) -> str:
    raw = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    parsed = urlparse(raw)
    database = (parsed.path or "").lstrip("/").split("?")[0]
    return f"host={parsed.hostname} port={parsed.port or 5432} database={database}"


def assert_disposable_local(database_url: str, expected_database: str) -> None:
    if os.environ.get("APP_ENV", "").strip().lower() == "production":
        raise SystemExit("APPLY_REFUSED production execution is disabled")
    raw = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    parsed = urlparse(raw)
    database = (parsed.path or "").lstrip("/").split("?")[0]
    if parsed.hostname not in {"localhost", "127.0.0.1"}:
        raise SystemExit("APPLY_REFUSED target host is not local")
    if database in {"railway", "postgres", "jobready_db"}:
        raise SystemExit("APPLY_REFUSED target is not a disposable database")
    if database != expected_database or expected_database != DISPOSABLE_DATABASE:
        raise SystemExit("APPLY_REFUSED target database was not explicitly confirmed")


async def _owned_existing(database_url: str) -> dict[str, object]:
    engine = create_async_engine(database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_factory() as db:
            rows = (
                await db.execute(
                    select(Job.id, Job.external_id).where(Job.external_id.startswith(EXTERNAL_PREFIX))
                )
            ).all()
            return {external_id: job_id for job_id, external_id in rows if external_id}
    finally:
        await engine.dispose()


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--apply-local-disposable", action="store_true")
    parser.add_argument("--target-database", default="")
    parser.add_argument("--target-url", default="")
    args = parser.parse_args()
    if args.apply and not args.apply_local_disposable:
        print("APPLY_REFUSED production and source writes are disabled")
        return 2
    try:
        rows = await fetch_source_jobs(_source_dsn())
    except Exception as exc:
        print("FETCH_FAILED", type(exc).__name__)
        print("NO_WRITES no rows archived or updated")
        return 1
    if not rows:
        print("EMPTY_SNAPSHOT")
        print("NO_WRITES empty source snapshot is not a withdrawal")
        return 1
    if not args.apply_local_disposable:
        plan = plan_sync(rows, {}, complete=True)
        print("SEEN", plan.seen)
        print("ELIGIBLE", plan.eligible)
        print("INSERTS", len(plan.inserts))
        print("UPDATES", len(plan.updates))
        print("WOULD_ARCHIVE", 0)
        print("NOTE dry-run does not load local jobs and does not archive")
        print("EXCLUSIONS")
        for reason, count in sorted(plan.exclusions.items()):
            print(f"  {reason} {count}")
        print("FLAGS")
        for reason, count in sorted(plan.flagged.items()):
            print(f"  {reason} {count}")
        return 0

    target_url = args.target_url.strip()
    assert_disposable_local(target_url, args.target_database.strip())
    print("TARGET", describe_target(target_url))
    existing = await _owned_existing(target_url)
    plan = plan_sync(rows, existing, complete=True)
    engine = create_async_engine(target_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_factory() as db:
            result = await apply_plan(db, plan)
    finally:
        await engine.dispose()
    print("SEEN", result.seen)
    print("ELIGIBLE", result.eligible)
    print("INSERTS", result.inserted)
    print("UPDATES", result.updated)
    print("ARCHIVED", result.archived)
    print("SKIPPED_FOREIGN", result.skipped_foreign)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
