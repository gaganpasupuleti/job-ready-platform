"""Production-safe jobs database coverage report.

Usage:
  python -m app.jobs.coverage
  python -m app.jobs.coverage --json
"""

from __future__ import annotations

import argparse
import asyncio
import json
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal, engine
from app.models.job import Job, JobApplication, JobLocation, JobRoleMap, JobSkill, SavedJob
from app.models.job_enums import JobListingType, JobStatus
from app.models.tagging import Company, JobRole, Skill


def _url_ok(url: str | None) -> bool:
    if not url or not str(url).strip():
        return False
    raw = str(url).strip()
    lower = raw.lower()
    if lower.startswith(("javascript:", "data:", "vbscript:")):
        return False
    try:
        parsed = urlparse(raw)
    except Exception:  # noqa: BLE001
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _freshness_bucket(posted_at: datetime | None, now: datetime) -> str:
    if posted_at is None:
        return "unknown"
    days = (now - posted_at).days
    if days <= 7:
        return "0-7"
    if days <= 14:
        return "8-14"
    if days <= 30:
        return "15-30"
    if days <= 60:
        return "31-60"
    return "60+"


def _quality_score(job: Job, *, has_role: bool, has_skill: bool, has_loc: bool) -> int:
    score = 0
    if job.company_id:
        score += 1
    if job.description and len(job.description) > 40:
        score += 1
    if has_role:
        score += 1
    if has_skill:
        score += 1
    if _url_ok(job.apply_url) or _url_ok(job.source_url):
        score += 1
    if has_loc:
        score += 1
    if job.posted_at:
        score += 1
    return score


async def jobs_coverage_report(session: AsyncSession) -> dict[str, Any]:
    now = datetime.now(UTC)
    jobs = (await session.execute(select(Job))).scalars().all()

    # Expire by expires_at for reporting (does not mutate)
    active = [
        j
        for j in jobs
        if j.is_active
        and j.status == JobStatus.ACTIVE
        and (j.expires_at is None or j.expires_at > now)
    ]
    expired = [j for j in jobs if j.status == JobStatus.EXPIRED or (j.expires_at and j.expires_at <= now)]
    archived = [j for j in jobs if j.status == JobStatus.ARCHIVED or not j.is_active]

    job_ids = [j.id for j in jobs]
    role_maps = (
        await session.execute(select(JobRoleMap).where(JobRoleMap.job_id.in_(job_ids)))
    ).scalars().all() if job_ids else []
    skill_maps = (
        await session.execute(select(JobSkill).where(JobSkill.job_id.in_(job_ids)))
    ).scalars().all() if job_ids else []
    locations = (
        await session.execute(select(JobLocation).where(JobLocation.job_id.in_(job_ids)))
    ).scalars().all() if job_ids else []

    roles_by_job: dict = defaultdict(set)
    for rm in role_maps:
        roles_by_job[rm.job_id].add(rm.role_id)
    skills_by_job: dict = defaultdict(set)
    for sm in skill_maps:
        skills_by_job[sm.job_id].add(sm.skill_id)
    locs_by_job: dict = defaultdict(int)
    for loc in locations:
        locs_by_job[loc.job_id] += 1

    companies = (await session.execute(select(Company))).scalars().all()
    roles = (await session.execute(select(JobRole))).scalars().all()
    skills = (await session.execute(select(Skill))).scalars().all()
    role_names = {r.id: r.name for r in roles}
    company_names = {c.id: c.name for c in companies}

    real_active = [
        j
        for j in active
        if j.listing_type
        and j.listing_type != JobListingType.SAMPLE_DEMO
    ]
    sample_active = [j for j in active if j.listing_type == JobListingType.SAMPLE_DEMO]

    by_role: dict[str, int] = defaultdict(int)
    by_company: dict[str, int] = defaultdict(int)
    by_city: dict[str, int] = defaultdict(int)
    by_work_mode: dict[str, int] = defaultdict(int)
    by_listing: dict[str, int] = defaultdict(int)
    by_freshness: dict[str, int] = defaultdict(int)

    for j in active:
        mapped = roles_by_job.get(j.id) or set()
        if not mapped:
            by_role["(unmapped)"] += 1
        else:
            for rid in mapped:
                by_role[role_names.get(rid, str(rid))] += 1
        cname = company_names.get(j.company_id) if j.company_id else (j.company_name_raw or "(unknown)")
        by_company[str(cname)] += 1
        by_city[(j.city or j.location_text or "(unknown)")] += 1
        by_work_mode[str(getattr(j.work_mode, "value", j.work_mode) or "unknown")] += 1
        by_listing[str(getattr(j.listing_type, "value", j.listing_type) or "unset")] += 1
        by_freshness[_freshness_bucket(j.posted_at, now)] += 1

    def _count_active(pred) -> int:
        return sum(1 for j in active if pred(j))

    company_mapped = _count_active(lambda j: j.company_id is not None)
    role_mapped = _count_active(lambda j: bool(roles_by_job.get(j.id)))
    skill_mapped = _count_active(lambda j: bool(skills_by_job.get(j.id)))
    location_present = _count_active(
        lambda j: bool(j.location_text) or bool(j.city) or locs_by_job.get(j.id, 0) > 0
    )
    valid_apply = _count_active(lambda j: _url_ok(j.apply_url))
    with_description = _count_active(lambda j: bool(j.description and len(j.description) > 40))
    with_requirements = _count_active(lambda j: bool(j.requirements_text))
    with_posted = _count_active(lambda j: j.posted_at is not None)

    quality = [
        {
            "slug": j.slug,
            "title": j.title,
            "score": _quality_score(
                j,
                has_role=bool(roles_by_job.get(j.id)),
                has_skill=bool(skills_by_job.get(j.id)),
                has_loc=bool(j.location_text or j.city or locs_by_job.get(j.id)),
            ),
        }
        for j in active
    ]

    saved_count = int(await session.scalar(select(func.count()).select_from(SavedJob)) or 0)
    app_count = int(await session.scalar(select(func.count()).select_from(JobApplication)) or 0)

    n_active = len(active)
    pct = lambda n: round(100.0 * n / n_active, 1) if n_active else 0.0

    return {
        "summary": {
            "total_jobs": len(jobs),
            "active_jobs": n_active,
            "real_active_jobs": len(real_active),
            "sample_active_jobs": len(sample_active),
            "expired_jobs": len(expired),
            "archived_or_inactive": len(archived),
            "mapped_companies_catalog": len(companies),
            "mapped_roles_catalog": len(roles),
            "mapped_skills_catalog": len(skills),
            "company_mapped": company_mapped,
            "company_mapped_pct": pct(company_mapped),
            "role_mapped": role_mapped,
            "role_mapped_pct": pct(role_mapped),
            "skill_mapped": skill_mapped,
            "skill_mapped_pct": pct(skill_mapped),
            "location_present": location_present,
            "location_present_pct": pct(location_present),
            "valid_apply_url": valid_apply,
            "valid_apply_url_pct": pct(valid_apply),
            "with_description": with_description,
            "with_description_pct": pct(with_description),
            "with_requirements": with_requirements,
            "with_requirements_pct": pct(with_requirements),
            "with_posted_date": with_posted,
            "with_posted_date_pct": pct(with_posted),
            "saved_jobs": saved_count,
            "applications": app_count,
            "by_role": dict(sorted(by_role.items(), key=lambda x: (-x[1], x[0]))),
            "by_company": dict(sorted(by_company.items(), key=lambda x: (-x[1], x[0]))[:25]),
            "by_city": dict(sorted(by_city.items(), key=lambda x: (-x[1], x[0]))[:25]),
            "by_work_mode": dict(sorted(by_work_mode.items())),
            "by_listing_type": dict(sorted(by_listing.items())),
            "by_freshness": dict(sorted(by_freshness.items())),
            "avg_quality_score": round(
                sum(i["score"] for i in quality) / len(quality), 2
            )
            if quality
            else 0,
        },
        "quality_samples": sorted(quality, key=lambda x: -x["score"])[:15],
    }


