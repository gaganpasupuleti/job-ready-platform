# ruff: noqa: E501
"""Content Factory: validation, staging, approval, student visibility."""

from __future__ import annotations

import json
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.content.hashing import content_hash, jaccard_similarity, normalize_question_text
from app.content.importer import import_questions_file
from app.content.publisher import publish_validated_question
from app.content.reports import daily_report, gap_report
from app.content.validator import validate_file_payload, validate_question_payload
from app.db.session import AsyncSessionLocal
from app.models.interview import (
    InterviewQuestionJob,
    InterviewQuestionRole,
    InterviewQuestionSkill,
    JobListing,
)
from app.models.interview_enums import ContentReviewStatus
from app.seed.runner import ensure_content_factory_catalog


def _headers(auth):
    return auth if isinstance(auth, dict) else auth[0]


VALID_PAYLOAD = {
    "question_text": "How does PARTITION BY change window ranking in SQL?",
    "question_type": "technical",
    "difficulty": "medium",
    "experience_level": "junior",
    "expected_answer": (
        "PARTITION BY splits the result into groups so RANK or DENSE_RANK restarts "
        "inside each group. Without it, ranking is computed over the entire result set."
    ),
    "key_points": [
        "PARTITION BY creates independent ranking groups",
        "Ranks restart at 1 within each partition",
        "Omitting PARTITION BY ranks the full result set",
    ],
    "skills": ["SQL"],
    "roles": ["Data Engineer", "Data Analyst"],
    "companies": ["Acme Labs"],
    "jobs": [],
}


@pytest.fixture
async def catalog():
    await ensure_content_factory_catalog()
    yield


@pytest.mark.asyncio
async def test_hash_normalization():
    a = content_hash("Explain RANK() and DENSE_RANK!!")
    b = content_hash("  explain rank and dense rank  ")
    assert a == b
    assert normalize_question_text("Hello,  World!") == "hello world"
    assert jaccard_similarity("rank dense rank gaps", "rank dense rank no gaps") > 0.5


@pytest.mark.asyncio
async def test_validate_rejects_placeholder_and_enums(catalog):
    async with AsyncSessionLocal() as session:
        bad = await validate_question_payload(
            session,
            {
                **VALID_PAYLOAD,
                "expected_answer": "TODO sample answer goes here lorem ipsum",
                "question_type": "not-a-type",
            },
        )
        assert not bad.ok
        assert any("Placeholder" in e or "placeholder" in e.lower() or "Invalid question_type" in e for e in bad.errors)


@pytest.mark.asyncio
async def test_invalid_skill_role_company(catalog):
    async with AsyncSessionLocal() as session:
        result = await validate_question_payload(
            session,
            {
                **VALID_PAYLOAD,
                "skills": ["NotARealSkill"],
                "roles": ["NotARealRole"],
                "companies": ["NotACompany"],
            },
        )
        assert not result.ok
        joined = " ".join(result.errors)
        assert "Unknown skills" in joined
        assert "Unknown roles" in joined
        assert "Unknown companies" in joined


@pytest.mark.asyncio
async def test_invalid_job_reference(catalog):
    async with AsyncSessionLocal() as session:
        result = await validate_question_payload(
            session, {**VALID_PAYLOAD, "jobs": ["no-such-job-listing"]}
        )
        assert not result.ok
        assert any("Unknown jobs" in e for e in result.errors)


@pytest.mark.asyncio
async def test_import_stays_staging_until_approve(client, student_auth, admin_auth, catalog, tmp_path):
    payload = {
        "questions": [
            {
                **VALID_PAYLOAD,
                "question_text": f"What is a covering index in PostgreSQL {uuid4().hex[:8]}?",
            }
        ]
    }
    path = tmp_path / "batch.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    async with AsyncSessionLocal() as session:
        batch = await import_questions_file(session, path, approve=False)

    listed = await client.get("/api/v1/interview/questions", headers=_headers(student_auth))
    assert listed.status_code == 200
    texts = [item["question_text"] for item in listed.json()["items"]]
    assert payload["questions"][0]["question_text"] not in texts

    cands = await client.get(
        "/api/v1/admin/content/candidates",
        headers=admin_auth,
        params={"batch_id": str(batch.id)},
    )
    assert cands.status_code == 200
    candidate = cands.json()["items"][0]
    assert candidate["review_status"] == "pending"
    assert candidate["validation_status"] == "valid"

    approve = await client.post(
        f"/api/v1/admin/content/candidates/{candidate['id']}/approve",
        headers=admin_auth,
    )
    assert approve.status_code == 200, approve.text
    assert approve.json()["review_status"] == "approved"

    listed2 = await client.get("/api/v1/interview/questions", headers=_headers(student_auth))
    texts2 = [item["question_text"] for item in listed2.json()["items"]]
    assert payload["questions"][0]["question_text"] in texts2


