"""Read-only sync from the Railway Jobs server catalog.

The source is PostgreSQL database `railway`, schema `public`, table
`validated_jobs`. It is not the application's `validated_jobs` table.
Publication requires an explicit approved status. PENDING and NEEDS_REVIEW
stay unpublished.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job, JobSource
from app.models.job_enums import JobSourceType, JobStatus
from app.models.tagging import Company
from app.services.job_normalization import job_content_hash, normalize_title, slugify_job, validate_url

SOURCE_SLUG_PREFIX = "jobs-server"
EXTERNAL_PREFIX = "jobs-server:"
APPROVED_STATUSES = frozenset({"APPROVED", "PUBLISHED"})
ACTIVE_LINK_STATUS = "active"
_MANUFACTURING_QC = re.compile(r"\b(?:qc|quality)\s+inspector\b|\bdrawing quality\b", re.I)
_SOFTWARE_QA = re.compile(r"qa|quality assurance|testing", re.I)


@dataclass(frozen=True)
class SourceJob:
    job_id: str
    source: str
    title: str
    company: str | None
    location: str | None
    job_url: str
    apply_url: str | None
    link_status: str
    approved_status: str | None
    manual_review_needed: bool | None
    date_posted: datetime | None
    scraped_created_at: datetime | None
    synced_at: datetime | None
    jd_summary: str | None
    jd_clean: str | None
    jd_requirements: Any
    jd_responsibilities: Any
    required_skills: Any
    actual_role_name: str | None
    role_family: str | None
    salary_min: Decimal | None = None
    salary_max: Decimal | None = None
    currency: str | None = None


@dataclass
class SyncPlan:
    complete: bool
    inserts: list[SourceJob] = field(default_factory=list)
    updates: list[tuple[UUID, SourceJob]] = field(default_factory=list)
    exclusions: dict[str, int] = field(default_factory=dict)
    flagged: dict[str, int] = field(default_factory=dict)
    archive_ids: list[UUID] = field(default_factory=list)
    eligible: int = 0
    seen: int = 0


@dataclass(frozen=True)
class ApplyResult:
    inserted: int
    updated: int
    archived: int
    skipped_foreign: int
    eligible: int
    seen: int


def source_identity(job_id: str) -> str:
    return f"{EXTERNAL_PREFIX}{job_id.strip()}"


def integration_owned(external_id: str | None) -> bool:
    """Only rows published by this catalog sync may be archived by it."""
    return bool(external_id and external_id.startswith(EXTERNAL_PREFIX))


def text_list(value: Any) -> tuple[list[str], bool]:
    """Return source strings and whether a non-string item was skipped."""
    parsed = value
    if isinstance(parsed, str):
        raw = parsed.strip()
        if not raw:
            return [], False
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return [raw], False
    if parsed is None:
        return [], False
    if not isinstance(parsed, list):
        return [], True
    items: list[str] = []
    skipped = False
    for item in parsed:
        if isinstance(item, str) and item.strip():
            items.append(item.strip())
        elif item is not None:
            skipped = True
    return items, skipped


def classification_mismatch(row: SourceJob) -> bool:
    """Manufacturing QC must not be published as software QA."""
    title = row.title or ""
    if not _MANUFACTURING_QC.search(title):
        return False
    role = f"{row.actual_role_name or ''} {row.role_family or ''}"
    return bool(_SOFTWARE_QA.search(role))


def https_url(value: str | None) -> str | None:
    if not value:
        return None
    text = value.strip()
    if text.lower().startswith("https://"):
        return validate_url(text)
    return None


def application_url(row: SourceJob) -> str | None:
    return https_url(row.apply_url) or https_url(row.job_url)


def description_text(row: SourceJob) -> str | None:
    clean = (row.jd_clean or "").strip()
    if clean:
        return clean
    summary = (row.jd_summary or "").strip()
    if summary:
        return summary
    requirements, _ = text_list(row.jd_requirements)
    responsibilities, _ = text_list(row.jd_responsibilities)
    lines = [*responsibilities, *requirements]
    if lines:
        return "\n".join(lines)
    return None


def exclusion_reasons(row: SourceJob) -> list[str]:
    reasons: list[str] = []
    if (row.approved_status or "").strip() not in APPROVED_STATUSES:
        reasons.append("not_explicitly_approved")
    if row.manual_review_needed is not False:
        reasons.append("manual_review_open")
    if (row.link_status or "").strip() != ACTIVE_LINK_STATUS:
        reasons.append("link_not_active")
    if not application_url(row):
        reasons.append("no_usable_application_url")
    if not (row.title or "").strip() or not (row.company or "").strip():
        reasons.append("missing_title_or_company")
    if len((row.title or "").strip()) > 255 or len((row.company or "").strip()) > 255:
        reasons.append("field_too_long")
    if not description_text(row):
        reasons.append("missing_source_description")
    if classification_mismatch(row):
        reasons.append("classification_mismatch")
    return reasons


def plan_sync(
    rows: list[SourceJob],
    existing_by_external_id: dict[str, UUID],
    *,
    complete: bool,
) -> SyncPlan:
    plan = SyncPlan(complete=complete, seen=len(rows))
    seen_identities: set[str] = set()
    for row in rows:
        identity = source_identity(row.job_id)
        seen_identities.add(identity)
        reasons = exclusion_reasons(row)
        if classification_mismatch(row):
            plan.flagged["classification_mismatch"] = plan.flagged.get("classification_mismatch", 0) + 1
        if reasons:
            for reason in reasons:
                plan.exclusions[reason] = plan.exclusions.get(reason, 0) + 1
            existing_id = existing_by_external_id.get(identity)
            if existing_id is not None and complete:
                plan.archive_ids.append(existing_id)
            continue
        plan.eligible += 1
        existing_id = existing_by_external_id.get(identity)
        if existing_id is None:
            plan.inserts.append(row)
        else:
            plan.updates.append((existing_id, row))
    # An empty successful snapshot is not proof the catalog was withdrawn.
    if complete and rows:
        for identity, job_id in existing_by_external_id.items():
            if identity not in seen_identities and job_id not in plan.archive_ids:
                plan.archive_ids.append(job_id)
                plan.exclusions["withdrawn_from_source"] = plan.exclusions.get("withdrawn_from_source", 0) + 1
    return plan


def _join(values: list[str]) -> str | None:
    return "\n".join(values) if values else None


async def apply_plan(db: AsyncSession, plan: SyncPlan) -> ApplyResult:
    """Write a complete nonempty plan. An empty or failed fetch must not be applied.

    A nonempty snapshot with zero eligible rows still archives previously published
    rows owned by this integration. Rows with any other external id are left alone.
    """
    if not plan.complete:
        raise RuntimeError("refusing to apply an incomplete source fetch")
    if plan.seen == 0:
        raise RuntimeError("refusing to apply an empty source snapshot")
    for row in plan.inserts:
        await _upsert(db, None, row)
    for job_id, row in plan.updates:
        await _upsert(db, job_id, row)
    archived = 0
    skipped_foreign = 0
    if plan.archive_ids:
        jobs = (
            await db.execute(select(Job).where(Job.id.in_(plan.archive_ids)))
        ).scalars().all()
        for job in jobs:
            if not integration_owned(job.external_id):
                skipped_foreign += 1
                continue
            job.status = JobStatus.ARCHIVED
            job.is_active = False
            archived += 1
    await db.commit()
    return ApplyResult(
        inserted=len(plan.inserts),
        updated=len(plan.updates),
        archived=archived,
        skipped_foreign=skipped_foreign,
        eligible=plan.eligible,
        seen=plan.seen,
    )


async def _board_source(db: AsyncSession, name: str) -> JobSource:
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-") or "unknown"
    slug = f"{SOURCE_SLUG_PREFIX}-{slug}"[:80]
    row = (await db.execute(select(JobSource).where(JobSource.slug == slug))).scalar_one_or_none()
    if row:
        return row
    row = JobSource(
        id=uuid4(),
        name=name.strip() or "unknown",
        slug=slug,
        source_type=JobSourceType.API,
        is_active=True,
    )
    db.add(row)
    await db.flush()
    return row


async def _company(db: AsyncSession, name: str) -> tuple[UUID | None, str | None]:
    existing = (
        await db.execute(select(Company).where(Company.name.ilike(name)).limit(1))
    ).scalar_one_or_none()
    if existing:
        return existing.id, None
    return None, name


async def _upsert(db: AsyncSession, job_id: UUID | None, row: SourceJob) -> Job:
    title = row.title.strip()
    company = (row.company or "").strip()
    description = description_text(row) or ""
    requirements, _ = text_list(row.jd_requirements)
    responsibilities, _ = text_list(row.jd_responsibilities)
    skills, _ = text_list(row.required_skills)
    if skills:
        skill_line = "Source skills: " + "; ".join(skills)
        requirements = [*requirements, skill_line]
    if row.actual_role_name and row.actual_role_name.strip():
        responsibilities = [*responsibilities, f"Source role: {row.actual_role_name.strip()}"]
    identity = source_identity(row.job_id)
    location = (row.location or "").strip() or None
    content_hash = job_content_hash(
        normalized_title=normalize_title(title),
        company=company,
        location=location,
        description_snippet=description,
        external_id=identity,
        source_slug=SOURCE_SLUG_PREFIX,
    )
    source = await _board_source(db, row.source or "unknown")
    company_id, company_raw = await _company(db, company)
    apply = application_url(row)
    posting = https_url(row.job_url)
    now = row.synced_at or datetime.now(UTC)
    job = await db.get(Job, job_id) if job_id else None
    if job is None:
        job = Job(
            id=uuid4(),
            slug=slugify_job(title, company, row.job_id.replace("-", "")[:8]),
            external_id=identity,
            source_id=source.id,
            title=title,
            normalized_title=normalize_title(title),
            company_id=company_id,
            company_name_raw=company_raw,
            description=description,
            requirements_text=_join(requirements),
            responsibilities_text=_join(responsibilities),
            location_text=location,
            source_url=posting,
            apply_url=apply,
            posted_at=row.date_posted,
            salary_min=row.salary_min,
            salary_max=row.salary_max,
            salary_currency=(row.currency or None),
            first_seen_at=row.scraped_created_at or now,
            last_seen_at=row.synced_at or now,
            status=JobStatus.ACTIVE,
            is_active=True,
            content_hash=content_hash,
        )
        db.add(job)
        await db.flush()
        return job
    job.title = title
    job.normalized_title = normalize_title(title)
    job.source_id = source.id
    job.company_id = company_id
    job.company_name_raw = company_raw
    job.description = description
    job.requirements_text = _join(requirements)
    job.responsibilities_text = _join(responsibilities)
    job.location_text = location
    job.source_url = posting
    job.apply_url = apply
    job.posted_at = row.date_posted
    job.salary_min = row.salary_min
    job.salary_max = row.salary_max
    job.salary_currency = row.currency or None
    job.last_seen_at = row.synced_at or now
    job.status = JobStatus.ACTIVE
    job.is_active = True
    job.content_hash = content_hash
    job.external_id = identity
    await db.flush()
    return job
