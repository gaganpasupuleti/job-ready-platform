"""Read-only fetch from the Jobs server catalog. Never writes and never logs the DSN."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from urllib.parse import urlparse

import asyncpg

from app.services.jobs_source_sync import SourceJob

_QUERY = """
SELECT job_id, source, title, company, location, job_url, apply_url, link_status,
       approved_status, manual_review_needed, date_posted, scraped_created_at, synced_at,
       jd_summary, jd_clean, jd_requirements, jd_responsibilities, required_skills,
       actual_role_name, role_family, salary_min, salary_max, currency
FROM public.validated_jobs
"""


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


async def fetch_source_jobs(dsn: str) -> list[SourceJob]:
    conn = await asyncpg.connect(dsn, ssl="require", timeout=30)
    try:
        await conn.execute("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY")
        rows = await conn.fetch(_QUERY)
    finally:
        await conn.close()
    jobs: list[SourceJob] = []
    for row in rows:
        jobs.append(
            SourceJob(
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
                actual_role_name=row["actual_role_name"],
                role_family=row["role_family"],
                salary_min=_money(row["salary_min"]),
                salary_max=_money(row["salary_max"]),
                currency=row["currency"],
            )
        )
    return jobs
