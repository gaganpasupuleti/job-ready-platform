"""Family counts and combined catalog filters."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.job import Job, JobSkill
from app.models.job_enums import JobSkillImportance, JobStatus
from app.models.tagging import Skill
from app.services.job_taxonomy import catalog_text, stored_source_value
from app.services.jobs_source_sync import ReviewedIdentity, SourceJob, apply_named_plan, plan_named_batch
from tests.test_jobs_source_sync import _row


def test_source_taxonomy_is_not_inferred():
    assert catalog_text("nan") is None
    assert catalog_text("  ") is None
    assert stored_source_value("Fresher") == "Fresher"
    assert stored_source_value(None) is None
    titled_like_java = SourceJob(
        job_id="CQJ-FAMILY",
        source="indeed",
        title="Java Backend Developer",
        company="Example",
        location="Hyderabad",
        job_url="https://example.com/job",
        apply_url="https://example.com/apply",
        link_status="active",
        approved_status="NEEDS_REVIEW",
        manual_review_needed=True,
        date_posted=None,
        scraped_created_at=None,
        synced_at=None,
        jd_summary=None,
        jd_clean="Source description",
        jd_requirements=[],
        jd_responsibilities=[],
        required_skills=[],
        actual_role_name=None,
        role_family=None,
    )
    assert stored_source_value(titled_like_java.role_family) is None
    assert stored_source_value(titled_like_java.experience_bucket) is None


@pytest.mark.asyncio
async def test_named_sync_keeps_source_taxonomy_without_guessing():
    job_id = f"CQJ-TAX-{uuid4().hex[:8]}"
    row = _row(
        job_id=job_id,
        source="indeed",
        title="Java Backend Developer",
        role_family="python-dev",
        actual_role_id="ROLE_PYTHON_DEV",
        actual_role_name="Python Developer",
        experience_bucket="Internship",
    )
    plan = plan_named_batch(
        [row],
        {},
        {f"indeed:{job_id}": "publish"},
        [ReviewedIdentity("indeed", job_id)],
    )
    async with AsyncSessionLocal() as db:
        await apply_named_plan(db, plan)
        stored = (
            await db.execute(select(Job).where(Job.external_id == f"jobs-server:{job_id}"))
        ).scalar_one()
        assert stored.role_family == "python-dev"
        assert stored.actual_role_id == "ROLE_PYTHON_DEV"
        assert stored.actual_role_name == "Python Developer"
        assert stored.experience_bucket == "Internship"
        assert stored.title == "Java Backend Developer"


def _job(**overrides) -> Job:
    now = datetime.now(UTC)
    suffix = uuid4().hex[:8]
    payload = dict(
        slug=f"family-filter-{suffix}",
        title="Family filter role",
        normalized_title="family filter role",
        description="Source description for the filter fixture.",
        status=JobStatus.ACTIVE,
        is_active=True,
        content_hash=uuid4().hex,
        first_seen_at=now,
        last_seen_at=now,
        company_name_raw="Filter Co",
        location_text="Filter City",
        role_family="data-engineer",
        experience_bucket="Experienced",
    )
    payload.update(overrides)
    return Job(**payload)


@pytest.mark.asyncio
async def test_family_counts_ignore_selected_family_and_page(client, student_auth):
    headers, _ = student_auth
    token = uuid4().hex[:8]
    location = f"Filter City {token}"
    company = f"Filter Co {token}"
    async with AsyncSessionLocal() as db:
        page_jobs = [
            _job(
                title=f"Engineer {index}",
                company_name_raw=company,
                location_text=location,
                role_family="data-engineer",
                experience_bucket="Experienced",
            )
            for index in range(21)
        ]
        analyst = _job(
            title="Analyst only",
            company_name_raw=company,
            location_text=location,
            role_family="data-analyst",
            experience_bucket="Fresher",
        )
        unknown = _job(
            title="Unmapped posting",
            company_name_raw=company,
            location_text=location,
            role_family="not-a-family",
            experience_bucket=None,
        )
        other = _job(
            title="Needs review",
            company_name_raw=company,
            location_text=location,
            role_family="other-review",
            experience_bucket="Entry (1-2 yrs)",
        )
        placeholder = _job(
            title="Placeholder company",
            company_name_raw="nan",
            location_text="nan",
            role_family="python-dev",
            experience_bucket="nan",
        )
        db.add_all([*page_jobs, analyst, unknown, other, placeholder])
        await db.flush()
        skill_job = page_jobs[0]
        sql = Skill(name=f"SQL {token}", slug=f"sql-{token}")
        nosql = Skill(name=f"NoSQL {token}", slug=f"nosql-{token}")
        db.add_all([sql, nosql])
        await db.flush()
        db.add_all(
            [
                JobSkill(job_id=skill_job.id, skill_id=sql.id, importance=JobSkillImportance.REQUIRED),
                JobSkill(job_id=skill_job.id, skill_id=nosql.id, importance=JobSkillImportance.MENTIONED),
            ]
        )
        await db.commit()

    listed = await client.get(
        "/api/v1/jobs",
        headers=headers,
        params={
            "company": company,
            "location": location,
            "experience_bucket": "Experienced",
            "role_family": "data-engineer",
            "page": 2,
            "limit": 20,
        },
    )
    assert listed.status_code == 200, listed.text
    body = listed.json()
    assert body["total"] == 21
    assert len(body["items"]) == 1
    assert body["page"] == 2
    assert all(item["experience_bucket"] == "Experienced" for item in body["items"])

    counts = await client.get(
        "/api/v1/jobs/family-counts",
        headers=headers,
        params={"company": company, "location": location},
    )
    assert counts.status_code == 200, counts.text
    payload = counts.json()
    by_id = {row["id"]: row["count"] for row in payload["families"]}
    assert payload["all"] == 24
    assert by_id["data-engineer"] == 21
    assert by_id["data-analyst"] == 1
    assert by_id["other-review"] == 1
    assert by_id["python-dev"] == 0
    assert "not-a-family" not in by_id
    assert sum(by_id.values()) == 23

    skilled = await client.get(
        "/api/v1/jobs/family-counts",
        headers=headers,
        params={"company": company, "location": location, "skill": f"sql-{token}"},
    )
    assert skilled.status_code == 200, skilled.text
    assert skilled.json()["all"] == 1

    options = await client.get(
        "/api/v1/jobs/filter-options",
        headers=headers,
        params={"company_q": token, "location_q": token},
    )
    assert options.status_code == 200, options.text
    choices = options.json()
    assert company in choices["companies"]
    assert location in choices["locations"]
    assert "nan" not in choices["companies"]
    assert "nan" not in choices["locations"]
    assert "Fresher" in choices["experience_buckets"]
    assert None not in choices["experience_buckets"]