@pytest.mark.asyncio
async def test_reject_does_not_publish(client, student_auth, admin_auth, catalog, tmp_path):
    qtext = f"Describe vacuum in PostgreSQL {uuid4().hex[:8]}"
    path = tmp_path / "rej.json"
    path.write_text(json.dumps({"questions": [{**VALID_PAYLOAD, "question_text": qtext}]}), encoding="utf-8")
    async with AsyncSessionLocal() as session:
        batch = await import_questions_file(session, path)

    items = (
        await client.get(
            "/api/v1/admin/content/candidates",
            headers=admin_auth,
            params={"batch_id": str(batch.id)},
        )
    ).json()["items"]
    reject = await client.post(
        f"/api/v1/admin/content/candidates/{items[0]['id']}/reject",
        headers=admin_auth,
    )
    assert reject.status_code == 200
    listed = await client.get("/api/v1/interview/questions", headers=_headers(student_auth))
    assert qtext not in [i["question_text"] for i in listed.json()["items"]]


@pytest.mark.asyncio
async def test_duplicate_hash_and_key_points(catalog):
    async with AsyncSessionLocal() as session:
        first = await publish_validated_question(
            session,
            {**VALID_PAYLOAD, "question_text": f"Unique covering question {uuid4().hex}"},
        )
        await session.commit()
        dup = await validate_question_payload(
            session, {**VALID_PAYLOAD, "question_text": first.question_text}
        )
        assert any("Duplicate" in e for e in dup.errors)

        few_points = await validate_question_payload(
            session, {**VALID_PAYLOAD, "question_text": f"Another unique {uuid4().hex}", "key_points": ["only one"]}
        )
        assert any("key points" in e.lower() for e in few_points.errors)


@pytest.mark.asyncio
async def test_duplicate_within_batch(catalog):
    qtext = f"Why index a foreign key column {uuid4().hex[:8]}?"
    payload = {**VALID_PAYLOAD, "question_text": qtext}
    async with AsyncSessionLocal() as session:
        results, _ = await validate_file_payload(session, {"questions": [payload, payload]})
        assert results[0].ok
        assert any("Duplicate question within this batch" in e for e in results[1].errors)


@pytest.mark.asyncio
async def test_multi_role_skill_and_job_mapping(catalog):
    async with AsyncSessionLocal() as session:
        job = (
            await session.execute(select(JobListing).where(JobListing.slug == "acme-data-engineer"))
        ).scalar_one_or_none()
        jobs = [job.slug] if job else []
        q = await publish_validated_question(
            session,
            {
                **VALID_PAYLOAD,
                "question_text": f"Explain Snowflake micro-partitions {uuid4().hex[:6]}",
                "skills": ["SQL", "Python"],
                "roles": ["Data Engineer", "Data Analyst"],
                "jobs": jobs,
            },
        )
        await session.commit()
        skill_count = len(
            (
                await session.execute(
                    select(InterviewQuestionSkill).where(InterviewQuestionSkill.question_id == q.id)
                )
            ).scalars().all()
        )
        role_count = len(
            (
                await session.execute(
                    select(InterviewQuestionRole).where(InterviewQuestionRole.question_id == q.id)
                )
            ).scalars().all()
        )
        job_count = len(
            (
                await session.execute(
                    select(InterviewQuestionJob).where(InterviewQuestionJob.question_id == q.id)
                )
            ).scalars().all()
        )
        assert skill_count >= 2
        assert role_count >= 2
        assert job_count >= 1
        assert q.review_status == ContentReviewStatus.APPROVED


@pytest.mark.asyncio
async def test_batch_stats_and_gap_report(catalog, tmp_path):
    path = tmp_path / "stats.json"
    path.write_text(
        json.dumps(
            {
                "questions": [
                    {**VALID_PAYLOAD, "question_text": f"Window functions vs group by {uuid4().hex[:6]}"}
                ]
            }
        ),
        encoding="utf-8",
    )
    async with AsyncSessionLocal() as session:
        batch = await import_questions_file(session, path)
        assert batch.generated_count == 1
        assert batch.accepted_count == 0
        gaps = await gap_report(session)
        daily = await daily_report(session)
        assert "live_questions" in gaps
        assert "pending_candidates" in daily
        assert "suggested_priorities" in gaps


@pytest.mark.asyncio
async def test_student_cannot_admin_content(client, student_auth, catalog):
    response = await client.get("/api/v1/admin/content/batches", headers=_headers(student_auth))
    assert response.status_code == 403