def _print_human(report: dict[str, Any]) -> None:
    s = report["summary"]
    print("=== JOBS COVERAGE ===")
    print(f"Active jobs:              {s['active_jobs']}")
    print(f"Real/curated active:      {s['real_active_jobs']}")
    print(f"Sample demo active:       {s['sample_active_jobs']}")
    print(f"Expired (status/date):    {s['expired_jobs']}")
    print(f"Company mapped:           {s['company_mapped']} ({s['company_mapped_pct']}%)")
    print(f"Role mapped:              {s['role_mapped']} ({s['role_mapped_pct']}%)")
    print(f"Skill mapped:             {s['skill_mapped']} ({s['skill_mapped_pct']}%)")
    print(f"Location present:         {s['location_present']} ({s['location_present_pct']}%)")
    print(f"Valid apply URL:          {s['valid_apply_url']} ({s['valid_apply_url_pct']}%)")
    print(f"With description:         {s['with_description']} ({s['with_description_pct']}%)")
    print(f"With posted date:         {s['with_posted_date']} ({s['with_posted_date_pct']}%)")
    print(f"Avg quality score (0-7):  {s['avg_quality_score']}")
    print("By listing type:", s["by_listing_type"])
    print("By freshness:", s["by_freshness"])
    print("By role (active):")
    for name, n in s["by_role"].items():
        print(f"  {name}: {n}")


async def _run(as_json: bool) -> None:
    async with AsyncSessionLocal() as session:
        report = await jobs_coverage_report(session)
    await engine.dispose()
    if as_json:
        print(json.dumps(report, indent=2, default=str))
    else:
        _print_human(report)


def main() -> None:
    parser = argparse.ArgumentParser(description="Jobs coverage report")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()
    asyncio.run(_run(args.json))


if __name__ == "__main__":
    main()
