"""Validate job source/apply URLs without mutating data.

Usage:
  python -m app.jobs.validate_urls
  python -m app.jobs.validate_urls --json --limit 50
"""

from __future__ import annotations

import argparse
import asyncio
import json
from typing import Any
from urllib.parse import urlparse

import httpx
from sqlalchemy import select

from app.db.session import AsyncSessionLocal, engine
from app.models.job import Job
from app.models.job_enums import JobStatus


def _scheme_ok(url: str | None) -> bool:
    if not url:
        return False
    lower = url.strip().lower()
    if lower.startswith(("javascript:", "data:", "vbscript:")):
        return False
    try:
        p = urlparse(url.strip())
    except Exception:  # noqa: BLE001
        return False
    return p.scheme in {"http", "https"} and bool(p.netloc)


async def _check_one(client: httpx.AsyncClient, url: str | None) -> str:
    if not url:
        return "UNKNOWN"
    if not _scheme_ok(url):
        return "DEAD"
    try:
        resp = await client.head(url, follow_redirects=True)
        code = resp.status_code
        if code in {404, 410}:
            return "DEAD"
        if code >= 400:
            # Some boards block HEAD — retry GET lightly
            resp = await client.get(url, follow_redirects=True)
            code = resp.status_code
            if code in {404, 410}:
                return "DEAD"
            if code >= 400:
                return "UNKNOWN"
        if resp.history:
            return "REDIRECT"
        return "VALID"
    except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPError):
        return "UNKNOWN"


async def validate_urls(*, limit: int | None = None) -> dict[str, Any]:
    async with AsyncSessionLocal() as session:
        stmt = select(Job).where(Job.status == JobStatus.ACTIVE).order_by(Job.created_at.desc())
        if limit:
            stmt = stmt.limit(limit)
        jobs = (await session.execute(stmt)).scalars().all()

    results: list[dict[str, Any]] = []
    tallies = {"VALID": 0, "REDIRECT": 0, "DEAD": 0, "UNKNOWN": 0}
    async with httpx.AsyncClient(timeout=8.0, headers={"User-Agent": "JobReadyURLCheck/1.0"}) as client:
        for job in jobs:
            apply_status = await _check_one(client, job.apply_url)
            source_status = await _check_one(client, job.source_url)
            # Prefer apply URL for overall status when present
            overall = apply_status if job.apply_url else source_status
            tallies[overall] = tallies.get(overall, 0) + 1
            results.append(
                {
                    "id": str(job.id),
                    "slug": job.slug,
                    "title": job.title,
                    "apply_url": job.apply_url,
                    "source_url": job.source_url,
                    "apply_status": apply_status,
                    "source_status": source_status,
                    "status": overall,
                }
            )
    return {"summary": tallies, "jobs": results}


async def _run(*, as_json: bool, limit: int | None) -> None:
    report = await validate_urls(limit=limit)
    await engine.dispose()
    if as_json:
        print(json.dumps(report, indent=2))
        return
    print("=== URL VALIDATION ===")
    for k, v in report["summary"].items():
        print(f"{k}: {v}")
    for row in report["jobs"]:
        if row["status"] != "VALID":
            print(f"  [{row['status']}] {row['title']} ({row['slug']})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate job URLs")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    asyncio.run(_run(as_json=args.json, limit=args.limit))


if __name__ == "__main__":
    main()
