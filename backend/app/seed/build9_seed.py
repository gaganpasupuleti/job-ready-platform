"""Build 9 seed: job postings, sources, sample saved/application for E2E."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.job import Job, JobApplication, JobRoleMap, JobSkill, JobSource, SavedJob
from app.models.job_enums import ApplicationStatus, JobRoleMappingSource, JobSkillImportance, JobSourceType, JobStatus
from app.models.tagging import Company, JobRole, Skill
from app.models.user import User
from app.services.job_normalization import job_content_hash, normalize_title, slugify_job


JOBS = [
    {
        "slug": "data-engineer-remote-infosys",
        "title": "Data Engineer",
        "company": "Infosys",
        "description": "Build ETL pipelines with Python, SQL, and AWS. Experience with Spark and Airflow preferred.",
        "location": "Remote, India",
        "work_mode": "remote",
        "employment_type": "full_time",
        "experience": "3-5 years",
        "skills": ["Python", "SQL", "AWS", "Spark"],
        "roles": ["Data Engineer"],
        "is_remote": True,
        "apply_url": "https://example.com/jobs/data-engineer-infosys",
    },
    {
        "slug": "data-analyst-hybrid-accenture",
        "title": "Data Analyst",
        "company": "Accenture",
        "description": "Analyze business data with SQL and Power BI. Create dashboards for stakeholders.",
        "location": "Bengaluru, Karnataka",
        "work_mode": "hybrid",
        "employment_type": "full_time",
        "experience": "2-4 years",
        "skills": ["SQL", "Power BI"],
        "roles": ["Data Analyst"],
        "is_remote": False,
    },
    {
        "slug": "python-developer-onsite-tcs",
        "title": "Python Developer",
        "company": "TCS",
        "description": "Develop backend APIs with Python and REST. Knowledge of PostgreSQL required.",
        "location": "Hyderabad, Telangana",
        "work_mode": "onsite",
        "employment_type": "full_time",
        "experience": "2+ years",
        "skills": ["Python", "SQL"],
        "roles": ["Python Developer"],
        "is_remote": False,
    },
    {
        "slug": "devops-engineer-cognizant",
        "title": "DevOps Engineer",
        "company": "Cognizant",
        "description": "Manage Kubernetes clusters, Terraform, and CI/CD pipelines on AWS.",
        "location": "Pune, Maharashtra",
        "work_mode": "hybrid",
        "skills": ["DevOps", "AWS", "Kubernetes", "Terraform"],
        "roles": ["DevOps Engineer"],
        "experience": "4+ years",
    },
    {
        "slug": "genai-engineer-capgemini",
        "title": "GenAI Engineer",
        "company": "Capgemini",
        "description": "Build RAG assistants and agent workflows with Python. Prompt engineering experience.",
        "location": "Remote",
        "work_mode": "remote",
        "skills": ["Python", "RAG", "Generative AI"],
        "roles": ["GenAI Engineer"],
        "is_remote": True,
    },
    {
        "slug": "soc-analyst-deloitte",
        "title": "SOC Analyst",
        "company": "Deloitte",
        "description": "Monitor SIEM alerts, triage incidents, and document security investigations.",
        "location": "Mumbai, Maharashtra",
        "work_mode": "onsite",
        "skills": ["SOC"],
        "roles": ["SOC Analyst"],
        "experience": "1-3 years",
    },
    {
        "slug": "ml-engineer-remote",
        "title": "ML Engineer",
        "company": "TechCorp",
        "description": "Train and deploy models with Python and AWS. MLOps exposure helpful.",
        "location": "Remote",
        "work_mode": "remote",
        "skills": ["Python", "AWS"],
        "roles": ["AI Engineer"],
        "is_remote": True,
    },
    {
        "slug": "sql-developer-onsite",
        "title": "SQL Developer",
        "company": "Acme Labs",
        "description": "Optimize queries, design schemas, and support analytics workloads in PostgreSQL.",
        "location": "Chennai, Tamil Nadu",
        "work_mode": "onsite",
        "skills": ["SQL"],
        "roles": ["SQL Developer"],
    },
]


async def _ensure_source(session, slug: str, source_type: JobSourceType) -> JobSource:
    row = (await session.execute(select(JobSource).where(JobSource.slug == slug))).scalar_one_or_none()
    if row:
        return row
    row = JobSource(
        id=uuid4(),
        name=slug.replace("-", " ").title(),
        slug=slug,
        source_type=source_type,
        is_active=True,
    )
    session.add(row)
    await session.flush()
    return row


async def _company(session, name: str) -> Company | None:
    slug = name.lower().replace(" ", "-")
    row = (await session.execute(select(Company).where(Company.slug == slug))).scalar_one_or_none()
    return row


async def _skill(session, name: str) -> Skill | None:
    slug = name.lower().replace(" ", "-")
    return (await session.execute(select(Skill).where(Skill.slug == slug))).scalar_one_or_none()


async def _role(session, name: str) -> JobRole | None:
    slug = name.lower().replace(" ", "-")
    return (await session.execute(select(JobRole).where(JobRole.slug == slug))).scalar_one_or_none()


async def seed_build9_jobs() -> None:
    async with AsyncSessionLocal() as session:
        manual = await _ensure_source(session, "manual", JobSourceType.MANUAL)
        now = datetime.now(UTC)
        job_ids: list[tuple[str, Job]] = []

        for item in JOBS:
            existing = (
                await session.execute(select(Job).where(Job.slug == item["slug"]))
            ).scalar_one_or_none()
            company = await _company(session, item["company"])
            norm = normalize_title(item["title"])
            desc = item["description"]
            ch = job_content_hash(
                normalized_title=norm,
                company=item["company"],
                location=item.get("location"),
                description_snippet=desc,
                source_slug="manual",
            )
            if existing:
                job = existing
                job.description = desc
                job.status = JobStatus.ACTIVE
                job.is_active = True
                job.last_seen_at = now
            else:
                from app.services.job_normalization import normalize_employment_type, normalize_work_mode, parse_experience

                exp_min, exp_max = parse_experience(item.get("experience"))
                job = Job(
                    id=uuid4(),
                    slug=item["slug"],
                    title=item["title"],
                    normalized_title=norm,
                    company_id=company.id if company else None,
                    company_name_raw=item["company"] if not company else None,
                    description=desc,
                    location_text=item.get("location"),
                    work_mode=normalize_work_mode(item.get("work_mode"), item.get("is_remote")),
                    employment_type=normalize_employment_type(item.get("employment_type")),
                    experience_min_years=exp_min,
                    experience_max_years=exp_max,
                    is_remote=item.get("is_remote"),
                    apply_url=item.get("apply_url"),
                    posted_at=now - timedelta(days=3),
                    first_seen_at=now,
                    last_seen_at=now,
                    status=JobStatus.ACTIVE,
                    is_active=True,
                    content_hash=ch,
                    source_id=manual.id,
                )
                session.add(job)
                await session.flush()

            for skill_name in item.get("skills", []):
                skill = await _skill(session, skill_name)
                if not skill:
                    continue
                link = (
                    await session.execute(
                        select(JobSkill).where(JobSkill.job_id == job.id, JobSkill.skill_id == skill.id)
                    )
                ).scalar_one_or_none()
                if not link:
                    session.add(
                        JobSkill(job_id=job.id, skill_id=skill.id, importance=JobSkillImportance.MENTIONED)
                    )
            for role_name in item.get("roles", []):
                role = await _role(session, role_name)
                if not role:
                    continue
                link = (
                    await session.execute(
                        select(JobRoleMap).where(JobRoleMap.job_id == job.id, JobRoleMap.role_id == role.id)
                    )
                ).scalar_one_or_none()
                if not link:
                    session.add(
                        JobRoleMap(
                            job_id=job.id,
                            role_id=role.id,
                            mapping_source=JobRoleMappingSource.RULE,
                        )
                    )
            job_ids.append((item["slug"], job))

        # Upgrade legacy acme-data-engineer stub if present
        legacy = (
            await session.execute(select(Job).where(Job.slug == "acme-data-engineer"))
        ).scalar_one_or_none()
        if legacy:
            legacy.description = legacy.description or "Data engineering role at Acme Labs."
            legacy.normalized_title = normalize_title(legacy.title)
            legacy.status = JobStatus.ACTIVE
            legacy.is_active = True
            legacy.first_seen_at = legacy.first_seen_at or now
            legacy.last_seen_at = now
            if not legacy.content_hash:
                legacy.content_hash = job_content_hash(
                    normalized_title=legacy.normalized_title,
                    company="Acme Labs",
                    location=None,
                    description_snippet=legacy.description,
                )
            legacy.source_id = manual.id

        # E2E student saved job + application
        student = (
            await session.execute(select(User).where(User.email == "e2e.student@jobready.dev"))
        ).scalar_one_or_none()
        if student and job_ids:
            target_job = job_ids[0][1]
            saved = (
                await session.execute(
                    select(SavedJob).where(SavedJob.user_id == student.id, SavedJob.job_id == target_job.id)
                )
            ).scalar_one_or_none()
            if not saved:
                session.add(SavedJob(id=uuid4(), user_id=student.id, job_id=target_job.id))
            app = (
                await session.execute(
                    select(JobApplication).where(
                        JobApplication.user_id == student.id,
                        JobApplication.job_id == job_ids[1][1].id,
                    )
                )
            ).scalar_one_or_none()
            if not app:
                session.add(
                    JobApplication(
                        id=uuid4(),
                        user_id=student.id,
                        job_id=job_ids[1][1].id,
                        status=ApplicationStatus.SCREENING,
                        applied_at=now - timedelta(days=5),
                        next_follow_up_at=now + timedelta(days=1),
                    )
                )

        await session.commit()


if __name__ == "__main__":
    import asyncio

    asyncio.run(seed_build9_jobs())
