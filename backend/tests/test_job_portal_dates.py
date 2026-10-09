"""Portal ingestion date filters use first_seen_at, not the employer posted_at."""

from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError

from app.db.session import AsyncSessionLocal
from app.models.job import Job
from app.models.job_enums import JobStatus
from app.services.job_portal_dates import PORTAL_TZ, added_window, portal_day_start
from app.services.job_service import JobService

FROZEN = datetime(2026, 10, 9, 7, 20, tzinfo=UTC)  # 2026-10-09 12:50 IST


def _freeze(monkeypatch) -> None:
    monkeypatch.setattr("app.services.job_portal_dates._now", lambda: FROZEN)


def _job(**overrides) -> Job:
    now = datetime.now(UTC)
    suffix = uuid4().hex[:8]
    payload = dict(
        slug=f"portal-date-{suffix}",
        title=f"Portal date {suffix}",
        normalized_title=f"portal date {suffix}",
        description="Portal ingestion filter fixture.",
        status=JobStatus.ACTIVE,
        is_active=True,
        content_hash=uuid4().hex,
        first_seen_at=now,
        last_seen_at=now,
        company_name_raw=f"Portal Co {suffix}",
        location_text=f"Portal City {suffix}",
    )
    payload.update(overrides)
    return Job(**payload)


def test_presets_are_inclusive_ist_calendar_days():
    cases = {
        "today": date(2026, 10, 9),
        "3d": date(2026, 10, 7),
        "7d": date(2026, 10, 3),
        "30d": date(2026, 9, 10),
    }
    end = portal_day_start(date(2026, 10, 10))
    for preset, start_day in cases.items():
        start, actual_end = added_window(preset, None, None, now=FROZEN)
        assert start == portal_day_start(start_day)
        assert actual_end == end
        assert start.tzinfo == PORTAL_TZ


def test_custom_range_is_inclusive_and_half_open():
    start, end = added_window(None, date(2026, 10, 1), date(2026, 10, 3), now=FROZEN)
    assert start == portal_day_start(date(2026, 10, 1))
    assert end == portal_day_start(date(2026, 10, 4))
    open_start, open_end = added_window(None, date(2026, 10, 1), None, now=FROZEN)
    assert open_start == portal_day_start(date(2026, 10, 1))
    assert open_end is None
    only_end_start, only_end = added_window(None, None, date(2026, 10, 3), now=FROZEN)
    assert only_end_start is None
    assert only_end == portal_day_start(date(2026, 10, 4))


def test_invalid_portal_ranges_are_rejected():
    with pytest.raises(ValueError, match="either added_within"):
        added_window("today", date(2026, 10, 1), None)
    with pytest.raises(ValueError, match="on or before"):
        added_window(None, date(2026, 10, 3), date(2026, 10, 1))
    with pytest.raises(ValueError, match="today, 3d, 7d, or 30d"):
        added_window("14d", None, None)


def test_unfiltered_window_is_empty_and_naive_clock_is_utc():
    assert added_window(None, None, None, now=FROZEN) == (None, None)
    start, _end = added_window("today", None, None, now=datetime(2026, 10, 9, 7, 20))
    assert start == portal_day_start(date(2026, 10, 9))


def test_missing_first_seen_is_an_explicit_sql_exclusion():
    start, end = added_window("today", None, None, now=FROZEN)
    stmt = select(Job.id).where(Job.first_seen_at.is_not(None), Job.first_seen_at >= start, Job.first_seen_at < end)
    compiled = str(stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))
    assert "first_seen_at IS NOT NULL" in compiled
    assert "first_seen_at >=" in compiled
    assert "first_seen_at <" in compiled
    service = JobService(db=None)  # type: ignore[arg-type]
    browse = service._browse_ids(added_start=start, added_end=end)
    browse_sql = str(browse.compile(dialect=postgresql.dialect()))
    assert "first_seen_at IS NOT NULL" in browse_sql
    assert "LIMIT" not in browse_sql


