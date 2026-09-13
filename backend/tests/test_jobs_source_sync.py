"""Jobs server catalog eligibility and idempotent local upserts."""

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.db.session import AsyncSessionLocal
from app.models.job import Job, JobApplication, SavedJob
from app.models.job_enums import ApplicationStatus, JobStatus
from app.models.job import JobPublicationDecision
from app.services.jobs_source_sync import (
    ReviewedIdentity,
    SourceJob,
    SyncPlan,
    application_url,
    apply_named_plan,
    apply_plan,
    assert_application_target,
    assert_catalog_roles,
    assert_named_plan_unchanged,
    database_identity,
    decision_key,
    exclusion_reasons,
    format_target_identity,
    load_publication_decisions,
    parse_reviewed_batch,
    parse_target_confirmation,
    plan_named_batch,
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


def test_reviewed_batch_parser_requires_pairs():
    names = parse_reviewed_batch("indeed/CQJ-1\n# note\n\nnaukri/CQJ-2\n")
    assert names == [
        ReviewedIdentity("indeed", "CQJ-1"),
        ReviewedIdentity("naukri", "CQJ-2"),
    ]
    with pytest.raises(ValueError, match="empty"):
        parse_reviewed_batch("# only a comment\n")
    with pytest.raises(ValueError, match="repeats"):
        parse_reviewed_batch("indeed/CQJ-1\nindeed/CQJ-1\n")


def test_named_plan_is_not_a_complete_snapshot():
    keep = uuid4()
    other = uuid4()
    accepted = _row(job_id="CQJ-KEEP", source="indeed")
    expired = _row(job_id="CQJ-OLD", source="indeed", link_status="expired")
    unpublished = _row(job_id="CQJ-NONE", source="indeed")
    withheld = _row(job_id="CQJ-HOLD", source="indeed")
    plan = plan_named_batch(
        [accepted, expired, unpublished, withheld, _row(job_id="CQJ-OUT", source="indeed")],
        {
            source_identity("CQJ-KEEP"): keep,
            source_identity("CQJ-OUT"): other,
        },
        {
            decision_key("indeed", "CQJ-KEEP"): "publish",
            decision_key("indeed", "CQJ-OLD"): "publish",
            decision_key("indeed", "CQJ-HOLD"): "withhold",
        },
        [
            ReviewedIdentity("indeed", "CQJ-KEEP"),
            ReviewedIdentity("indeed", "CQJ-OLD"),
            ReviewedIdentity("indeed", "CQJ-NONE"),
            ReviewedIdentity("indeed", "CQJ-HOLD"),
            ReviewedIdentity("indeed", "CQJ-MISSING"),
        ],
    )
    assert plan.named_only is True
    assert plan.complete is False
    assert plan.archive_ids == []
    assert plan.eligible == 1
    assert plan.updates == [(keep, accepted)]
    assert plan.inserts == []
    assert other not in plan.archive_ids
    rejected = {job_id: reasons for _source, job_id, reasons in plan.rejected}
    assert "link_not_active" in rejected["CQJ-OLD"]
    assert "no_publication_decision" in rejected["CQJ-NONE"]
    assert "publication_withheld" in rejected["CQJ-HOLD"]
    assert rejected["CQJ-MISSING"] == "named_not_in_source"


@pytest.mark.asyncio
async def test_named_batch_rerun_keeps_ids_and_rejects_unpublished(client, student_auth):
    headers, _ = student_auth
    accepted_key = f"CQJ-NAMED-{uuid4().hex[:8]}"
    withheld_key = f"CQJ-HOLD-{uuid4().hex[:8]}"
    foreign_id = uuid4()
    other_owned_key = f"CQJ-OTHER-{uuid4().hex[:8]}"
    names = [
        ReviewedIdentity("indeed", accepted_key),
        ReviewedIdentity("indeed", withheld_key),
        ReviewedIdentity("indeed", "CQJ-EXPIRED"),
        ReviewedIdentity("indeed", "CQJ-UNREVIEWED"),
    ]
    rows = [
        _row(job_id=accepted_key, source="indeed", title="Named role"),
        _row(job_id=withheld_key, source="indeed"),
        _row(job_id="CQJ-EXPIRED", source="indeed", link_status="expired"),
        _row(job_id="CQJ-UNREVIEWED", source="indeed"),
        _row(job_id=other_owned_key, source="indeed", title="Leave this owned row"),
    ]
    async with AsyncSessionLocal() as db:
        await record_publication_decision(db, source="indeed", job_id=accepted_key, decision="publish")
        await record_publication_decision(db, source="indeed", job_id=withheld_key, decision="withhold")
        await record_publication_decision(db, source="indeed", job_id="CQJ-EXPIRED", decision="publish")
        other = plan_sync(
            [_row(job_id=other_owned_key, source="indeed")],
            {},
            complete=True,
            decisions={decision_key("indeed", other_owned_key): "publish"},
        )
        await apply_plan(db, other)
        other_job = (
            await db.execute(select(Job).where(Job.external_id == source_identity(other_owned_key)))
        ).scalar_one()
        other_id = other_job.id
        foreign = Job(
            id=foreign_id,
            slug=f"catalog-keep-{uuid4().hex[:8]}",
            external_id=None,
            title="Unrelated catalog listing",
            normalized_title="unrelated catalog listing",
            description="Not a jobs-server identity.",
            status=JobStatus.ACTIVE,
            is_active=True,
            content_hash=uuid4().hex,
            first_seen_at=datetime.now(UTC),
            last_seen_at=datetime.now(UTC),
        )
        db.add(foreign)
        await db.commit()
        decisions = await load_publication_decisions(db)
        first = plan_named_batch(
            rows,
            {source_identity(other_owned_key): other_id},
            decisions,
            names,
        )
        assert first.archive_ids == []
        assert len(first.inserts) == 1
        await apply_named_plan(db, first)
        created = (
            await db.execute(select(Job).where(Job.external_id == source_identity(accepted_key)))
        ).scalar_one()
        created_id = created.id
        hold = (
            await db.execute(select(Job).where(Job.external_id == source_identity(withheld_key)))
        ).scalar_one_or_none()
        assert hold is None

    saved = await client.post(f"/api/v1/jobs/{created_id}/save", headers=headers)
    assert saved.status_code == 204, saved.text
    applied = await client.post(f"/api/v1/jobs/{created_id}/apply", headers=headers)
    assert applied.status_code == 200, applied.text
    application_id = applied.json()["id"]
    async with AsyncSessionLocal() as db:
        owned = await db.get(JobApplication, application_id)
        assert owned is not None
        catalog_application = JobApplication(
            user_id=owned.user_id,
            job_id=foreign_id,
            status=ApplicationStatus.APPLIED,
        )
        other_application = JobApplication(
            user_id=owned.user_id,
            job_id=other_id,
            status=ApplicationStatus.APPLIED,
        )
        db.add(catalog_application)
        db.add(other_application)
        await db.commit()
        catalog_application_id = catalog_application.id
        other_application_id = other_application.id

    revised = _row(
        job_id=accepted_key,
        source="indeed",
        title="Named role revised",
        apply_url="https://example.com/apply/named-revised",
    )
    async with AsyncSessionLocal() as db:
        decisions = await load_publication_decisions(db)
        assert decisions[decision_key("indeed", withheld_key)] == "withhold"
        again = plan_named_batch(
            [revised, *rows[1:]],
            {
                source_identity(accepted_key): created_id,
                source_identity(other_owned_key): other_id,
            },
            decisions,
            names,
        )
        assert again.inserts == []
        assert len(again.updates) == 1
        assert again.archive_ids == []
        await apply_named_plan(db, again)
        stored = await db.get(Job, created_id)
        assert stored is not None
        assert stored.id == created_id
        assert stored.title == "Named role revised"
        assert stored.status == JobStatus.ACTIVE
        preserved = await db.get(JobApplication, application_id)
        assert preserved is not None
        assert str(preserved.id) == str(application_id)
        assert preserved.job_id == created_id
        catalog_application_row = await db.get(JobApplication, catalog_application_id)
        other_application_row = await db.get(JobApplication, other_application_id)
        assert catalog_application_row is not None and catalog_application_row.job_id == foreign_id
        assert other_application_row is not None and other_application_row.job_id == other_id
        assert (
            await db.execute(select(SavedJob).where(SavedJob.job_id == created_id))
        ).scalar_one().job_id == created_id
        untouched = await db.get(Job, other_id)
        catalog = await db.get(Job, foreign_id)
        assert untouched is not None and untouched.id == other_id and untouched.status == JobStatus.ACTIVE
        assert catalog is not None and catalog.id == foreign_id and catalog.is_active is True
        expired = (
            await db.execute(select(Job).where(Job.external_id == source_identity("CQJ-EXPIRED")))
        ).scalar_one_or_none()
        assert expired is None

    stale = SyncPlan(complete=True, named_only=True, seen=1)
    with pytest.raises(RuntimeError, match="complete snapshot"):
        await apply_named_plan(None, stale)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_rejected_named_batch_does_not_write():
    plan = SyncPlan(
        complete=False,
        named_only=True,
        seen=1,
        rejected=[("indeed", "CQJ-UNREVIEWED", "no_publication_decision")],
    )
    result = await apply_named_plan(None, plan)  # type: ignore[arg-type]
    assert result.inserted == 0
    assert result.updated == 0
    assert result.archived == 0


def test_target_confirmation_rejects_swap_without_leaking_credentials():
    secret = "batch-importer-secret"
    apply_url = f"postgresql://appuser:{secret}@app.internal:5432/jobready_db"
    source_url = f"postgresql://source:{secret}@source.internal:5432/railway"
    application_url = f"postgresql://appuser:{secret}@app.internal:5432/jobready_db"
    assert database_identity(apply_url) == ("app.internal", 5432, "jobready_db")
    assert secret not in format_target_identity(apply_url)
    identity = assert_application_target(
        apply_url=apply_url,
        source_url=source_url,
        application_url=application_url,
        confirmation="app.internal:5432/jobready_db",
    )
    assert identity == "host=app.internal port=5432 database=jobready_db"
    assert secret not in identity
    with pytest.raises(SystemExit, match="does not match") as mismatch:
        assert_application_target(
            apply_url=apply_url,
            source_url=source_url,
            application_url=application_url,
            confirmation=f"postgresql://appuser:{secret}@app.internal:5432/jobready_db",
        )
    assert secret not in str(mismatch.value)
    with pytest.raises(SystemExit, match="swapped") as swapped:
        assert_application_target(
            apply_url=source_url,
            source_url=application_url,
            application_url=application_url,
            confirmation="source.internal:5432/railway",
        )
    assert secret not in str(swapped.value)
    with pytest.raises(SystemExit, match="Jobs source"):
        assert_application_target(
            apply_url=source_url,
            source_url=source_url,
            application_url=source_url,
            confirmation="source.internal:5432/railway",
        )
    with pytest.raises(ValueError):
        parse_target_confirmation("app.internal:5432/jobready_db extra")


def test_catalog_role_swap_is_refused():
    assert_catalog_roles(
        apply_has_decisions=True,
        source_has_validated_jobs=True,
        source_has_decisions=False,
    )
    with pytest.raises(SystemExit, match="publication decisions"):
        assert_catalog_roles(
            apply_has_decisions=False,
            source_has_validated_jobs=True,
            source_has_decisions=False,
        )
    with pytest.raises(SystemExit, match="source target has application"):
        assert_catalog_roles(
            apply_has_decisions=True,
            source_has_validated_jobs=False,
            source_has_decisions=True,
        )


def test_changed_plan_aborts_before_write():
    reviewed = SyncPlan(
        complete=False,
        named_only=True,
        seen=1,
        eligible=1,
        inserts=[_row(job_id="CQJ-KEEP", source="indeed")],
    )
    current = SyncPlan(
        complete=False,
        named_only=True,
        seen=1,
        rejected=[("indeed", "CQJ-KEEP", "link_not_active")],
    )
    assert_named_plan_unchanged(reviewed, reviewed)
    with pytest.raises(SystemExit, match="changed before write"):
        assert_named_plan_unchanged(reviewed, current)


def test_cli_does_not_print_target_credentials(tmp_path):
    import os
    import subprocess
    import sys

    batch = tmp_path / "reviewed.txt"
    batch.write_text("indeed/CQJ-REVIEWED\n", encoding="utf-8")
    secret = "cli-target-secret"
    env = os.environ.copy()
    env["JOBS_APPLY_DATABASE_URL"] = f"postgresql://appuser:{secret}@app.internal:5432/jobready_db"
    env["JOBS_SOURCE_DATABASE_URL"] = f"postgresql://source:{secret}@source.internal:5432/railway"
    env["DATABASE_URL"] = f"postgresql://appuser:{secret}@app.internal:5432/jobready_db"
    script = Path(__file__).resolve().parents[1] / "scripts" / "sync_jobs_source.py"
    confirmed = subprocess.run(
        [
            sys.executable,
            str(script),
            "--batch",
            str(batch),
            "--confirm-target",
            "other.internal:5432/jobready_db",
        ],
        cwd=script.parents[1],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    leaked = subprocess.run(
        [
            sys.executable,
            str(script),
            "--batch",
            str(batch),
            "--confirm-target",
            "app.internal:5432/jobready_db",
            "--target-url",
            f"postgresql://appuser:{secret}@app.internal:5432/jobready_db",
        ],
        cwd=script.parents[1],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    for result in (confirmed, leaked):
        blob = result.stdout + result.stderr
        assert result.returncode == 2
        assert secret not in blob
        assert "postgresql://" not in blob
        assert "appuser" not in blob
    assert "does not match" in confirmed.stdout
    assert "must not be passed as an argument" in leaked.stdout
