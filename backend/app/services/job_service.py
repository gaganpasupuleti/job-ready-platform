"""Student jobs browse, save, apply, recommendations."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppException
from app.models.job import (
    ApplicationStatusHistory,
    Job,
    JobApplication,
    JobRoleMap,
    JobSkill,
    SavedJob,
    UserJobPreference,
)
from app.models.job_enums import ApplicationStatus, JobStatus
from app.models.tagging import Company, JobRole, Skill
from app.models.user import User
from app.schemas.job import (
    ApplicationDetail,
    ApplicationStatusChange,
    ApplicationStatusHistoryItem,
    ApplicationSummary,
    ApplicationUpdate,
    JobCard,
    JobDetail,
    JobListResponse,
    JobPracticeLink,
    JobPreferenceUpdate,
    JobRolePublic,
    JobSkillPublic,
    JobsSummary,
    SavedJobItem,
)
from app.services.job_match_service import JobMatchService
from app.services.job_normalization import validate_url


def _utcnow() -> datetime:
    return datetime.now(UTC)


class JobService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _company_name(self, job: Job) -> str:
        if job.company_id:
            c = await self.db.get(Company, job.company_id)
            if c:
                return c.name
        return job.company_name_raw or "Unknown company"

    async def _company_slug(self, job: Job) -> str | None:
        if job.company_id:
            c = await self.db.get(Company, job.company_id)
            return c.slug if c else None
        return None

    async def _saved_ids(self, user_id: UUID, job_ids: list[UUID]) -> set[UUID]:
        if not job_ids:
            return set()
        rows = (
            await self.db.execute(
                select(SavedJob.job_id).where(
                    SavedJob.user_id == user_id, SavedJob.job_id.in_(job_ids)
                )
            )
        ).scalars().all()
        return set(rows)

    async def _practice_links(self, skill_names: list[str], role_names: list[str]) -> list[JobPracticeLink]:
        links: list[JobPracticeLink] = []
        lower = {s.lower() for s in skill_names}
        if any(s in lower for s in ("sql", "postgresql", "mysql")):
            links.append(JobPracticeLink(label="SQL Practice", path="/practice/sql", reason="SQL skill"))
        if any(s in lower for s in ("python", "dsa")):
            links.append(JobPracticeLink(label="Coding / DSA", path="/practice/coding", reason="Programming"))
        if any(s in lower for s in ("aws", "cloud", "azure", "gcp")):
            links.append(JobPracticeLink(label="Cloud Practice", path="/cloud", reason="Cloud skills"))
        if any(s in lower for s in ("devops", "kubernetes", "terraform")):
            links.append(JobPracticeLink(label="DevOps", path="/devops", reason="DevOps skills"))
        if any(s in lower for s in ("rag", "generative ai", "prompt engineering", "agents")):
            links.append(JobPracticeLink(label="AI Practice", path="/ai", reason="AI skills"))
        if any("data engineer" in r.lower() for r in role_names):
            links.append(
                JobPracticeLink(
                    label="Data Engineering Pack",
                    path="/interviews/packs/data-engineer-intermediate",
                    reason="Role match",
                )
            )
        if not links:
            links.append(JobPracticeLink(label="Practice Hub", path="/practice", reason="General practice"))
        return links

    async def _to_card(self, job: Job, user_id: UUID | None, saved: set[UUID]) -> JobCard:
        skills = (
            await self.db.execute(
                select(Skill.name)
                .join(JobSkill, JobSkill.skill_id == Skill.id)
                .where(JobSkill.job_id == job.id)
                .limit(5)
            )
        ).scalars().all()
        return JobCard(
            id=job.id,
            slug=job.slug,
            title=job.title,
            company_name=await self._company_name(job),
            company_slug=await self._company_slug(job),
            location_text=job.location_text,
            work_mode=job.work_mode,
            employment_type=job.employment_type,
            experience_min_years=job.experience_min_years,
            experience_max_years=job.experience_max_years,
            posted_at=job.posted_at,
            status=job.status,
            is_remote=job.is_remote,
            top_skills=list(skills),
            is_saved=job.id in saved,
        )

    async def list_jobs(
        self,
        user: User,
        *,
        q: str | None = None,
        role: str | None = None,
        skill: str | None = None,
        company: str | None = None,
        city: str | None = None,
        state: str | None = None,
        country: str | None = None,
        remote: bool | None = None,
        work_mode: str | None = None,
        employment_type: str | None = None,
        experience_min: int | None = None,
        posted_within_days: int | None = None,
        sort: str = "newest",
        page: int = 1,
        limit: int = 20,
    ) -> JobListResponse:
        limit = min(max(limit, 1), 50)
        page = max(page, 1)
        stmt = select(Job).where(Job.status == JobStatus.ACTIVE)
        if q:
            pattern = f"%{q.strip()}%"
            stmt = stmt.where(
                or_(
                    Job.title.ilike(pattern),
                    Job.normalized_title.ilike(pattern),
                    Job.description.ilike(pattern),
                    Job.company_name_raw.ilike(pattern),
                )
            )
        if company:
            stmt = stmt.join(Company, Company.id == Job.company_id, isouter=True).where(
                or_(Company.slug == company, Company.name.ilike(f"%{company}%"), Job.company_name_raw.ilike(f"%{company}%"))
            )
        if city:
            stmt = stmt.where(Job.city.ilike(f"%{city}%"))
        if state:
            stmt = stmt.where(Job.state.ilike(f"%{state}%"))
        if country:
            stmt = stmt.where(Job.country.ilike(f"%{country}%"))
        if remote is not None:
            stmt = stmt.where(Job.is_remote.is_(remote))
        if work_mode:
            stmt = stmt.where(Job.work_mode == work_mode)
        if employment_type:
            stmt = stmt.where(Job.employment_type == employment_type)
        if experience_min is not None:
            stmt = stmt.where(
                or_(Job.experience_min_years.is_(None), Job.experience_min_years <= experience_min)
            )
        if posted_within_days:
            cutoff = _utcnow() - timedelta(days=posted_within_days)
            stmt = stmt.where(Job.posted_at.is_not(None), Job.posted_at >= cutoff)
        if role:
            stmt = stmt.join(JobRoleMap, JobRoleMap.job_id == Job.id).join(
                JobRole, JobRole.id == JobRoleMap.role_id
            ).where(or_(JobRole.slug == role, JobRole.name.ilike(f"%{role}%")))
        if skill:
            stmt = stmt.join(JobSkill, JobSkill.job_id == Job.id).join(
                Skill, Skill.id == JobSkill.skill_id
            ).where(or_(Skill.slug == skill, Skill.name.ilike(f"%{skill}%")))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = int(await self.db.scalar(count_stmt) or 0)

        if sort == "oldest":
            stmt = stmt.order_by(Job.posted_at.asc().nullslast(), Job.created_at.asc())
        elif sort == "company":
            stmt = stmt.order_by(Job.company_name_raw.asc().nullslast(), Job.title.asc())
        elif sort == "title":
            stmt = stmt.order_by(Job.title.asc())
        else:
            stmt = stmt.order_by(Job.posted_at.desc().nullslast(), Job.created_at.desc())

        stmt = stmt.offset((page - 1) * limit).limit(limit)
        jobs = (await self.db.execute(stmt)).scalars().unique().all()
        saved = await self._saved_ids(user.id, [j.id for j in jobs])
        items = [await self._to_card(j, user.id, saved) for j in jobs]
        return JobListResponse(items=items, total=total, page=page, limit=limit)

    async def get_job(self, user: User, id_or_slug: str) -> JobDetail:
        job = None
        try:
            uid = UUID(id_or_slug)
            job = await self.db.get(Job, uid)
        except ValueError:
            job = (
                await self.db.execute(select(Job).where(Job.slug == id_or_slug))
            ).scalar_one_or_none()
        if job is None:
            raise AppException("Job not found", status_code=404)

        saved = await self._saved_ids(user.id, [job.id])
        app = (
            await self.db.execute(
                select(JobApplication).where(
                    JobApplication.user_id == user.id, JobApplication.job_id == job.id
                )
            )
        ).scalar_one_or_none()

        skill_rows = (
            await self.db.execute(
                select(Skill, JobSkill.importance)
                .join(JobSkill, JobSkill.skill_id == Skill.id)
                .where(JobSkill.job_id == job.id)
            )
        ).all()
        role_rows = (
            await self.db.execute(
                select(JobRole, JobRoleMap.mapping_source)
                .join(JobRoleMap, JobRoleMap.role_id == JobRole.id)
                .where(JobRoleMap.job_id == job.id)
            )
        ).all()
        skill_names = [s.name for s, _ in skill_rows]
        role_names = [r.name for r, _ in role_rows]
        company_slug = await self._company_slug(job)

        interview_url = "/interviews/session/new"
        if role_names:
            interview_url += f"?role={role_names[0].lower().replace(' ', '-')}"
        company_prep_url = f"/company-prep/{company_slug}" if company_slug else None

        match = await JobMatchService(self.db).match_job(user, job.id)

        source_name = None
        if job.source_id:
            from app.models.job import JobSource
            src = await self.db.get(JobSource, job.source_id)
            source_name = src.name if src else None

        return JobDetail(
            id=job.id,
            slug=job.slug,
            title=job.title,
            company_name=await self._company_name(job),
            company_slug=company_slug,
            company_id=job.company_id,
            description=job.description,
            requirements_text=job.requirements_text,
            responsibilities_text=job.responsibilities_text,
            employment_type=job.employment_type,
            work_mode=job.work_mode,
            experience_min_years=job.experience_min_years,
            experience_max_years=job.experience_max_years,
            salary_min=job.salary_min,
            salary_max=job.salary_max,
            salary_currency=job.salary_currency,
            location_text=job.location_text,
            country=job.country,
            state=job.state,
            city=job.city,
            source_url=job.source_url,
            apply_url=job.apply_url,
            posted_at=job.posted_at,
            expires_at=job.expires_at,
            status=job.status,
            is_remote=job.is_remote,
            source_name=source_name,
            skills=[
                JobSkillPublic(id=s.id, name=s.name, slug=s.slug, importance=imp)
                for s, imp in skill_rows
            ],
            roles=[
                JobRolePublic(id=r.id, name=r.name, slug=r.slug, mapping_source=src.value)
                for r, src in role_rows
            ],
            is_saved=job.id in saved,
            application_id=app.id if app else None,
            application_status=app.status if app else None,
            practice_links=await self._practice_links(skill_names, role_names),
            interview_prep_url=interview_url,
            company_prep_url=company_prep_url,
            match=match,
        )

    async def save_job(self, user: User, job_id: UUID) -> None:
        job = await self.db.get(Job, job_id)
        if job is None:
            raise AppException("Job not found", status_code=404)
        existing = (
            await self.db.execute(
                select(SavedJob).where(SavedJob.user_id == user.id, SavedJob.job_id == job_id)
            )
        ).scalar_one_or_none()
        if existing is None:
            self.db.add(SavedJob(user_id=user.id, job_id=job_id))
            await self.db.commit()

    async def unsave_job(self, user: User, job_id: UUID) -> None:
        row = (
            await self.db.execute(
                select(SavedJob).where(SavedJob.user_id == user.id, SavedJob.job_id == job_id)
            )
        ).scalar_one_or_none()
        if row:
            await self.db.delete(row)
            await self.db.commit()

    async def list_saved(self, user: User) -> list[SavedJobItem]:
        rows = (
            await self.db.execute(
                select(SavedJob, Job)
                .join(Job, Job.id == SavedJob.job_id)
                .where(SavedJob.user_id == user.id)
                .order_by(SavedJob.created_at.desc())
            )
        ).all()
        saved = {job.id for _, job in rows}
        items = []
        for saved_row, job in rows:
            card = await self._to_card(job, user.id, saved)
            items.append(
                SavedJobItem(id=saved_row.id, job_id=job.id, saved_at=saved_row.created_at, job=card)
            )
        return items

    async def recommended(self, user: User, limit: int = 20, sort: str = "coverage") -> JobListResponse:
        if sort == "coverage":
            matcher = JobMatchService(self.db)
            ranked = await matcher.recommended_jobs(user, sort=sort, limit=limit)
            if not ranked:
                return await self.list_jobs(user, sort="newest", page=1, limit=limit)
            job_ids = [UUID(r["job_id"]) for r in ranked]
            jobs = (
                await self.db.execute(select(Job).where(Job.id.in_(job_ids)))
            ).scalars().all()
            job_map = {j.id: j for j in jobs}
            saved = await self._saved_ids(user.id, job_ids)
            items: list[JobCard] = []
            for row in ranked:
                job = job_map.get(UUID(row["job_id"]))
                if job is None:
                    continue
                card = await self._to_card(job, user.id, saved)
                card.requirement_coverage = row.get("coverage")
                card.has_sufficient_mapping = True
                card.missing_skill_count = row.get("missing_skill_count")
                items.append(card)
            return JobListResponse(items=items, total=len(items), page=1, limit=limit)

        pref = (
            await self.db.execute(
                select(UserJobPreference).where(UserJobPreference.user_id == user.id)
            )
        ).scalar_one_or_none()
        if pref and pref.target_role_id:
            role = await self.db.get(JobRole, pref.target_role_id)
            if role:
                return await self.list_jobs(user, role=role.slug, sort="newest", page=1, limit=limit)
        return await self.list_jobs(user, sort="newest", page=1, limit=limit)

    async def mark_applied(self, user: User, job_id: UUID) -> ApplicationDetail:
        job = await self.db.get(Job, job_id)
        if job is None:
            raise AppException("Job not found", status_code=404)
        app = (
            await self.db.execute(
                select(JobApplication).where(
                    JobApplication.user_id == user.id, JobApplication.job_id == job_id
                )
            )
        ).scalar_one_or_none()
        now = _utcnow()
        if app is None:
            app = JobApplication(
                id=uuid4(),
                user_id=user.id,
                job_id=job_id,
                status=ApplicationStatus.APPLIED,
                applied_at=now,
            )
            self.db.add(app)
            await self.db.flush()
            self.db.add(
                ApplicationStatusHistory(
                    application_id=app.id,
                    from_status=None,
                    to_status=ApplicationStatus.APPLIED,
                    note="Marked as applied",
                    changed_at=now,
                    created_by_user_id=user.id,
                )
            )
        else:
            if app.status != ApplicationStatus.APPLIED:
                self.db.add(
                    ApplicationStatusHistory(
                        application_id=app.id,
                        from_status=app.status,
                        to_status=ApplicationStatus.APPLIED,
                        note="Marked as applied",
                        changed_at=now,
                        created_by_user_id=user.id,
                    )
                )
            app.status = ApplicationStatus.APPLIED
            if app.applied_at is None:
                app.applied_at = now
        await self.db.commit()
        return await self.get_application(user, app.id)

    async def summary(self, user: User) -> JobsSummary:
        saved = await self.db.scalar(
            select(func.count()).select_from(SavedJob).where(SavedJob.user_id == user.id)
        )
        apps = (
            await self.db.execute(
                select(JobApplication.status, func.count())
                .where(JobApplication.user_id == user.id)
                .group_by(JobApplication.status)
            )
        ).all()
        counts = {status: int(n) for status, n in apps}
        now = _utcnow()
        today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        follow_due = await self.db.scalar(
            select(func.count()).select_from(JobApplication).where(
                JobApplication.user_id == user.id,
                JobApplication.next_follow_up_at.is_not(None),
                JobApplication.next_follow_up_at <= today_end,
                JobApplication.status.not_in(
                    [ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN, ApplicationStatus.ACCEPTED]
                ),
            )
        )
        overdue = await self.db.scalar(
            select(func.count()).select_from(JobApplication).where(
                JobApplication.user_id == user.id,
                JobApplication.next_follow_up_at.is_not(None),
                JobApplication.next_follow_up_at < now.replace(hour=0, minute=0, second=0),
                JobApplication.status.not_in(
                    [ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN, ApplicationStatus.ACCEPTED]
                ),
            )
        )
        today = await self.db.scalar(
            select(func.count()).select_from(JobApplication).where(
                JobApplication.user_id == user.id,
                JobApplication.next_follow_up_at.is_not(None),
                JobApplication.next_follow_up_at >= now.replace(hour=0, minute=0, second=0),
                JobApplication.next_follow_up_at <= today_end,
            )
        )
        total = sum(counts.values())
        return JobsSummary(
            saved_count=int(saved or 0),
            applications_total=total,
            applied_count=counts.get(ApplicationStatus.APPLIED, 0),
            interview_count=counts.get(ApplicationStatus.INTERVIEW, 0),
            offer_count=counts.get(ApplicationStatus.OFFER, 0) + counts.get(ApplicationStatus.ACCEPTED, 0),
            rejected_count=counts.get(ApplicationStatus.REJECTED, 0),
            follow_ups_due=int(follow_due or 0),
            follow_ups_today=int(today or 0),
            follow_ups_overdue=int(overdue or 0),
        )

    async def update_preference(self, user: User, payload: JobPreferenceUpdate) -> None:
        pref = (
            await self.db.execute(
                select(UserJobPreference).where(UserJobPreference.user_id == user.id)
            )
        ).scalar_one_or_none()
        if pref is None:
            pref = UserJobPreference(id=uuid4(), user_id=user.id)
            self.db.add(pref)
        if payload.target_role_slug:
            role = (
                await self.db.execute(
                    select(JobRole).where(JobRole.slug == payload.target_role_slug)
                )
            ).scalar_one_or_none()
            pref.target_role_id = role.id if role else None
        if payload.preferred_locations is not None:
            pref.preferred_locations_json = payload.preferred_locations
        if payload.remote_preference is not None:
            pref.remote_preference = payload.remote_preference
        await self.db.commit()

    # --- Applications ---

    async def list_applications(self, user: User, status: str | None = None) -> list[ApplicationSummary]:
        stmt = (
            select(JobApplication, Job)
            .join(Job, Job.id == JobApplication.job_id)
            .where(JobApplication.user_id == user.id)
            .order_by(JobApplication.updated_at.desc())
        )
        if status:
            stmt = stmt.where(JobApplication.status == status)
        rows = (await self.db.execute(stmt)).all()
        out = []
        for app, job in rows:
            out.append(
                ApplicationSummary(
                    id=app.id,
                    job_id=job.id,
                    job_title=job.title,
                    company_name=await self._company_name(job),
                    status=app.status,
                    applied_at=app.applied_at,
                    next_follow_up_at=app.next_follow_up_at,
                    priority=app.priority,
                    job_status=job.status,
                )
            )
        return out

    async def get_application(self, user: User, application_id: UUID) -> ApplicationDetail:
        app = await self.db.get(JobApplication, application_id)
        if app is None or app.user_id != user.id:
            raise AppException("Application not found", status_code=404)
        job_detail = await self.get_job(user, str(app.job_id))
        return ApplicationDetail(
            id=app.id,
            job_id=app.job_id,
            status=app.status,
            applied_at=app.applied_at,
            next_follow_up_at=app.next_follow_up_at,
            source_of_application=app.source_of_application,
            application_url=app.application_url,
            notes=app.notes,
            salary_expected=app.salary_expected,
            priority=app.priority,
            created_at=app.created_at,
            updated_at=app.updated_at,
            job=job_detail,
        )

    async def update_application(
        self, user: User, application_id: UUID, payload: ApplicationUpdate
    ) -> ApplicationDetail:
        app = await self.db.get(JobApplication, application_id)
        if app is None or app.user_id != user.id:
            raise AppException("Application not found", status_code=404)
        if payload.application_url:
            payload.application_url = validate_url(payload.application_url)
        if payload.status and payload.status != app.status:
            await self._change_status(app, user, payload.status, None)
        if payload.next_follow_up_at is not None:
            app.next_follow_up_at = payload.next_follow_up_at
        if payload.notes is not None:
            app.notes = payload.notes[:20000]
        if payload.salary_expected is not None:
            app.salary_expected = payload.salary_expected
        if payload.priority is not None:
            app.priority = payload.priority
        if payload.application_url is not None:
            app.application_url = payload.application_url
        if payload.source_of_application is not None:
            app.source_of_application = payload.source_of_application[:120]
        await self.db.commit()
        return await self.get_application(user, application_id)

    async def change_status(
        self, user: User, application_id: UUID, payload: ApplicationStatusChange
    ) -> ApplicationDetail:
        app = await self.db.get(JobApplication, application_id)
        if app is None or app.user_id != user.id:
            raise AppException("Application not found", status_code=404)
        await self._change_status(app, user, payload.to_status, payload.note)
        await self.db.commit()
        return await self.get_application(user, application_id)

    async def _change_status(
        self,
        app: JobApplication,
        user: User,
        to_status: ApplicationStatus,
        note: str | None,
    ) -> None:
        if app.status == to_status:
            return
        now = _utcnow()
        self.db.add(
            ApplicationStatusHistory(
                application_id=app.id,
                from_status=app.status,
                to_status=to_status,
                note=note,
                changed_at=now,
                created_by_user_id=user.id,
            )
        )
        app.status = to_status
        if to_status == ApplicationStatus.APPLIED and app.applied_at is None:
            app.applied_at = now

    async def application_history(
        self, user: User, application_id: UUID
    ) -> list[ApplicationStatusHistoryItem]:
        app = await self.db.get(JobApplication, application_id)
        if app is None or app.user_id != user.id:
            raise AppException("Application not found", status_code=404)
        rows = (
            await self.db.execute(
                select(ApplicationStatusHistory)
                .where(ApplicationStatusHistory.application_id == application_id)
                .order_by(ApplicationStatusHistory.changed_at.asc())
            )
        ).scalars().all()
        return [
            ApplicationStatusHistoryItem(
                id=r.id,
                from_status=r.from_status,
                to_status=r.to_status,
                note=r.note,
                changed_at=r.changed_at,
            )
            for r in rows
        ]

    async def create_application_preparing(self, user: User, job_id: UUID) -> ApplicationDetail:
        job = await self.db.get(Job, job_id)
        if job is None:
            raise AppException("Job not found", status_code=404)
        app = (
            await self.db.execute(
                select(JobApplication).where(
                    JobApplication.user_id == user.id, JobApplication.job_id == job_id
                )
            )
        ).scalar_one_or_none()
        if app is None:
            now = _utcnow()
            app = JobApplication(
                id=uuid4(),
                user_id=user.id,
                job_id=job_id,
                status=ApplicationStatus.PREPARING,
            )
            self.db.add(app)
            await self.db.flush()
            self.db.add(
                ApplicationStatusHistory(
                    application_id=app.id,
                    from_status=None,
                    to_status=ApplicationStatus.PREPARING,
                    note="Started application",
                    changed_at=now,
                    created_by_user_id=user.id,
                )
            )
            await self.db.commit()
        return await self.get_application(user, app.id)
