"""Admin job CRUD, sources, CSV import."""

from __future__ import annotations

import csv
import io
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.job import (
    Job,
    JobIngestionError,
    JobIngestionRun,
    JobLocation,
    JobRoleMap,
    JobSkill,
    JobSource,
)
from app.models.job_enums import (
    IngestionRunStatus,
    JobListingType,
    JobRoleMappingSource,
    JobSkillImportance,
    JobSourceType,
    JobStatus,
)
from app.models.tagging import Company, JobRole, Skill
from app.schemas.job import (
    AdminJobCreate,
    AdminJobUpdate,
    ImportConfirmResponse,
    ImportPreviewResponse,
    ImportPreviewRow,
    IngestionErrorPublic,
    IngestionRunPublic,
    JobCard,
    JobSourcePublic,
)
from app.services.job_normalization import (
    infer_roles,
    job_content_hash,
    normalize_employment_type,
    normalize_title,
    normalize_work_mode,
    parse_csv_skills,
    parse_experience,
    slugify_job,
    validate_url,
    extract_skill_names,
)
from app.services.job_service import JobService


def _utcnow() -> datetime:
    return datetime.now(UTC)


class AdminJobService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.job_svc = JobService(db)

    async def _resolve_company(self, name: str) -> tuple[UUID | None, str]:
        slug = name.lower().replace(" ", "-")
        row = (
            await self.db.execute(
                select(Company).where(
                    (Company.slug == slug) | (func.lower(Company.name) == name.lower().strip())
                )
            )
        ).scalar_one_or_none()
        if row:
            return row.id, row.name
        return None, name.strip()

    async def _skill_map(self) -> dict[str, str]:
        rows = (await self.db.execute(select(Skill))).scalars().all()
        return {s.name.lower(): s.name for s in rows}

    async def _attach_skills(self, job_id: UUID, skill_names: list[str], text: str) -> None:
        known = await self._skill_map()
        names = set(skill_names)
        for name, _ in extract_skill_names(text, known):
            names.add(name)
        for name in names:
            skill = (
                await self.db.execute(
                    select(Skill).where(func.lower(Skill.name) == name.lower())
                )
            ).scalar_one_or_none()
            if not skill:
                continue
            existing = (
                await self.db.execute(
                    select(JobSkill).where(JobSkill.job_id == job_id, JobSkill.skill_id == skill.id)
                )
            ).scalar_one_or_none()
            if not existing:
                self.db.add(
                    JobSkill(
                        job_id=job_id,
                        skill_id=skill.id,
                        importance=JobSkillImportance.MENTIONED,
                    )
                )

    async def _attach_roles(self, job_id: UUID, role_names: list[str], title: str, desc: str) -> None:
        names = set(role_names)
        for name, src in infer_roles(title, desc):
            names.add(name)
        for name in names:
            role = (
                await self.db.execute(
                    select(JobRole).where(func.lower(JobRole.name) == name.lower())
                )
            ).scalar_one_or_none()
            if not role:
                continue
            existing = (
                await self.db.execute(
                    select(JobRoleMap).where(JobRoleMap.job_id == job_id, JobRoleMap.role_id == role.id)
                )
            ).scalar_one_or_none()
            if not existing:
                self.db.add(
                    JobRoleMap(
                        job_id=job_id,
                        role_id=role.id,
                        mapping_source=JobRoleMappingSource.MANUAL,
                    )
                )

    async def list_jobs(self, status: str | None = None, page: int = 1, limit: int = 50) -> dict:
        stmt = select(Job)
        if status:
            stmt = stmt.where(Job.status == status)
        total = int(await self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
        jobs = (
            await self.db.execute(
                stmt.order_by(Job.created_at.desc()).offset((page - 1) * limit).limit(limit)
            )
        ).scalars().all()
        cards = [await self.job_svc._to_card(j, None, set()) for j in jobs]
        return {"items": cards, "total": total, "page": page, "limit": limit}

    async def create_job(self, payload: AdminJobCreate) -> JobCard:
        company_id, company_raw = await self._resolve_company(payload.company_name)
        norm_title = normalize_title(payload.title)
        now = _utcnow()
        slug = slugify_job(payload.title, payload.company_name, str(uuid4())[:8])
        desc = payload.description
        ch = job_content_hash(
            normalized_title=norm_title,
            company=payload.company_name,
            location=payload.location_text,
            description_snippet=desc,
        )
        try:
            apply_url = validate_url(payload.apply_url) if payload.apply_url else None
        except ValueError as exc:
            raise AppException(str(exc), status_code=400) from exc
        try:
            source_url = validate_url(payload.source_url) if payload.source_url else None
        except ValueError as exc:
            raise AppException(str(exc), status_code=400) from exc
        manual = await self._ensure_source("manual", JobSourceType.MANUAL)
        job = Job(
            id=uuid4(),
            slug=slug,
            title=payload.title.strip(),
            normalized_title=norm_title,
            company_id=company_id,
            company_name_raw=company_raw if not company_id else None,
            description=desc,
            requirements_text=payload.requirements_text,
            responsibilities_text=payload.responsibilities_text,
            employment_type=payload.employment_type,
            work_mode=payload.work_mode,
            experience_min_years=payload.experience_min_years,
            experience_max_years=payload.experience_max_years,
            location_text=payload.location_text,
            city=payload.city,
            state=payload.state,
            country=payload.country,
            is_remote=payload.is_remote,
            source_url=source_url,
            apply_url=apply_url,
            posted_at=payload.posted_at,
            expires_at=payload.expires_at,
            first_seen_at=now,
            last_seen_at=now,
            status=payload.status,
            is_active=payload.status == JobStatus.ACTIVE,
            content_hash=ch,
            source_id=manual.id,
        )
        self.db.add(job)
        await self.db.flush()
        await self._attach_skills(job.id, payload.skills, desc)
        await self._attach_roles(job.id, payload.roles, payload.title, desc)
        if payload.location_text or payload.city:
            self.db.add(
                JobLocation(
                    job_id=job.id,
                    location_text=payload.location_text,
                    city=payload.city,
                    state=payload.state,
                    country=payload.country,
                    is_remote=bool(payload.is_remote),
                )
            )
        await self.db.commit()
        return await self.job_svc._to_card(job, None, set())

    async def update_job(self, job_id: UUID, payload: AdminJobUpdate) -> JobCard:
        job = await self.db.get(Job, job_id)
        if job is None:
            raise AppException("Job not found", status_code=404)
        if payload.title:
            job.title = payload.title.strip()
            job.normalized_title = normalize_title(payload.title)
        if payload.company_name:
            cid, raw = await self._resolve_company(payload.company_name)
            job.company_id = cid
            job.company_name_raw = raw if not cid else None
        if payload.description is not None:
            job.description = payload.description
        for field in (
            "requirements_text", "responsibilities_text", "employment_type", "work_mode",
            "experience_min_years", "experience_max_years", "location_text", "city", "state",
            "country", "is_remote", "posted_at", "expires_at",
        ):
            val = getattr(payload, field, None)
            if val is not None:
                setattr(job, field, val)
        if payload.source_url is not None:
            job.source_url = validate_url(payload.source_url) if payload.source_url else None
        if payload.apply_url is not None:
            job.apply_url = validate_url(payload.apply_url) if payload.apply_url else None
        if payload.status is not None:
            job.status = payload.status
            job.is_active = payload.status == JobStatus.ACTIVE
        if payload.skills is not None:
            await self.db.execute(
                JobSkill.__table__.delete().where(JobSkill.job_id == job_id)
            )
            await self._attach_skills(job_id, payload.skills, job.description)
        if payload.roles is not None:
            await self.db.execute(
                JobRoleMap.__table__.delete().where(JobRoleMap.job_id == job_id)
            )
            await self._attach_roles(job_id, payload.roles, job.title, job.description)
        job.last_seen_at = _utcnow()
        await self.db.commit()
        return await self.job_svc._to_card(job, None, set())

    async def archive_job(self, job_id: UUID) -> None:
        job = await self.db.get(Job, job_id)
        if job is None:
            raise AppException("Job not found", status_code=404)
        job.status = JobStatus.ARCHIVED
        job.is_active = False
        await self.db.commit()

    async def list_sources(self) -> list[JobSourcePublic]:
        rows = (await self.db.execute(select(JobSource).order_by(JobSource.name))).scalars().all()
        return [
            JobSourcePublic(
                id=s.id, name=s.name, slug=s.slug, source_type=s.source_type, is_active=s.is_active
            )
            for s in rows
        ]

    async def _ensure_source(self, slug: str, source_type: JobSourceType) -> JobSource:
        row = (
            await self.db.execute(select(JobSource).where(JobSource.slug == slug))
        ).scalar_one_or_none()
        if row:
            return row
        row = JobSource(
            id=uuid4(),
            name=slug.replace("-", " ").title(),
            slug=slug,
            source_type=source_type,
            is_active=True,
        )
        self.db.add(row)
        await self.db.flush()
        return row

    async def list_import_runs(self) -> list[IngestionRunPublic]:
        rows = (
            await self.db.execute(
                select(JobIngestionRun, JobSource)
                .join(JobSource, JobSource.id == JobIngestionRun.source_id, isouter=True)
                .order_by(JobIngestionRun.started_at.desc())
                .limit(50)
            )
        ).all()
        return [
            IngestionRunPublic(
                id=run.id,
                source_id=run.source_id,
                source_name=src.name if src else None,
                started_at=run.started_at,
                completed_at=run.completed_at,
                status=run.status,
                records_seen=run.records_seen,
                records_created=run.records_created,
                records_updated=run.records_updated,
                records_skipped=run.records_skipped,
                records_failed=run.records_failed,
                source_file_name=run.source_file_name,
            )
            for run, src in rows
        ]

    async def import_errors(self, run_id: UUID) -> list[IngestionErrorPublic]:
        rows = (
            await self.db.execute(
                select(JobIngestionError).where(JobIngestionError.run_id == run_id).limit(200)
            )
        ).scalars().all()
        return [
            IngestionErrorPublic(
                id=e.id,
                row_number=e.row_number,
                external_id=e.external_id,
                error_type=e.error_type,
                message=e.message,
            )
            for e in rows
        ]

    _preview_cache: dict[str, list[dict]] = {}

    async def validate_csv(self, content: str, filename: str) -> ImportPreviewResponse:
        rows_out: list[ImportPreviewRow] = []
        create = update = duplicate = errors = 0
        reader = csv.DictReader(io.StringIO(content))
        if not reader.fieldnames:
            raise AppException("CSV has no header row", status_code=400)
        preview_id = str(uuid4())
        staged: list[dict] = []
        for i, row in enumerate(reader, start=2):
            title = (row.get("title") or "").strip()
            company = (row.get("company") or "").strip()
            errs: list[str] = []
            if not title:
                errs.append("title required")
            if not company:
                errs.append("company required")
            desc = (row.get("description") or "").strip()
            if not desc and not (row.get("source_url") or row.get("apply_url")):
                errs.append("description or source URL required")
            listing_raw = (row.get("listing_type") or "").strip().lower()
            if listing_raw in {"real", "career_site"}:
                src = (row.get("source_url") or "").strip()
                app = (row.get("apply_url") or "").strip()
                if not src.startswith(("http://", "https://")) and not app.startswith(
                    ("http://", "https://")
                ):
                    errs.append("real/career_site listings require http(s) source_url or apply_url")
            action = "invalid"
            if not errs:
                norm = normalize_title(title)
                ch = job_content_hash(
                    normalized_title=norm,
                    company=company,
                    location=row.get("location"),
                    description_snippet=desc,
                    external_id=row.get("external_id"),
                    source_slug="csv-import",
                )
                existing = (
                    await self.db.execute(select(Job).where(Job.content_hash == ch))
                ).scalar_one_or_none()
                if existing:
                    action = "duplicate"
                    duplicate += 1
                else:
                    ext = (row.get("external_id") or "").strip()
                    if ext:
                        by_ext = (
                            await self.db.execute(
                                select(Job).where(Job.external_id == ext)
                            )
                        ).scalar_one_or_none()
                        if by_ext:
                            action = "update"
                            update += 1
                        else:
                            action = "new"
                            create += 1
                    else:
                        action = "new"
                        create += 1
                staged.append({"row_number": i, "data": dict(row), "action": action})
            else:
                errors += 1
            rows_out.append(
                ImportPreviewRow(row_number=i, title=title or "—", company=company or "—", action=action, errors=errs)
            )
        AdminJobService._preview_cache[preview_id] = staged
        return ImportPreviewResponse(
            run_id=UUID(preview_id),
            rows=rows_out[:200],
            valid_count=create + update,
            error_count=errors,
            create_count=create,
            update_count=update,
            duplicate_count=duplicate,
        )

    async def confirm_import(self, preview_id: UUID, filename: str | None = None) -> ImportConfirmResponse:
        key = str(preview_id)
        staged = AdminJobService._preview_cache.get(key)
        if not staged:
            raise AppException("Import preview expired — validate again", status_code=400)
        source = await self._ensure_source("csv-import", JobSourceType.IMPORT)
        now = _utcnow()
        run = JobIngestionRun(
            id=uuid4(),
            source_id=source.id,
            started_at=now,
            status=IngestionRunStatus.RUNNING,
            source_file_name=filename,
        )
        self.db.add(run)
        await self.db.flush()
        created = updated = skipped = failed = 0
        for item in staged:
            if item["action"] == "invalid":
                failed += 1
                continue
            if item["action"] == "duplicate":
                skipped += 1
                continue
            row = item["data"]
            try:
                await self._import_row(run.id, row, item["action"], source.id)
                if item["action"] == "update":
                    updated += 1
                else:
                    created += 1
            except Exception as exc:
                failed += 1
                self.db.add(
                    JobIngestionError(
                        run_id=run.id,
                        row_number=item["row_number"],
                        external_id=row.get("external_id"),
                        error_type=type(exc).__name__,
                        message=str(exc)[:500],
                    )
                )
        run.completed_at = _utcnow()
        run.records_seen = len(staged)
        run.records_created = created
        run.records_updated = updated
        run.records_skipped = skipped
        run.records_failed = failed
        run.status = (
            IngestionRunStatus.FAILED if failed and not created and not updated
            else IngestionRunStatus.PARTIAL if failed
            else IngestionRunStatus.COMPLETED
        )
        AdminJobService._preview_cache.pop(key, None)
        await self.db.commit()
        return ImportConfirmResponse(
            run_id=run.id,
            status=run.status,
            records_created=created,
            records_updated=updated,
            records_skipped=skipped,
            records_failed=failed,
        )

    async def _import_row(self, run_id: UUID, row: dict, action: str, source_id: UUID) -> None:
        title = row["title"].strip()
        company = row["company"].strip()
        desc = (row.get("description") or "").strip() or title
        company_id, company_raw = await self._resolve_company(company)
        norm = normalize_title(title)
        loc = (row.get("location") or "").strip() or None
        ext = (row.get("external_id") or "").strip() or None
        ch = job_content_hash(
            normalized_title=norm,
            company=company,
            location=loc,
            description_snippet=desc,
            external_id=ext,
            source_slug="csv-import",
        )
        job = None
        if action == "update" and ext:
            job = (
                await self.db.execute(select(Job).where(Job.external_id == ext))
            ).scalar_one_or_none()
        if job is None:
            job = (
                await self.db.execute(select(Job).where(Job.content_hash == ch))
            ).scalar_one_or_none()
        now = _utcnow()
        exp_min, exp_max = parse_experience(row.get("experience"))
        listing_raw = (row.get("listing_type") or "").strip().lower()
        listing_type = None
        if listing_raw in {e.value for e in JobListingType}:
            listing_type = JobListingType(listing_raw)
        elif "sample" in listing_raw or "demo" in listing_raw:
            listing_type = JobListingType.SAMPLE_DEMO
        elif listing_raw in {"real", "career_site", "curated", "curated_import"}:
            listing_type = (
                JobListingType.REAL
                if listing_raw == "real"
                else JobListingType.CAREER_SITE
                if listing_raw == "career_site"
                else JobListingType.CURATED_IMPORT
            )

        def _parse_dt(val: str | None):
            if not val or not str(val).strip():
                return None
            raw = str(val).strip().replace("Z", "+00:00")
            try:
                dt = datetime.fromisoformat(raw)
                return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
            except ValueError:
                try:
                    return datetime.strptime(raw[:10], "%Y-%m-%d").replace(tzinfo=UTC)
                except ValueError:
                    return None

        posted_at = _parse_dt(row.get("posted_at")) or now
        expires_at = _parse_dt(row.get("expires_at"))
        city = (row.get("city") or "").strip() or None
        state = (row.get("state") or "").strip() or None
        country = (row.get("country") or "").strip() or None
        if job:
            job.title = title
            job.normalized_title = norm
            job.description = desc
            job.last_seen_at = now
            job.content_hash = ch
            job.requirements_text = (row.get("requirements") or "").strip() or job.requirements_text
            job.responsibilities_text = (
                (row.get("responsibilities") or "").strip() or job.responsibilities_text
            )
            job.location_text = loc or job.location_text
            job.city = city or job.city
            job.state = state or job.state
            job.country = country or job.country
            if row.get("source_url"):
                job.source_url = validate_url(row.get("source_url"))
            if row.get("apply_url"):
                job.apply_url = validate_url(row.get("apply_url"))
            if listing_type:
                job.listing_type = listing_type
            if posted_at:
                job.posted_at = posted_at
            if expires_at:
                job.expires_at = expires_at
        else:
            job = Job(
                id=uuid4(),
                slug=slugify_job(title, company, str(uuid4())[:8]),
                external_id=ext,
                source_id=source_id,
                title=title,
                normalized_title=norm,
                company_id=company_id,
                company_name_raw=company_raw if not company_id else None,
                description=desc,
                requirements_text=(row.get("requirements") or "").strip() or None,
                responsibilities_text=(row.get("responsibilities") or "").strip() or None,
                location_text=loc,
                city=city,
                state=state,
                country=country,
                employment_type=normalize_employment_type(row.get("employment_type")),
                work_mode=normalize_work_mode(row.get("work_mode"), None),
                experience_min_years=exp_min,
                experience_max_years=exp_max,
                source_url=validate_url(row.get("source_url")) if row.get("source_url") else None,
                apply_url=validate_url(row.get("apply_url")) if row.get("apply_url") else None,
                posted_at=posted_at,
                expires_at=expires_at,
                first_seen_at=now,
                last_seen_at=now,
                status=JobStatus.ACTIVE,
                is_active=True,
                content_hash=ch,
                listing_type=listing_type or JobListingType.CURATED_IMPORT,
            )
            self.db.add(job)
            await self.db.flush()
        skills = parse_csv_skills(row.get("skills"))
        roles = parse_csv_skills(row.get("role"))
        await self._attach_skills(job.id, skills, desc)
        await self._attach_roles(job.id, roles, title, desc)
