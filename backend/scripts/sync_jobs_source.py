"""Dry-run and controlled apply for the Jobs server catalog.

Source access stays read-only. A full catalog apply remains disabled.
A reviewed batch reads the application target from JOBS_APPLY_DATABASE_URL.
Confirm that target with host:port/database. Do not pass a DSN as an argument.
The source and application targets are refused if they are the same or swapped.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.models.job import Job, JobApplication, SavedJob
from app.services.jobs_source_reader import fetch_source_jobs, public_proxy_dsn
from app.services.jobs_source_sync import (
    EXTERNAL_PREFIX,
    apply_named_plan,
    apply_plan,
    assert_application_target,
    assert_catalog_roles,
    assert_named_plan_unchanged,
    decision_key,
    load_publication_decisions,
    parse_reviewed_batch,
    plan_named_batch,
    plan_sync,
    source_identity,
)

logging.getLogger("sqlalchemy.engine").setLevel(logging.CRITICAL)
logging.getLogger("sqlalchemy.pool").setLevel(logging.CRITICAL)

APPLY_TARGET_ENV = "JOBS_APPLY_DATABASE_URL"

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


def same_database(left: str, right: str) -> bool:
    def parts(value: str) -> tuple[str, int, str]:
        raw = value.replace("postgresql+asyncpg://", "postgresql://", 1)
        parsed = urlparse(raw)
        database = (parsed.path or "").lstrip("/").split("?")[0]
        return (parsed.hostname or "", parsed.port or 5432, database)

    return parts(left) == parts(right)


def _engine(database_url: str):
    return create_async_engine(database_url, echo=False, hide_parameters=True)


def _apply_target_url() -> str:
    value = os.environ.get(APPLY_TARGET_ENV, "").strip()
    if not value:
        raise SystemExit("APPLY_REFUSED application target is not configured")
    return value


def _application_database_url() -> str:
    value = os.environ.get("DATABASE_URL", "").strip()
    if not value:
        raise SystemExit("APPLY_REFUSED application database is not configured")
    return value


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
    engine = _engine(database_url)
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


async def _relation_present(database_url: str, table: str) -> bool:
    engine = _engine(database_url)
    try:
        async with engine.connect() as conn:
            found = await conn.scalar(
                text(
                    "SELECT 1 FROM information_schema.tables "
                    "WHERE table_schema = 'public' AND table_name = :name"
                ),
                {"name": table},
            )
            return found is not None
    finally:
        await engine.dispose()


async def _assert_connected_roles(apply_url: str, source_url: str) -> None:
    try:
        apply_has_decisions = await _relation_present(apply_url, "job_publication_decisions")
        source_has_validated_jobs = await _relation_present(source_url, "validated_jobs")
        source_has_decisions = await _relation_present(source_url, "job_publication_decisions")
    except Exception as exc:
        print("PROBE_FAILED", type(exc).__name__)
        print("NO_WRITES no rows archived or updated")
        raise SystemExit(1) from None
    assert_catalog_roles(
        apply_has_decisions=apply_has_decisions,
        source_has_validated_jobs=source_has_validated_jobs,
        source_has_decisions=source_has_decisions,
    )


def _print_named_plan(plan) -> None:
    print("MODE named-batch")
    print("NAMED", plan.seen)
    print("ELIGIBLE", plan.eligible)
    print("INSERTS", len(plan.inserts))
    print("UPDATES", len(plan.updates))
    print("ARCHIVE", 0)
    print("ELIGIBLE_IDS")
    for row in plan.inserts:
        print(f"  {row.source}/{row.job_id} insert")
    for _job_id, row in plan.updates:
        print(f"  {row.source}/{row.job_id} update")
    print("REJECTED")
    for source, job_id, reasons in plan.rejected:
        print(f"  {source}/{job_id} {reasons}")


async def _named_plan(target_url: str, names, rows):
    existing = await _owned_existing(target_url)
    engine = _engine(target_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_factory() as db:
            decisions = await load_publication_decisions(db)
    finally:
        await engine.dispose()
    return plan_named_batch(rows, existing, decisions, names)


async def _verify_named_batch(target_url: str, names) -> int:
    engine = _engine(target_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_factory() as db:
            decisions = await load_publication_decisions(db)
            print("VERIFY")
            for name in names:
                identity = source_identity(name.job_id)
                job = (
                    await db.execute(select(Job).where(Job.external_id == identity))
                ).scalar_one_or_none()
                decision = decisions.get(decision_key(name.source, name.job_id), "missing")
                if job is None:
                    print(f"  {name.source}/{name.job_id} present=no decision={decision}")
                    continue
                saved_count = await db.scalar(
                    select(func.count()).select_from(SavedJob).where(SavedJob.job_id == job.id)
                )
                application_count = await db.scalar(
                    select(func.count()).select_from(JobApplication).where(JobApplication.job_id == job.id)
                )
                print(
                    f"  {name.source}/{name.job_id} present=yes id={job.id} status={job.status.value} "
                    f"saved={saved_count} applications={application_count} decision={decision}"
                )
    finally:
        await engine.dispose()
    return 0


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--apply-local-disposable", action="store_true")
    parser.add_argument("--apply-reviewed-batch", action="store_true")
    parser.add_argument("--verify-reviewed-batch", action="store_true")
    parser.add_argument("--batch", default="")
    parser.add_argument("--confirm-target", default="")
    parser.add_argument("--target-database", default="")
    parser.add_argument("--target-url", default="")
    args = parser.parse_args()
    if args.apply and not args.apply_local_disposable and not args.apply_reviewed_batch:
        print("APPLY_REFUSED production and source writes are disabled")
        return 2
    if args.apply_reviewed_batch or args.verify_reviewed_batch or args.batch:
        if args.target_url.strip():
            print("APPLY_REFUSED target connection must not be passed as an argument")
            return 2
        if not args.batch.strip() or not args.confirm_target.strip():
            print("APPLY_REFUSED explicit target confirmation and reviewed batch are required")
            return 2
        try:
            names = parse_reviewed_batch(Path(args.batch).read_text(encoding="utf-8"))
            apply_url = _apply_target_url()
            application_url = _application_database_url()
            source_url = _source_dsn()
            identity = assert_application_target(
                apply_url=apply_url,
                source_url=source_url,
                application_url=application_url,
                confirmation=args.confirm_target,
            )
        except SystemExit as exc:
            if isinstance(exc.code, int):
                raise
            print(exc.code)
            return 2
        except (OSError, ValueError):
            print("APPLY_REFUSED", "ValueError")
            return 2
        print("TARGET", identity)
        try:
            await _assert_connected_roles(apply_url, source_url)
        except SystemExit as exc:
            if exc.code == 1:
                return 1
            if isinstance(exc.code, str):
                print(exc.code)
            return 2
        if args.verify_reviewed_batch:
            try:
                return await _verify_named_batch(apply_url, names)
            except Exception as exc:
                print("VERIFY_FAILED", type(exc).__name__)
                return 1
        try:
            rows = await fetch_source_jobs(source_url)
        except Exception as exc:
            print("FETCH_FAILED", type(exc).__name__)
            print("NO_WRITES no rows archived or updated")
            return 1
        if not rows:
            print("EMPTY_SNAPSHOT")
            print("NO_WRITES empty source snapshot is not a withdrawal")
            return 1
        try:
            plan = await _named_plan(apply_url, names, rows)
        except Exception as exc:
            print("PLAN_FAILED", type(exc).__name__)
            print("NO_WRITES no rows archived or updated")
            return 1
        _print_named_plan(plan)
        if not args.apply_reviewed_batch:
            print("NO_WRITES named dry-run")
            return 0
        reviewed = plan
        try:
            rows = await fetch_source_jobs(source_url)
        except Exception as exc:
            print("FETCH_FAILED", type(exc).__name__)
            print("NO_WRITES no rows archived or updated")
            return 1
        if not rows:
            print("EMPTY_SNAPSHOT")
            print("NO_WRITES empty source snapshot is not a withdrawal")
            return 1
        try:
            await _assert_connected_roles(apply_url, source_url)
            plan = await _named_plan(apply_url, names, rows)
            assert_named_plan_unchanged(reviewed, plan)
        except SystemExit as exc:
            if isinstance(exc.code, str):
                print(exc.code)
            print("NO_WRITES no rows archived or updated")
            return 2 if not isinstance(exc.code, int) or exc.code != 1 else 1
        except Exception as exc:
            print("RECHECK_FAILED", type(exc).__name__)
            print("NO_WRITES no rows archived or updated")
            return 1
        engine = _engine(apply_url)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        try:
            async with session_factory() as db:
                result = await apply_named_plan(db, plan)
        except Exception as exc:
            print("APPLY_FAILED", type(exc).__name__)
            print("NO_WRITES unexpected apply error")
            return 1
        finally:
            await engine.dispose()
        print("APPLIED", result.inserted, result.updated)
        print("ARCHIVED", result.archived)
        return 0
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
    engine = _engine(target_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_factory() as db:
            decisions = await load_publication_decisions(db)
        plan = plan_sync(rows, existing, complete=True, decisions=decisions)
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
    try:
        raise SystemExit(asyncio.run(main()))
    except SystemExit:
        raise
    except Exception:
        print("FAILED unexpected error")
        raise SystemExit(1) from None
