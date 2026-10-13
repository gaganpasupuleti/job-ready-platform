"""Read-only fetch from the Jobs server catalog. Never writes and never logs the DSN."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from urllib.parse import urlparse

import asyncpg

from app.services.jobs_source_sync import SourceJob

_COLUMNS = """job_id, source, title, company, location, job_url, apply_url, link_status,
       approved_status, manual_review_needed, date_posted, scraped_created_at, synced_at,
       jd_summary, jd_clean, jd_requirements, jd_responsibilities, required_skills,
       actual_role_id, actual_role_name, role_family, experience_bucket,
       salary_min, salary_max, currency"""

_QUERY = f"""
SELECT {_COLUMNS}
FROM public.validated_jobs
"""

_CATALOG_QUERY = f"""
SELECT {_COLUMNS}, has_jd_clean
FROM public.validated_jobs
"""

_RELATIONS_QUERY = """
SELECT to_regclass('public.validated_jobs') IS NOT NULL,
       to_regclass('public.job_publication_decisions') IS NOT NULL
"""


@dataclass(frozen=True)
class CatalogEntry:
    job: SourceJob
    has_jd_clean: bool | None


@dataclass(frozen=True)
class SourceCatalogSnapshot:
    """One read-only transaction over the catalog and its role probes."""

    entries: list[CatalogEntry]
    has_validated_jobs: bool
    has_publication_decisions: bool


def public_proxy_dsn(database_url: str, host: str, port: int) -> str:
    raw = database_url
    if raw.startswith("postgres://"):
        raw = "postgresql://" + raw[len("postgres://") :]
    parsed = urlparse(raw)
    auth = parsed.username or ""
    if parsed.password:
        auth = f"{auth}:{parsed.password}"
    database = (parsed.path or "").lstrip("/")
    return f"postgresql://{auth}@{host}:{port}/{database}"


def _money(value: Any) -> Decimal | None:
    if value is None:
        return None
    return Decimal(value)


def _source_job(row: Any) -> SourceJob:
    return SourceJob(
        job_id=row["job_id"],
        source=row["source"],
        title=row["title"],
        company=row["company"],
        location=row["location"],
        job_url=row["job_url"],
        apply_url=row["apply_url"],
        link_status=row["link_status"],
        approved_status=row["approved_status"],
        manual_review_needed=row["manual_review_needed"],
        date_posted=row["date_posted"],
        scraped_created_at=row["scraped_created_at"],
        synced_at=row["synced_at"],
        jd_summary=row["jd_summary"],
        jd_clean=row["jd_clean"],
        jd_requirements=row["jd_requirements"],
        jd_responsibilities=row["jd_responsibilities"],
        required_skills=row["required_skills"],
        actual_role_id=row["actual_role_id"],
        actual_role_name=row["actual_role_name"],
        role_family=row["role_family"],
        experience_bucket=row["experience_bucket"],
        salary_min=_money(row["salary_min"]),
        salary_max=_money(row["salary_max"]),
        currency=row["currency"],
    )


async def fetch_source_jobs(dsn: str) -> list[SourceJob]:
    conn = await asyncpg.connect(dsn, ssl="require", timeout=30)
    try:
        await conn.execute("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY")
        rows = await conn.fetch(_QUERY)
    finally:
        await conn.close()
    return [_source_job(row) for row in rows]


async def fetch_source_catalog(dsn: str) -> SourceCatalogSnapshot:
    """Read the catalog and its role probes in one verified read-only transaction."""
    conn = await asyncpg.connect(dsn, ssl="require", timeout=30)
    try:
        await conn.execute("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY")
        async with conn.transaction(isolation="repeatable_read", readonly=True):
            if await conn.fetchval("SHOW transaction_read_only") != "on":
                raise RuntimeError("source session is not read-only")
            has_validated_jobs, has_decisions = await conn.fetchrow(_RELATIONS_QUERY)
            rows = await conn.fetch(_CATALOG_QUERY) if has_validated_jobs else []
    finally:
        await conn.close()
    return SourceCatalogSnapshot(
        entries=[
            CatalogEntry(job=_source_job(row), has_jd_clean=row["has_jd_clean"]) for row in rows
        ],
        has_validated_jobs=bool(has_validated_jobs),
        has_publication_decisions=bool(has_decisions),
    )
