"""Read-only sync from the Railway Jobs server catalog.

The source is PostgreSQL database `railway`, schema `public`, table
`validated_jobs`. It is not the application's `validated_jobs` table.
Publication requires an application-owned decision of `publish`. Source
PENDING, NEEDS_REVIEW, APPROVED, and PUBLISHED do not publish or withdraw.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from urllib.parse import urlparse
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job, JobPublicationDecision, JobSource
from app.models.job_enums import JobSourceType, JobStatus
from app.models.tagging import Company
from app.services.job_normalization import https_job_url, job_content_hash, normalize_title, slugify_job
from app.services.job_taxonomy import stored_source_value

SOURCE_SLUG_PREFIX = "jobs-server"
EXTERNAL_PREFIX = "jobs-server:"
PUBLISH = "publish"
WITHHOLD = "withhold"
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
    actual_role_id: str | None = None
    experience_bucket: str | None = None


@dataclass(frozen=True)
class ReviewedIdentity:
    source: str
    job_id: str


@dataclass
class SyncPlan:
    complete: bool
    inserts: list[SourceJob] = field(default_factory=list)
    updates: list[tuple[UUID, SourceJob]] = field(default_factory=list)
    exclusions: dict[str, int] = field(default_factory=dict)
    flagged: dict[str, int] = field(default_factory=dict)
    archive_ids: list[UUID] = field(default_factory=list)
    rejected: list[tuple[str, str, str]] = field(default_factory=list)
    eligible: int = 0
    seen: int = 0
    named_only: bool = False


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


def decision_key(source: str, job_id: str) -> str:
    return f"{(source or '').strip().lower()}:{job_id.strip()}"


def database_identity(database_url: str) -> tuple[str, int, str]:
    """Return host, port, and database name. Never include user, password, or query."""
    raw = (database_url or "").strip()
    raw = raw.replace("postgresql+asyncpg://", "postgresql://", 1)
    raw = raw.replace("postgres://", "postgresql://", 1)
    parsed = urlparse(raw)
    database = (parsed.path or "").lstrip("/").split("?")[0]
    host = (parsed.hostname or "").lower()
    if not host or not database or "@" in host:
        raise ValueError("target identity is incomplete")
    return (host, parsed.port or 5432, database)


def format_target_identity(database_url: str) -> str:
    host, port, database = database_identity(database_url)
    return f"host={host} port={port} database={database}"


def parse_target_confirmation(value: str) -> tuple[str, int, str]:
    """Parse host:port/database. A confirmation must not carry credentials."""
    text = (value or "").strip()
    if not text or "@" in text or "://" in text or " " in text:
        raise ValueError("target confirmation must be host:port/database")
    host_port, separator, database = text.partition("/")
    host, port_separator, port_text = host_port.partition(":")
    if not separator or not port_separator or not host or not database or "/" in database:
        raise ValueError("target confirmation must be host:port/database")
    if not port_text.isdigit():
        raise ValueError("target confirmation must be host:port/database")
    return (host.lower(), int(port_text), database)


def assert_application_target(
    *,
    apply_url: str,
    source_url: str,
    application_url: str,
    confirmation: str,
) -> str:
    """Confirm the write target without echoing a DSN, and refuse a swapped source."""
    try:
        confirmed = parse_target_confirmation(confirmation)
        identity = database_identity(apply_url)
    except ValueError as exc:
        raise SystemExit("APPLY_REFUSED target confirmation does not match") from exc
    if confirmed != identity:
        raise SystemExit("APPLY_REFUSED target confirmation does not match")
    if not (application_url or "").strip() or not (source_url or "").strip() or not (apply_url or "").strip():
        raise SystemExit("APPLY_REFUSED application and source targets must both be configured")
    try:
        same_as_source = database_identity(apply_url) == database_identity(source_url)
        source_is_application = database_identity(source_url) == database_identity(application_url)
        apply_is_application = database_identity(apply_url) == database_identity(application_url)
    except ValueError as exc:
        raise SystemExit("APPLY_REFUSED target identity is incomplete") from exc
    if same_as_source:
        raise SystemExit("APPLY_REFUSED target is the Jobs source database")
    if source_is_application:
        raise SystemExit("APPLY_REFUSED source and application targets appear swapped")
    if not apply_is_application:
        raise SystemExit("APPLY_REFUSED apply target is not the application database")
    return format_target_identity(apply_url)


def assert_catalog_roles(
    *,
    apply_has_decisions: bool,
    source_has_validated_jobs: bool,
    source_has_decisions: bool,
) -> None:
    """Refuse a write when the connected catalogs are missing or swapped.

    The application database owns publication decisions. The Jobs source owns
    validated_jobs and must not own those decisions. A leftover validated_jobs
    table on the application database is not itself a swap.
    """
    if source_has_decisions:
        raise SystemExit("APPLY_REFUSED source target has application publication decisions")
    if not source_has_validated_jobs:
        raise SystemExit("APPLY_REFUSED source target has no validated_jobs catalog")
    if not apply_has_decisions:
        raise SystemExit("APPLY_REFUSED application target has no publication decisions")


def named_plan_signature(plan: SyncPlan) -> tuple:
    return (
        tuple((row.source, row.job_id) for row in plan.inserts),
        tuple((str(job_id), row.source, row.job_id) for job_id, row in plan.updates),
        tuple(plan.rejected),
    )


def assert_named_plan_unchanged(reviewed: SyncPlan, current: SyncPlan) -> None:
    if named_plan_signature(reviewed) != named_plan_signature(current):
        raise SystemExit("APPLY_REFUSED eligibility or decisions changed before write")


def parse_reviewed_batch(text: str) -> list[ReviewedIdentity]:
    """Parse source/job_id lines. A reviewed batch is never implied by the catalog."""
    names: list[ReviewedIdentity] = []
    seen: set[tuple[str, str]] = set()
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if "/" not in line:
            raise ValueError(f"reviewed batch line must be source/job_id: {line}")
        source, job_id = line.split("/", 1)
        source = source.strip().lower()
        job_id = job_id.strip()
        if not source or not job_id or "/" in job_id or " " in source or " " in job_id:
            raise ValueError(f"reviewed batch line must be source/job_id: {line}")
        key = (source, job_id)
        if key in seen:
            raise ValueError(f"reviewed batch repeats {source}/{job_id}")
        seen.add(key)
        names.append(ReviewedIdentity(source=source, job_id=job_id))
    if not names:
        raise ValueError("reviewed batch is empty")
    return names


async def load_publication_decisions(db: AsyncSession) -> dict[str, str]:
    rows = (await db.execute(select(JobPublicationDecision))).scalars().all()
    return {decision_key(row.source, row.source_job_id): row.decision for row in rows}


async def record_publication_decision(
    db: AsyncSession,
    *,
    source: str,
    job_id: str,
    decision: str,
) -> None:
    if decision not in {PUBLISH, WITHHOLD}:
        raise ValueError("publication decision must be publish or withhold")
    board = source.strip().lower()
    existing = (
        await db.execute(
            select(JobPublicationDecision).where(
                JobPublicationDecision.source == board,
                JobPublicationDecision.source_job_id == job_id.strip(),
            )
        )
    ).scalar_one_or_none()
    if existing is None:
        db.add(
            JobPublicationDecision(
                id=uuid4(),
                source=board,
                source_job_id=job_id.strip(),
                decision=decision,
            )
        )
    else:
        existing.decision = decision
    await db.commit()


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
    return https_job_url(value)


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


def exclusion_reasons(row: SourceJob, decision: str | None = None) -> list[str]:
    """Content checks plus an application-owned publish decision.

    Source approved_status and manual_review_needed are not this gate. A
    collector refresh can change those fields without a proven preserve rule.
    """
    reasons: list[str] = []
    if decision == WITHHOLD:
        reasons.append("publication_withheld")
    elif decision != PUBLISH:
        reasons.append("no_publication_decision")
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
    decisions: dict[str, str] | None = None,
) -> SyncPlan:
    """decisions is keyed by decision_key(source, job_id). Missing means unpublished."""
    chosen = decisions or {}
    plan = SyncPlan(complete=complete, seen=len(rows))
    seen_identities: set[str] = set()
    for row in rows:
        identity = source_identity(row.job_id)
        seen_identities.add(identity)
        reasons = exclusion_reasons(row, chosen.get(decision_key(row.source, row.job_id)))
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


def plan_named_batch(
    rows: list[SourceJob],
    existing_by_external_id: dict[str, UUID],
    decisions: dict[str, str],
    names: list[ReviewedIdentity],
) -> SyncPlan:
    """Upsert only named identities. A subset is not a complete snapshot.

    Recheck the current decision and content/link rules for each named pair.
    Missing, withheld, expired, or otherwise ineligible names are rejected.
    Unnamed jobs are not archived.
    """
    if not names:
        raise ValueError("reviewed batch is empty")
    by_key = {(row.source.strip().lower(), row.job_id.strip()): row for row in rows}
    plan = SyncPlan(complete=False, named_only=True, seen=len(names))
    for name in names:
        row = by_key.get((name.source, name.job_id))
        if row is None:
            plan.exclusions["named_not_in_source"] = plan.exclusions.get("named_not_in_source", 0) + 1
            plan.rejected.append((name.source, name.job_id, "named_not_in_source"))
            continue
        reasons = exclusion_reasons(row, decisions.get(decision_key(name.source, name.job_id)))
        if classification_mismatch(row):
            plan.flagged["classification_mismatch"] = plan.flagged.get("classification_mismatch", 0) + 1
        if reasons:
            for reason in reasons:
                plan.exclusions[reason] = plan.exclusions.get(reason, 0) + 1
            plan.rejected.append((name.source, name.job_id, ",".join(reasons)))
            continue
        plan.eligible += 1
        existing_id = existing_by_external_id.get(source_identity(name.job_id))
        if existing_id is None:
            plan.inserts.append(row)
        else:
            plan.updates.append((existing_id, row))
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


async def backfill_source_taxonomy(db: AsyncSession, rows: list[SourceJob]) -> int:
    """Copy source taxonomy onto existing jobs. Does not change ids or publication."""
    updated = 0
    for row in rows:
        job = (
            await db.execute(select(Job).where(Job.external_id == source_identity(row.job_id)))
        ).scalar_one_or_none()
        if job is None:
            continue
        values = {
            "role_family": stored_source_value(row.role_family),
            "actual_role_id": stored_source_value(row.actual_role_id),
            "actual_role_name": stored_source_value(row.actual_role_name),
            "experience_bucket": stored_source_value(row.experience_bucket),
        }
        if any(getattr(job, key) != value for key, value in values.items()):
            for key, value in values.items():
                setattr(job, key, value)
            updated += 1
    await db.commit()
    return updated


async def apply_named_plan(db: AsyncSession, plan: SyncPlan) -> ApplyResult:
    """Write only the named inserts and updates. Never archive from a subset."""
    if not plan.named_only or plan.complete:
        raise RuntimeError("refusing to apply a named batch as a complete snapshot")
    if plan.archive_ids:
        raise RuntimeError("refusing to archive from a named batch")
    if plan.seen == 0:
        raise RuntimeError("refusing to apply an empty reviewed batch")
    if not plan.inserts and not plan.updates:
        return ApplyResult(
            inserted=0,
            updated=0,
            archived=0,
            skipped_foreign=0,
            eligible=0,
            seen=plan.seen,
        )
    for row in plan.inserts:
        await _upsert(db, None, row)
    for job_id, row in plan.updates:
        await _upsert(db, job_id, row)
    await db.commit()
    return ApplyResult(
        inserted=len(plan.inserts),
        updated=len(plan.updates),
        archived=0,
        skipped_foreign=0,
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
            slug=slugify_job(title, company, row.job_id.replace("-", "")[-8:]),
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
            role_family=stored_source_value(row.role_family),
            actual_role_id=stored_source_value(row.actual_role_id),
            actual_role_name=stored_source_value(row.actual_role_name),
            experience_bucket=stored_source_value(row.experience_bucket),
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
    job.role_family = stored_source_value(row.role_family)
    job.actual_role_id = stored_source_value(row.actual_role_id)
    job.actual_role_name = stored_source_value(row.actual_role_name)
    job.experience_bucket = stored_source_value(row.experience_bucket)
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
