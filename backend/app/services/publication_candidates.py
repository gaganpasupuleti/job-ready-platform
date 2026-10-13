"""Read-only publication candidate planner (PUB-01).

Answers one question: which unpublished catalog jobs would pass the canonical
content gate in jobs_source_sync.exclusion_reasons if an application-owned
publish decision existed. It never records decisions and never writes jobs.
The proposed batch is input for human/product review, not approval.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Awaitable, Callable, Iterable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, date, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.db.session import sqlalchemy_async_url
from app.services.jobs_source_reader import (
    CatalogEntry,
    SourceCatalogSnapshot,
    fetch_source_catalog,
)
from app.services.jobs_source_sync import (
    EXTERNAL_PREFIX,
    PUBLISH,
    WITHHOLD,
    assert_catalog_roles,
    database_identity,
    decision_key,
    exclusion_reasons,
    format_target_identity,
    load_publication_decisions,
    parse_reviewed_batch,
    source_identity,
)

CANDIDATE_NOTICE = (
    "This file contains candidates only. It does not represent publication approval "
    "and cannot by itself create publication decisions."
)
PLANNER_VERSION = "pub-01"
ARTIFACT_PREFIX = "publication_candidates_"
LINK_NOT_ACTIVE = "link_not_active"
# job_publication_decisions.source_job_id is VARCHAR(80).
MAX_DECISION_JOB_ID = 80
# parse_reviewed_batch splits on "/", strips "#" comments, and rejects spaces.
_BATCH_UNSAFE = ("/", "#", " ", "\t", "\r", "\n")
_ACTIVE_STATUS = "active"
_ARCHIVED_STATUS = "archived"

_OWNED_JOBS_SQL = text(
    "SELECT external_id, status, is_active FROM jobs "
    "WHERE external_id LIKE :prefix ORDER BY external_id"
)
_DECISIONS_PRESENT_SQL = text("SELECT to_regclass('public.job_publication_decisions') IS NOT NULL")


class PlanCategory(StrEnum):
    VISIBLE_OR_ALREADY_PUBLISHED = "VISIBLE_OR_ALREADY_PUBLISHED"
    PUBLISH_DECISION_MISSING_CONTENT_ELIGIBLE = "PUBLISH_DECISION_MISSING_CONTENT_ELIGIBLE"
    PUBLISH_DECISION_MISSING_CONTENT_BLOCKED = "PUBLISH_DECISION_MISSING_CONTENT_BLOCKED"
    DECISION_EXISTS_APP_ROW_MISSING = "DECISION_EXISTS_APP_ROW_MISSING"
    WITHHELD = "WITHHELD"
    LINK_INACTIVE = "LINK_INACTIVE"
    IDENTITY_CONFLICT = "IDENTITY_CONFLICT"
    OTHER = "OTHER"


class QualityWarning(StrEnum):
    ROLE_FAMILY_OTHER_REVIEW = "role_family_other_review"
    MANUAL_REVIEW_NEEDED = "manual_review_needed"
    EXPERIENCED_ROLE = "experienced_role"
    MISSING_DATE_POSTED = "missing_date_posted"


@dataclass(frozen=True)
class ApplicationRow:
    external_id: str
    status: str
    is_active: bool


@dataclass(frozen=True)
class ApplicationState:
    decisions: dict[str, str]
    owned_rows: list[ApplicationRow]
    has_publication_decisions: bool


@dataclass(frozen=True)
class Classification:
    category: PlanCategory
    detail: str | None
    content_reasons: tuple[str, ...]


@dataclass(frozen=True)
class PublicationPlan:
    generated_at: datetime
    report: dict[str, Any]
    batch_text: str
    candidate_set_sha256: str


@dataclass(frozen=True)
class PlannerResult:
    report: dict[str, Any]
    batch_path: Path
    report_path: Path


def identity_problem(source: str | None, job_id: str | None) -> str | None:
    """Why a catalog row cannot safely use the jobs-server:<job_id> identity, if at all."""
    job_id = job_id or ""
    board = (source or "").strip()
    if not job_id.strip():
        return "blank_job_id"
    if not board:
        return "blank_source"
    if job_id != job_id.strip():
        return "job_id_surrounding_whitespace"
    if any(char in job_id for char in _BATCH_UNSAFE):
        return "job_id_not_batch_safe"
    if any(char in board for char in _BATCH_UNSAFE):
        return "source_not_batch_safe"
    if len(job_id) > MAX_DECISION_JOB_ID:
        return "job_id_too_long_for_decision"
    return None


def classify(
    entry: CatalogEntry,
    *,
    decision: str | None,
    app_rows: list[ApplicationRow],
    duplicate_job_id: bool,
) -> Classification:
    """Exactly one category per catalog row. Precedence is the order of the checks below."""
    job = entry.job
    content = tuple(exclusion_reasons(job, PUBLISH))
    problem = identity_problem(job.source, job.job_id)
    if problem is None and duplicate_job_id:
        problem = "duplicate_catalog_job_id"
    if problem is None and len(app_rows) > 1:
        problem = "duplicate_application_external_id"
    if problem is not None:
        return Classification(PlanCategory.IDENTITY_CONFLICT, problem, content)
    if LINK_NOT_ACTIVE in content:
        return Classification(PlanCategory.LINK_INACTIVE, None, content)
    if decision == WITHHOLD:
        return Classification(PlanCategory.WITHHELD, None, content)
    app_row = app_rows[0] if app_rows else None
    if decision == PUBLISH:
        if app_row is None:
            return Classification(PlanCategory.DECISION_EXISTS_APP_ROW_MISSING, None, content)
        if app_row.status == _ACTIVE_STATUS and app_row.is_active:
            return Classification(PlanCategory.VISIBLE_OR_ALREADY_PUBLISHED, None, content)
        return Classification(PlanCategory.OTHER, "publish_decision_app_row_not_active", content)
    if decision is not None:
        return Classification(PlanCategory.OTHER, "unrecognized_decision", content)
    if app_row is not None:
        return Classification(PlanCategory.OTHER, "application_row_without_decision", content)
    if content:
        return Classification(PlanCategory.PUBLISH_DECISION_MISSING_CONTENT_BLOCKED, None, content)
    return Classification(PlanCategory.PUBLISH_DECISION_MISSING_CONTENT_ELIGIBLE, None, content)


def batch_line(source: str, job_id: str) -> str:
    """The reviewed-batch form that parse_reviewed_batch reads back unchanged."""
    return f"{source.strip().lower()}/{job_id}"


def candidate_set_sha256(batch_text: str) -> str:
    """SHA-256 of the exact batch file bytes. A fingerprint for drift, not approval."""
    return hashlib.sha256(batch_text.encode("utf-8")).hexdigest()


def quality_warnings(entry: CatalogEntry) -> list[str]:
    job = entry.job
    flags: list[str] = []
    if (job.role_family or "").strip() == "other-review":
        flags.append(QualityWarning.ROLE_FAMILY_OTHER_REVIEW.value)
    if job.manual_review_needed is True:
        flags.append(QualityWarning.MANUAL_REVIEW_NEEDED.value)
    if (job.experience_bucket or "").strip() == "Experienced":
        flags.append(QualityWarning.EXPERIENCED_ROLE.value)
    if job.date_posted is None:
        flags.append(QualityWarning.MISSING_DATE_POSTED.value)
    return flags


def _label(value: Any) -> str:
    if value is None:
        return "(none)"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _when(value: date | datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _sorted_counts(counter: Counter[str]) -> dict[str, int]:
    return {key: counter[key] for key in sorted(counter)}


def _sort_key(entry: CatalogEntry) -> tuple[str, str]:
    return ((entry.job.source or "").strip().lower(), entry.job.job_id or "")


def _candidate_record(entry: CatalogEntry) -> dict[str, Any]:
    job = entry.job
    return {
        "source": (job.source or "").strip().lower(),
        "job_id": job.job_id,
        "title": job.title,
        "company": job.company,
        "role_family": job.role_family,
        "actual_role_name": job.actual_role_name,
        "experience_bucket": job.experience_bucket,
        "approved_status": job.approved_status,
        "manual_review_needed": job.manual_review_needed,
        "has_jd_clean": entry.has_jd_clean,
        "date_posted": _when(job.date_posted),
        "scraped_created_at": _when(job.scraped_created_at),
        "link_status": job.link_status,
        "job_url": job.job_url,
        "apply_url": job.apply_url,
        "warnings": quality_warnings(entry),
    }


def build_publication_plan(
    entries: Iterable[CatalogEntry],
    application: ApplicationState,
    *,
    generated_at: datetime,
    source_target: str,
    application_target: str,
) -> PublicationPlan:
    """Pure planning over a catalog snapshot and application state. Input order does not matter."""
    ordered = sorted(entries, key=_sort_key)
    job_id_counts = Counter((entry.job.job_id or "").strip() for entry in ordered)
    app_by_identity: dict[str, list[ApplicationRow]] = {}
    for row in application.owned_rows:
        app_by_identity.setdefault(row.external_id, []).append(row)

    categories: Counter[str] = Counter({category.value: 0 for category in PlanCategory})
    other_reasons: Counter[str] = Counter()
    identity_conflicts: Counter[str] = Counter()
    content_all: Counter[str] = Counter()
    content_blocked: Counter[str] = Counter()
    published_content: Counter[str] = Counter()
    decision_counts: Counter[str] = Counter(
        {"publish": 0, "withhold": 0, "missing": 0, "unrecognized": 0}
    )
    candidates: list[CatalogEntry] = []
    catalog_identities = {
        source_identity(entry.job.job_id) for entry in ordered if (entry.job.job_id or "").strip()
    }

    for entry in ordered:
        job = entry.job
        usable_id = bool((job.job_id or "").strip())
        decision = (
            application.decisions.get(decision_key(job.source or "", job.job_id))
            if usable_id
            else None
        )
        if decision is None:
            decision_counts["missing"] += 1
        elif decision in (PUBLISH, WITHHOLD):
            decision_counts[decision] += 1
        else:
            decision_counts["unrecognized"] += 1
        identity = source_identity(job.job_id) if usable_id else ""
        result = classify(
            entry,
            decision=decision,
            app_rows=app_by_identity.get(identity, []) if identity else [],
            duplicate_job_id=job_id_counts[(job.job_id or "").strip()] > 1,
        )
        categories[result.category.value] += 1
        content_all.update(result.content_reasons)
        if result.category is PlanCategory.OTHER:
            other_reasons[result.detail or "unspecified"] += 1
        elif result.category is PlanCategory.IDENTITY_CONFLICT:
            identity_conflicts[result.detail or "unspecified"] += 1
        elif result.category is PlanCategory.PUBLISH_DECISION_MISSING_CONTENT_BLOCKED:
            content_blocked.update(result.content_reasons)
        elif result.category is PlanCategory.VISIBLE_OR_ALREADY_PUBLISHED:
            published_content.update(result.content_reasons)
        elif result.category is PlanCategory.PUBLISH_DECISION_MISSING_CONTENT_ELIGIBLE:
            candidates.append(entry)

    candidates.sort(key=_sort_key)
    lines = [batch_line(entry.job.source or "", entry.job.job_id) for entry in candidates]
    batch_text = "".join(f"{line}\n" for line in lines)
    if lines:
        parsed = [f"{name.source}/{name.job_id}" for name in parse_reviewed_batch(batch_text)]
        if parsed != lines:
            raise RuntimeError("candidate batch does not round-trip through parse_reviewed_batch")
    digest = candidate_set_sha256(batch_text)

    records = [_candidate_record(entry) for entry in candidates]
    warnings: Counter[str] = Counter({flag.value: 0 for flag in QualityWarning})
    for record in records:
        warnings.update(record["warnings"])

    owned = application.owned_rows
    statuses = Counter(row.status for row in owned)
    table_decisions = Counter(application.decisions.values())
    report: dict[str, Any] = {
        "notice": CANDIDATE_NOTICE,
        "planner_version": PLANNER_VERSION,
        "generated_at": generated_at.isoformat(),
        "read_only": True,
        "identity_rule": f"application.jobs.external_id = '{EXTERNAL_PREFIX}' + catalog job_id",
        "eligibility": "jobs_source_sync.exclusion_reasons(row, 'publish')",
        "targets": {"source": source_target, "application": application_target},
        "catalog_count": len(ordered),
        "active_catalog_count": sum(
            1 for entry in ordered if LINK_NOT_ACTIVE not in exclusion_reasons(entry.job, PUBLISH)
        ),
        "application": {
            "integration_owned_rows": len(owned),
            "active_rows": statuses.get(_ACTIVE_STATUS, 0),
            "archived_rows": statuses.get(_ARCHIVED_STATUS, 0),
            "other_status_rows": len(owned)
            - statuses.get(_ACTIVE_STATUS, 0)
            - statuses.get(_ARCHIVED_STATUS, 0),
            "owned_rows_without_catalog_job": sum(
                1 for row in owned if row.external_id not in catalog_identities
            ),
        },
        "decisions": {
            **{
                key: decision_counts[key]
                for key in ("publish", "withhold", "missing", "unrecognized")
            },
            "table_total": sum(table_decisions.values()),
            "table_publish": table_decisions.get(PUBLISH, 0),
            "table_withhold": table_decisions.get(WITHHOLD, 0),
        },
        "categories": {category.value: categories[category.value] for category in PlanCategory},
        "other_reasons": _sorted_counts(other_reasons),
        "identity_conflicts": _sorted_counts(identity_conflicts),
        "content_exclusions": _sorted_counts(content_all),
        "content_exclusions_missing_decision": _sorted_counts(content_blocked),
        "content_exclusions_already_published": _sorted_counts(published_content),
        "candidate_breakdown": {
            "by_source": _sorted_counts(Counter(record["source"] for record in records)),
            "by_role_family": _sorted_counts(Counter(_label(r["role_family"]) for r in records)),
            "by_experience_bucket": _sorted_counts(
                Counter(_label(r["experience_bucket"]) for r in records)
            ),
            "by_approved_status": _sorted_counts(
                Counter(_label(r["approved_status"]) for r in records)
            ),
            "by_manual_review_needed": _sorted_counts(
                Counter(_label(r["manual_review_needed"]) for r in records)
            ),
        },
        "quality_warnings": {flag.value: warnings[flag.value] for flag in QualityWarning},
        "candidate_count": len(records),
        "candidate_batch_path": None,
        "candidate_set_sha256": digest,
        "candidates": records,
    }
    return PublicationPlan(
        generated_at=generated_at,
        report=report,
        batch_text=batch_text,
        candidate_set_sha256=digest,
    )


def artifact_paths(output_dir: Path, generated_at: datetime) -> tuple[Path, Path]:
    stamp = generated_at.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    base = output_dir / f"{ARTIFACT_PREFIX}{stamp}"
    return base.with_suffix(".txt"), base.with_suffix(".json")


def write_plan_artifacts(plan: PublicationPlan, output_dir: Path) -> PlannerResult:
    """Write the proposed batch and report as new local files. Never overwrites."""
    output_dir.mkdir(parents=True, exist_ok=True)
    batch_path, report_path = artifact_paths(output_dir, plan.generated_at)
    if batch_path.exists() or report_path.exists():
        raise FileExistsError("planner artifacts already exist")
    report = {**plan.report, "candidate_batch_path": str(batch_path.resolve())}
    with open(batch_path, "xb") as handle:
        handle.write(plan.batch_text.encode("utf-8"))
    with open(report_path, "xb") as handle:
        handle.write((json.dumps(report, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    return PlannerResult(report=report, batch_path=batch_path, report_path=report_path)


@asynccontextmanager
async def read_only_session(database_url: str):
    """An application session whose transaction is verified read-only before any read."""
    engine = create_async_engine(
        sqlalchemy_async_url(database_url), echo=False, hide_parameters=True
    )
    try:
        async with AsyncSession(engine) as db:
            await db.execute(text("SET TRANSACTION READ ONLY"))
            if await db.scalar(text("SHOW transaction_read_only")) != "on":
                raise RuntimeError("application session is not read-only")
            try:
                yield db
            finally:
                await db.rollback()
    finally:
        await engine.dispose()


async def load_application_state(database_url: str) -> ApplicationState:
    async with read_only_session(database_url) as db:
        has_decisions = bool(await db.scalar(_DECISIONS_PRESENT_SQL))
        decisions = await load_publication_decisions(db) if has_decisions else {}
        rows = (await db.execute(_OWNED_JOBS_SQL, {"prefix": f"{EXTERNAL_PREFIX}%"})).all()
    return ApplicationState(
        decisions=decisions,
        owned_rows=[
            ApplicationRow(external_id=external_id, status=str(status), is_active=bool(is_active))
            for external_id, status, is_active in rows
        ],
        has_publication_decisions=has_decisions,
    )


def planner_targets(source_dsn: str, application_dsn: str) -> tuple[str, str]:
    """host/port/database for both targets. Refuses incomplete or identical targets."""
    try:
        source = database_identity(source_dsn)
        application = database_identity(application_dsn)
    except ValueError:
        raise SystemExit("PLAN_REFUSED target identity is incomplete") from None
    if source == application:
        raise SystemExit("PLAN_REFUSED source and application targets are the same database")
    return format_target_identity(source_dsn), format_target_identity(application_dsn)


async def run_publication_planner(
    *,
    source_dsn: str,
    application_dsn: str,
    output_dir: Path,
    now: datetime | None = None,
    fetch_catalog: Callable[[str], Awaitable[SourceCatalogSnapshot]] = fetch_source_catalog,
    load_application: Callable[[str], Awaitable[ApplicationState]] = load_application_state,
) -> PlannerResult:
    source_target, application_target = planner_targets(source_dsn, application_dsn)
    application = await load_application(application_dsn)
    snapshot = await fetch_catalog(source_dsn)
    try:
        assert_catalog_roles(
            apply_has_decisions=application.has_publication_decisions,
            source_has_validated_jobs=snapshot.has_validated_jobs,
            source_has_decisions=snapshot.has_publication_decisions,
        )
    except SystemExit as exc:
        raise SystemExit(str(exc.code).replace("APPLY_REFUSED", "PLAN_REFUSED", 1)) from None
    if not snapshot.entries:
        raise SystemExit("PLAN_REFUSED empty source catalog")
    plan = build_publication_plan(
        snapshot.entries,
        application,
        generated_at=now or datetime.now(UTC),
        source_target=source_target,
        application_target=application_target,
    )
    return write_plan_artifacts(plan, output_dir)


def _counts_line(label: str, counts: dict[str, int]) -> str:
    return f"{label} " + " ".join(f"{key}={value}" for key, value in counts.items())


def summary_lines(result: PlannerResult) -> list[str]:
    report = result.report
    categories = report["categories"]
    decisions = report["decisions"]
    application = report["application"]
    breakdown = report["candidate_breakdown"]
    return [
        f"CATALOG_TOTAL {report['catalog_count']}",
        f"CATALOG_ACTIVE {report['active_catalog_count']}",
        f"APPLICATION_OWNED {application['integration_owned_rows']} "
        f"active={application['active_rows']} archived={application['archived_rows']}",
        f"DECISIONS_PUBLISH {decisions['publish']}",
        f"DECISIONS_WITHHOLD {decisions['withhold']}",
        f"DECISIONS_MISSING {decisions['missing']}",
        *(f"CATEGORY {name} {count}" for name, count in categories.items()),
        f"CONTENT_ELIGIBLE_MISSING_DECISION "
        f"{categories[PlanCategory.PUBLISH_DECISION_MISSING_CONTENT_ELIGIBLE.value]}",
        f"CONTENT_BLOCKED_MISSING_DECISION "
        f"{categories[PlanCategory.PUBLISH_DECISION_MISSING_CONTENT_BLOCKED.value]}",
        _counts_line("BLOCKED_REASONS", report["content_exclusions_missing_decision"]),
        _counts_line("BY_SOURCE", breakdown["by_source"]),
        _counts_line("BY_FAMILY", breakdown["by_role_family"]),
        _counts_line("WARNINGS", report["quality_warnings"]),
        f"CANDIDATE_SET_SHA256 {report['candidate_set_sha256']}",
        f"PROPOSED_BATCH {result.batch_path}",
        f"REPORT {result.report_path}",
        "NOTICE candidates only; not publication approval; creates no decisions",
        "NO_WRITES publication planning only",
    ]