@pytest.mark.asyncio
async def test_first_seen_at_cannot_be_stored_as_null():
    async with AsyncSessionLocal() as db:
        db.add(_job(first_seen_at=None))
        with pytest.raises(IntegrityError):
            await db.commit()
        await db.rollback()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("preset", "days"),
    [("today", 1), ("3d", 3), ("7d", 7), ("30d", 30)],
)
async def test_each_preset_includes_the_start_and_excludes_the_instant_before(
    client, student_auth, monkeypatch, preset, days
):
    _freeze(monkeypatch)
    headers, _ = student_auth
    token = uuid4().hex[:8]
    location = f"Portal City {token}"
    local_today = date(2026, 10, 9)
    start = portal_day_start(local_today - timedelta(days=days - 1))
    end = portal_day_start(local_today + timedelta(days=1))
    inside = _job(
        title=f"Inside {preset} {token}",
        location_text=location,
        company_name_raw=f"Portal Co {token}",
        first_seen_at=start,
        posted_at=None,
    )
    outside = _job(
        title=f"Outside {preset} {token}",
        location_text=location,
        company_name_raw=f"Portal Co {token}",
        first_seen_at=start - timedelta(microseconds=1),
        posted_at=FROZEN,
    )
    async with AsyncSessionLocal() as db:
        db.add_all([inside, outside])
        await db.commit()
        inside_id = str(inside.id)
        outside_id = str(outside.id)

    listed = await client.get(
        "/api/v1/jobs",
        headers=headers,
        params={"location": location, "added_within": preset, "limit": 20},
    )
    assert listed.status_code == 200, listed.text
    body = listed.json()
    ids = {item["id"] for item in body["items"]}
    assert body["total"] == 1
    assert inside_id in ids
    assert outside_id not in ids
    assert body["items"][0]["posted_at"] is None
    assert body["items"][0]["first_seen_at"] is not None

    counts = await client.get(
        "/api/v1/jobs/family-counts",
        headers=headers,
        params={"location": location, "added_within": preset},
    )
    assert counts.status_code == 200, counts.text
    assert counts.json()["all"] == 1

    at_end = _job(
        title=f"End {preset} {token}",
        location_text=location,
        company_name_raw=f"Portal Co {token}",
        first_seen_at=end,
    )
    async with AsyncSessionLocal() as db:
        db.add(at_end)
        await db.commit()
        end_id = str(at_end.id)
    again = await client.get(
        "/api/v1/jobs",
        headers=headers,
        params={"location": location, "added_within": preset, "limit": 20},
    )
    assert end_id not in {item["id"] for item in again.json()["items"]}
    assert again.json()["total"] == 1


@pytest.mark.asyncio
async def test_custom_range_pagination_and_other_filters_stay_independent(client, student_auth, monkeypatch):
    _freeze(monkeypatch)
    headers, _ = student_auth
    token = uuid4().hex[:8]
    location = f"Range City {token}"
    company = f"Range Co {token}"
    other_company = f"Other Co {token}"
    start = portal_day_start(date(2026, 10, 1))
    jobs = [
        _job(
            title=f"Range {index} {token}",
            location_text=location,
            company_name_raw=company,
            first_seen_at=start + timedelta(days=index % 3, hours=index),
            posted_at=datetime.now(UTC) - timedelta(days=10),
        )
        for index in range(21)
    ]
    too_early = _job(
        title=f"Too early {token}",
        location_text=location,
        company_name_raw=company,
        first_seen_at=portal_day_start(date(2026, 9, 30)),
        posted_at=FROZEN,
    )
    other = _job(
        title=f"Other company {token}",
        location_text=location,
        company_name_raw=other_company,
        first_seen_at=start + timedelta(hours=1),
        posted_at=datetime.now(UTC),
    )
    async with AsyncSessionLocal() as db:
        db.add_all([*jobs, too_early, other])
        await db.commit()
        early_id = str(too_early.id)

    listed = await client.get(
        "/api/v1/jobs",
        headers=headers,
        params={
            "location": location,
            "company": company,
            "added_from": "2026-10-01",
            "added_to": "2026-10-03",
            "limit": 20,
            "page": 1,
        },
    )
    assert listed.status_code == 200, listed.text
    body = listed.json()
    assert body["total"] == 21
    assert len(body["items"]) == 20
    assert early_id not in {item["id"] for item in body["items"]}

    page_two = await client.get(
        "/api/v1/jobs",
        headers=headers,
        params={
            "location": location,
            "company": company,
            "added_from": "2026-10-01",
            "added_to": "2026-10-03",
            "limit": 20,
            "page": 2,
        },
    )
    assert page_two.status_code == 200, page_two.text
    assert page_two.json()["total"] == 21
    assert len(page_two.json()["items"]) == 1
    assert early_id not in {item["id"] for item in page_two.json()["items"]}

    employer = await client.get(
        "/api/v1/jobs",
        headers=headers,
        params={
            "location": location,
            "company": company,
            "added_from": "2026-10-01",
            "added_to": "2026-10-03",
            "posted_within_days": 7,
            "limit": 20,
        },
    )
    assert employer.status_code == 200, employer.text
    assert employer.json()["total"] == 0

    fresh_post = await client.get(
        "/api/v1/jobs",
        headers=headers,
        params={"location": location, "company": other_company, "posted_within_days": 1, "limit": 20},
    )
    assert fresh_post.status_code == 200, fresh_post.text
    assert fresh_post.json()["total"] == 1


@pytest.mark.asyncio
async def test_mixed_or_reversed_ranges_do_not_filter(client, student_auth):
    headers, _ = student_auth
    mixed = await client.get(
        "/api/v1/jobs",
        headers=headers,
        params={"added_within": "today", "added_from": "2026-10-01"},
    )
    assert mixed.status_code == 422
    reversed_range = await client.get(
        "/api/v1/jobs",
        headers=headers,
        params={"added_from": "2026-10-03", "added_to": "2026-10-01"},
    )
    assert reversed_range.status_code == 422
    unknown = await client.get("/api/v1/jobs", headers=headers, params={"added_within": "14d"})
    assert unknown.status_code == 422
