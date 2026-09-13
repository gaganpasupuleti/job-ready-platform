"""Prove local apply against a disposable database, then drop it.

Does not read or write the Jobs server catalog. Production apply stays disabled.
"""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import asyncpg
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.models.job import Job, JobApplication, SavedJob
from app.models.job_enums import ApplicationStatus, JobStatus
from app.models.enums import UserRole
from app.models.user import User
from app.services.jobs_source_sync import SourceJob, apply_plan, plan_sync, source_identity
from sync_jobs_source import DISPOSABLE_DATABASE, assert_disposable_local, describe_target

ADMIN_URL = os.environ.get("JOBS_APPLY_ADMIN_URL", "").strip()
CREATE_URL = os.environ.get("JOBS_APPLY_CREATE_URL", "").strip()


def _async_url(database: str) -> str:
    raw = ADMIN_URL.replace("postgresql+asyncpg://", "postgresql://", 1)
    parsed = urlparse(raw)
    auth = parsed.username or ""
    if parsed.password:
        auth = f"{auth}:{parsed.password}"
    return (
        f"postgresql+asyncpg://{auth}@{parsed.hostname}:{parsed.port or 5432}/{database}"
    )


def _row(job_id: str, *, approved: str) -> SourceJob:
    return SourceJob(
        job_id=job_id,
        source="naukri",
        title="Data Engineer",
        company="Fixture Mapping Co",
        location="Hyderabad",
        job_url=f"https://example.com/jobs/{job_id}",
        apply_url=f"https://example.com/apply/{job_id}",
        link_status="active",
        approved_status=approved,
        manual_review_needed=False,
        date_posted=datetime(2026, 9, 1, tzinfo=UTC),
        scraped_created_at=datetime(2026, 9, 8, tzinfo=UTC),
        synced_at=datetime(2026, 9, 9, tzinfo=UTC),
        jd_summary=None,
        jd_clean="Source description only.",
        jd_requirements=["SQL required"],
        jd_responsibilities=["Own the warehouse"],
        required_skills=["sql"],
        actual_role_name="Data Engineer",
        role_family="data-engineer",
    )


def _maintenance_connect(database: str = "postgres"):
    raw = CREATE_URL.replace("postgresql+asyncpg://", "postgresql://", 1)
    parsed = urlparse(raw)
    return asyncpg.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        user=parsed.username,
        password=parsed.password,
        database=database,
    )


async def _recreate() -> None:
    conn = await _maintenance_connect()
    try:
        await conn.execute(
            f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{DISPOSABLE_DATABASE}'"
        )
        await conn.execute(f"DROP DATABASE IF EXISTS {DISPOSABLE_DATABASE}")
        await conn.execute(f"CREATE DATABASE {DISPOSABLE_DATABASE} OWNER jobready")
    finally:
        await conn.close()


async def _drop() -> None:
    conn = await _maintenance_connect()
    try:
        await conn.execute(
            f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{DISPOSABLE_DATABASE}'"
        )
        await conn.execute(f"DROP DATABASE IF EXISTS {DISPOSABLE_DATABASE}")
    finally:
        await conn.close()


async def main() -> int:
    if not ADMIN_URL or not CREATE_URL:
        print("APPLY_REFUSED local admin URL is not configured")
        return 2
    target = _async_url(DISPOSABLE_DATABASE)
    assert_disposable_local(target, DISPOSABLE_DATABASE)
    print("TARGET", describe_target(target))
    await _recreate()
    env = os.environ.copy()
    env["DATABASE_URL"] = target
    env["APP_ENV"] = "development"
    migrated = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    if migrated.returncode != 0:
        print("MIGRATE_FAILED")
        print(migrated.stderr[-400:])
        await _drop()
        return 1
    owned_key = "CQJ-DISP-OWN"
    engine = create_async_engine(target)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with factory() as db:
            first = await apply_plan(db, plan_sync([_row(owned_key, approved="APPROVED")], {}, complete=True))
            job = (
                await db.execute(select(Job).where(Job.external_id == source_identity(owned_key)))
            ).scalar_one()
            user = User(
                id=uuid4(),
                email=f"sync-{uuid4().hex[:8]}@example.com",
                username=f"sync{uuid4().hex[:8]}",
                password_hash="not-a-login",
                role=UserRole.STUDENT,
                is_active=True,
            )
            db.add(user)
            await db.flush()
            db.add(SavedJob(id=uuid4(), user_id=user.id, job_id=job.id))
            application = JobApplication(
                id=uuid4(),
                user_id=user.id,
                job_id=job.id,
                status=ApplicationStatus.APPLIED,
                applied_at=datetime.now(UTC),
            )
            db.add(application)
            foreign = Job(
                id=uuid4(),
                slug=f"manual-keep-{uuid4().hex[:8]}",
                external_id="manual:keep",
                title="Keep this manual listing",
                normalized_title="keep this manual listing",
                description="Not owned by the catalog sync.",
                status=JobStatus.ACTIVE,
                is_active=True,
                content_hash=uuid4().hex,
                first_seen_at=datetime.now(UTC),
                last_seen_at=datetime.now(UTC),
            )
            db.add(foreign)
            await db.commit()
            job_id = job.id
            application_id = application.id
            foreign_id = foreign.id
        print("SEED_INSERTS", first.inserted)
        nonempty = [
            _row(owned_key, approved="PENDING"),
            _row("CQJ-DISP-OTHER", approved="NEEDS_REVIEW"),
        ]
        plan = plan_sync(
            nonempty,
            {source_identity(owned_key): job_id, "jobs-server:missing": foreign_id},
            complete=True,
        )
        async with factory() as db:
            result = await apply_plan(db, plan)
            stored = await db.get(Job, job_id)
            saved = (await db.execute(select(SavedJob).where(SavedJob.job_id == job_id))).scalar_one()
            app_row = await db.get(JobApplication, application_id)
            other = await db.get(Job, foreign_id)
        print("SEEN", result.seen)
        print("ELIGIBLE", result.eligible)
        print("INSERTS", result.inserted)
        print("UPDATES", result.updated)
        print("ARCHIVED", result.archived)
        print("SKIPPED_FOREIGN", result.skipped_foreign)
        print("OWNED_STATUS", stored.status.value if stored else "missing")
        print("SAVED_KEPT", saved.job_id == job_id)
        print("APPLICATION_KEPT", app_row is not None and app_row.job_id == job_id)
        print("FOREIGN_STATUS", other.status.value if other else "missing")
        empty = plan_sync([], {source_identity(owned_key): job_id}, complete=True)
        print("EMPTY_ARCHIVE_IDS", len(empty.archive_ids))
        try:
            async with factory() as db:
                await apply_plan(db, empty)
            print("EMPTY_APPLY unexpected")
            return 1
        except RuntimeError as exc:
            print("EMPTY_APPLY_REFUSED", exc)
        return 0 if result.archived == 1 and result.skipped_foreign == 1 and stored.status == JobStatus.ARCHIVED else 1
    finally:
        await engine.dispose()
        await _drop()
        print("DROPPED", DISPOSABLE_DATABASE)


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
