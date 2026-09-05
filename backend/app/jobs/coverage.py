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
from typing import Any
from urllib.parse import urlparse

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal, engine
from app.models.job import Job, JobApplication, JobLocation, JobRoleMap, JobSkill, SavedJob
from app.models.job_enums import JobStatus
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


async def jobs_coverage_report(session: AsyncSession) -> dict[str, Any]:
    jobs = (await session.execute(select(Job))).scalars().all()

    active = [j for j in jobs if j.is_active and j.status == JobStatus.ACTIVE]
    expired = [j for j in jobs if j.status == JobStatus.EXPIRED]
    archived = [j for j in jobs if j.status == JobStatus.ARCHIVED or not j.is_active]

    job_ids = [j.id for j in jobs]
    active_ids = {j.id for j in active}

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

    by_role: dict[str, int] = defaultdict(int)
    for j in active:
        mapped = roles_by_job.get(j.id) or set()
        if not mapped:
            by_role["(unmapped)"] += 1
        else:
            for rid in mapped:
                by_role[role_names.get(rid, str(rid))] += 1

    def _count_active(pred) -> int:
        return sum(1 for j in active if pred(j))

    company_mapped = _count_active(lambda j: j.company_id is not None)
    role_mapped = _count_active(lambda j: bool(roles_by_job.get(j.id)))
    skill_mapped = _count_active(lambda j: bool(skills_by_job.get(j.id)))
    location_present = _count_active(
        lambda j: bool(j.location_text) or bool(j.city) or locs_by_job.get(j.id, 0) > 0
    )
    valid_apply = _count_active(lambda j: _url_ok(j.apply_url))
    valid_source = _count_active(lambda j: _url_ok(j.source_url))

    missing = {
        "without_company_mapping": [
            {"id": str(j.id), "title": j.title, "slug": j.slug}
            for j in active
            if j.company_id is None
        ],
        "without_role_mapping": [
            {"id": str(j.id), "title": j.title, "slug": j.slug}
            for j in active
            if not roles_by_job.get(j.id)
        ],
        "without_skill_mapping": [
            {"id": str(j.id), "title": j.title, "slug": j.slug}
            for j in active
            if not skills_by_job.get(j.id)
        ],
        "without_location": [
            {"id": str(j.id), "title": j.title, "slug": j.slug}
            for j in active
            if not (j.location_text or j.city or locs_by_job.get(j.id, 0))
        ],
        "without_valid_apply_url": [
            {"id": str(j.id), "title": j.title, "slug": j.slug, "apply_url": j.apply_url}
            for j in active
            if not _url_ok(j.apply_url)
        ],
        "malformed_urls": [
            {
                "id": str(j.id),
                "title": j.title,
                "slug": j.slug,
                "apply_url": j.apply_url,
                "source_url": j.source_url,
            }
            for j in active
            if (j.apply_url and not _url_ok(j.apply_url))
            or (j.source_url and not _url_ok(j.source_url))
        ],
    }

    saved_count = int(await session.scalar(select(func.count()).select_from(SavedJob)) or 0)
    app_count = int(await session.scalar(select(func.count()).select_from(JobApplication)) or 0)

    n_active = len(active)
    pct = lambda n: round(100.0 * n / n_active, 1) if n_active else 0.0

    return {
        "summary": {
            "total_jobs": len(jobs),
            "active_jobs": n_active,
            "expired_jobs": len(expired),
            "archived_or_inactive": len(archived),
            "mapped_companies_catalog": len(companies),
            "mapped_roles_catalog": len(roles),
            "mapped_skills_catalog": len(skills),
            "job_location_rows": len(locations),
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
            "valid_source_url": valid_source,
            "saved_jobs": saved_count,
            "applications": app_count,
            "by_role": dict(sorted(by_role.items(), key=lambda x: (-x[1], x[0]))),
        },
        "gaps": {k: v for k, v in missing.items()},
        "gap_counts": {k: len(v) for k, v in missing.items()},
    }


def _print_human(report: dict[str, Any]) -> None:
    s = report["summary"]
    print("=== JOBS COVERAGE ===")
    print(f"Active jobs:              {s['active_jobs']}")
    print(f"Expired jobs:             {s['expired_jobs']}")
    print(f"Archived/inactive:        {s['archived_or_inactive']}")
    print(f"Company catalog size:     {s['mapped_companies_catalog']}")
    print(f"Role catalog size:        {s['mapped_roles_catalog']}")
    print(f"Skill catalog size:       {s['mapped_skills_catalog']}")
    print(f"Company mapped:           {s['company_mapped']} ({s['company_mapped_pct']}%)")
    print(f"Role mapped:              {s['role_mapped']} ({s['role_mapped_pct']}%)")
    print(f"Skill mapped:             {s['skill_mapped']} ({s['skill_mapped_pct']}%)")
    print(f"Location present:         {s['location_present']} ({s['location_present_pct']}%)")
    print(f"Valid apply URL:          {s['valid_apply_url']} ({s['valid_apply_url_pct']}%)")
    print(f"Saved jobs:               {s['saved_jobs']}")
    print(f"Applications:             {s['applications']}")
    print("By role (active):")
    for name, n in s["by_role"].items():
        print(f"  {name}: {n}")
    print("Gap counts:")
    for k, n in report["gap_counts"].items():
        print(f"  {k}: {n}")


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
