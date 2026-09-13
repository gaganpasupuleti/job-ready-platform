"""Jobs server catalog eligibility and idempotent local upserts."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.db.session import AsyncSessionLocal
from app.models.job import Job, JobApplication, SavedJob
from app.models.job_enums import JobStatus
from app.models.job import JobPublicationDecision
from app.services.jobs_source_sync import (
    SourceJob,
    application_url,
    apply_plan,
    decision_key,
    exclusion_reasons,
    load_publication_decisions,
    plan_sync,
    record_publication_decision,
    source_identity,
)


def _row(**overrides) -> SourceJob:
    payload = dict(
        job_id="CQJ-TEST-QC",
        source="naukri",
        title="Data Engineer",
        company="Infosys",
        location="Hyderabad",
        job_url="https://example.com/jobs/data-engineer",
        apply_url="https://example.com/apply/data-engineer",
        link_status="active",
        approved_status="APPROVED",
        manual_review_needed=False,
        date_posted=datetime(2026, 9, 1, tzinfo=UTC),
        scraped_created_at=datetime(2026, 9, 8, tzinfo=UTC),
        synced_at=datetime(2026, 9, 9, tzinfo=UTC),
        jd_summary=None,
        jd_clean="Build pipelines. Source description only.",
        jd_requirements=["SQL required"],
        jd_responsibilities=["Own the warehouse"],
        required_skills=["sql"],
        actual_role_name="Data Engineer",
        role_family="data-engineer",
        salary_min=Decimal("10"),
        salary_max=Decimal("12"),
        currency="INR",
    )
    payload.update(overrides)
    return SourceJob(**payload)


def test_same_day_source_ids_do_not_share_a_slug():
    from app.services.job_normalization import slugify_job

    first = slugify_job("Pipeline Engineer", "Infosys", "CQJ-20260909-0303".replace("-", "")[-8:])
    second = slugify_job("Pipeline Engineer", "Infosys", "CQJ-20260909-0071".replace("-", "")[-8:])
    assert first != second


def test_job_links_require_https_with_a_host():
    http_only = _row(
        job_id="CQJ-TEST-HTTP",
        apply_url="http://example.com/apply",
        job_url="http://example.com/job",
    )
    assert application_url(http_only) is None
    assert "no_usable_application_url" in exclusion_reasons(http_only, "publish")
    hostless = _row(job_id="CQJ-TEST-HOST", apply_url="https://", job_url="https://")
    assert application_url(hostless) is None
    usable = _row(apply_url="http://example.com/apply", job_url="https://example.com/job")
    assert application_url(usable) == "https://example.com/job"


def test_source_status_alone_does_not_publish():
    pending = _row(job_id="CQJ-TEST-PEND", approved_status="PENDING", manual_review_needed=False)
    approved = _row(job_id="CQJ-TEST-OK", approved_status="APPROVED", manual_review_needed=False)
    qc = _row(
        approved_status="APPROVED",
        manual_review_needed=False,
        title="Walk-in || Qc Inspector",
        company="SRI Bm Tools",
        actual_role_name="QA / Testing Engineer",
        role_family="qa-testing",
        jd_clean="Drawing quality check on the shop floor.",
    )
    assert "no_publication_decision" in exclusion_reasons(pending, None)
    assert "no_publication_decision" in exclusion_reasons(approved, None)
    assert "publication_withheld" in exclusion_reasons(approved, "withhold")
    assert "classification_mismatch" in exclusion_reasons(qc, "publish")
    plan = plan_sync(
        [pending, approved, qc],
        {},
        complete=True,
        decisions={decision_key("naukri", approved.job_id): "publish", decision_key("naukri", qc.job_id): "publish"},
    )
    assert plan.eligible == 1
    assert plan.inserts == [approved]


def test_posted_date_is_not_the_sync_date():
    row = _row()
    assert exclusion_reasons(row, "publish") == []
    assert row.date_posted != row.synced_at
    assert row.date_posted != row.scraped_created_at


def test_incomplete_or_empty_fetch_does_not_archive():
    existing = {"jobs-server:old": uuid4()}
    incomplete = plan_sync([_row(approved_status="PENDING")], existing, complete=False)
    empty = plan_sync([], existing, complete=True)
    assert incomplete.archive_ids == []
    assert empty.archive_ids == []
    with pytest.raises(RuntimeError, match="incomplete"):
        import asyncio

        asyncio.run(apply_plan(None, incomplete))  # type: ignore[arg-type]
    with pytest.raises(RuntimeError, match="empty"):
        import asyncio

        asyncio.run(apply_plan(None, empty))  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_zero_eligible_snapshot_unpublishes_only_owned_jobs():
    owned_key = f"CQJ-OWN-{uuid4().hex[:8]}"
    foreign_id = uuid4()
    async with AsyncSessionLocal() as db:
        created = plan_sync(
            [_row(job_id=owned_key)],
            {},
            complete=True,
            decisions={decision_key("naukri", owned_key): "publish"},
        )
        await apply_plan(db, created)
        owned = (
            await db.execute(select(Job).where(Job.external_id == source_identity(owned_key)))
        ).scalar_one()
        foreign = Job(
            id=foreign_id,
            slug=f"manual-keep-{uuid4().hex[:8]}",
            external_id="manual:keep",
            title="Keep this manual listing",
            normalized_title="keep this manual listing",
            description="Not owned by the jobs server sync.",
            status=JobStatus.ACTIVE,
            is_active=True,
            content_hash=uuid4().hex,
            first_seen_at=datetime.now(UTC),
            last_seen_at=datetime.now(UTC),
        )
        db.add(foreign)
        await db.commit()
        owned_id = owned.id

    snapshot = [
        _row(job_id=owned_key, approved_status="PENDING", manual_review_needed=False),
        _row(job_id="CQJ-OTHER-PENDING", approved_status="NEEDS_REVIEW", manual_review_needed=True),
    ]
    plan = plan_sync(
        snapshot,
        {source_identity(owned_key): owned_id, "jobs-server:missing": foreign_id},
        complete=True,
    )
    assert plan.eligible == 0
    assert plan.seen == 2
    assert owned_id in plan.archive_ids
    assert foreign_id in plan.archive_ids
    async with AsyncSessionLocal() as db:
        result = await apply_plan(db, plan)
        assert result.inserted == 0
        assert result.updated == 0
        assert result.archived == 1
        assert result.skipped_foreign == 1
        stored_owned = await db.get(Job, owned_id)
        stored_foreign = await db.get(Job, foreign_id)
        assert stored_owned is not None and stored_owned.status == JobStatus.ARCHIVED
        assert stored_foreign is not None and stored_foreign.status == JobStatus.ACTIVE
        await db.delete(stored_foreign)
        await db.commit()


@pytest.mark.asyncio
async def test_second_sync_updates_same_job_and_keeps_application(client, student_auth):
    headers, _ = student_auth
    job_key = f"CQJ-TEST-{uuid4().hex[:8]}"
    first = _row(job_id=job_key, title="Pipeline Engineer")
    async with AsyncSessionLocal() as db:
        created = plan_sync(
            [first],
            {},
            complete=True,
            decisions={decision_key("naukri", job_key): "publish"},
        )
        await apply_plan(db, created)
        job = (
            await db.execute(select(Job).where(Job.external_id == source_identity(job_key)))
        ).scalar_one()
        job_id = job.id
        slug = job.slug
        assert job.posted_at == first.date_posted
        assert job.apply_url == first.apply_url
        assert "sql" in (job.requirements_text or "")
        assert "Source role: Data Engineer" in (job.responsibilities_text or "")

    saved = await client.post(f"/api/v1/jobs/{job_id}/save", headers=headers)
    assert saved.status_code == 204, saved.text
    applied = await client.post(f"/api/v1/jobs/{job_id}/apply", headers=headers)
    assert applied.status_code == 200, applied.text
    application_id = applied.json()["id"]

    revised = _row(
        job_id=job_key,
        title="Pipeline Engineer II",
        apply_url="https://example.com/apply/data-engineer-2",
        synced_at=datetime(2026, 9, 10, tzinfo=UTC),
    )
    async with AsyncSessionLocal() as db:
        existing = {source_identity(job_key): job_id}
        again = plan_sync(
            [revised],
            existing,
            complete=True,
            decisions={decision_key("naukri", job_key): "publish"},
        )
        assert len(again.inserts) == 0
        assert len(again.updates) == 1
        await apply_plan(db, again)
        count = await db.scalar(
            select(func.count()).select_from(Job).where(Job.external_id == source_identity(job_key))
        )
        stored = (
            await db.execute(select(Job).where(Job.external_id == source_identity(job_key)))
        ).scalar_one()
        assert count == 1
        assert stored.id == job_id
        assert stored.title == "Pipeline Engineer II"
        assert stored.slug == slug
        assert stored.apply_url == revised.apply_url
        assert stored.posted_at == first.date_posted
        saved_row = (
            await db.execute(select(SavedJob).where(SavedJob.job_id == job_id))
        ).scalar_one()
        app_row = (
            await db.execute(select(JobApplication).where(JobApplication.id == application_id))
        ).scalar_one()
        assert saved_row.job_id == job_id
        assert app_row.job_id == job_id

    pending = _row(job_id=job_key, approved_status="PENDING", manual_review_needed=False)
    async with AsyncSessionLocal() as db:
        withdrawn = plan_sync(
            [pending],
            {source_identity(job_key): job_id},
            complete=True,
            decisions={decision_key("naukri", job_key): "withhold"},
        )
        assert job_id in withdrawn.archive_ids
        result = await apply_plan(db, withdrawn)
        assert result.archived == 1
        assert result.eligible == 0
        assert result.seen == 1
        stored = await db.get(Job, job_id)
        assert stored is not None
        assert stored.status == JobStatus.ARCHIVED
        app_row = await db.get(JobApplication, application_id)
        assert app_row is not None
        assert app_row.job_id == job_id


@pytest.mark.asyncio
async def test_collector_refresh_does_not_erase_or_republish(client, student_auth):
    headers, _ = student_auth
    job_key = f"CQJ-REFRESH-{uuid4().hex[:8]}"
    source_row = _row(
        job_id=job_key,
        approved_status="PENDING",
        manual_review_needed=False,
        title=f"Acceptance {job_key}",
    )
    async with AsyncSessionLocal() as db:
        await record_publication_decision(db, source="naukri", job_id=job_key, decision="publish")
        decisions = await load_publication_decisions(db)
        created = plan_sync([source_row], {}, complete=True, decisions=decisions)
        await apply_plan(db, created)
        job = (
            await db.execute(select(Job).where(Job.external_id == source_identity(job_key)))
        ).scalar_one()
        job_id = job.id

    listed = await client.get("/api/v1/jobs", headers=headers, params={"q": job_key})
    assert listed.status_code == 200
    assert any(item["id"] == str(job_id) for item in listed.json()["items"])
    detail = await client.get(f"/api/v1/jobs/{job_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["apply_url"] == source_row.apply_url
    assert (await client.post(f"/api/v1/jobs/{job_id}/save", headers=headers)).status_code == 204
    applied = await client.post(f"/api/v1/jobs/{job_id}/apply", headers=headers)
    assert applied.status_code == 200
    application_id = applied.json()["id"]

    refreshed = _row(
        job_id=job_key,
        approved_status="NEEDS_REVIEW",
        manual_review_needed=True,
        title="Data Engineer refreshed",
    )
    async with AsyncSessionLocal() as db:
        decisions = await load_publication_decisions(db)
        assert decisions[decision_key("naukri", job_key)] == "publish"
        again = plan_sync([refreshed], {source_identity(job_key): job_id}, complete=True, decisions=decisions)
        await apply_plan(db, again)
        stored = await db.get(Job, job_id)
        assert stored is not None and stored.status == JobStatus.ACTIVE
        assert stored.title == "Data Engineer refreshed"
        assert (await db.get(JobApplication, application_id)).job_id == job_id

    async with AsyncSessionLocal() as db:
        await record_publication_decision(db, source="naukri", job_id=job_key, decision="withhold")
        decisions = await load_publication_decisions(db)
        later = _row(job_id=job_key, approved_status="APPROVED", manual_review_needed=False)
        withheld = plan_sync([later], {source_identity(job_key): job_id}, complete=True, decisions=decisions)
        await apply_plan(db, withheld)
        stored = await db.get(Job, job_id)
        decision = (
            await db.execute(
                select(JobPublicationDecision).where(JobPublicationDecision.source_job_id == job_key)
            )
        ).scalar_one()
        assert stored is not None and stored.status == JobStatus.ARCHIVED
        assert decision.decision == "withhold"
        assert (await db.get(JobApplication, application_id)).job_id == job_id
