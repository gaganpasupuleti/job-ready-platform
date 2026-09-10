"""Sprint 1: mistake idempotency, readiness denominator/aliases, formula version, lesson verify."""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from sqlalchemy import func, select

from app.models.readiness_enums import EvidenceStrength, MistakeSourceType, MistakeStatus
from app.readiness.formulas import FORMULA_VERSION
from app.readiness.skill_mapping import SKILL_ALIASES, normalize_skill_key
from app.services.mistake_service import MistakeService
from app.services.readiness_service import ReadinessService
from app.services.skill_evidence_service import SkillEvidence


def test_unsafe_skill_aliases_removed():
    assert "powerbi" not in SKILL_ALIASES
    assert "power-bi" not in SKILL_ALIASES
    assert "communication" not in SKILL_ALIASES
    assert "apache flink" not in SKILL_ALIASES
    assert normalize_skill_key("powerbi") == "powerbi"
    assert normalize_skill_key("communication") == "communication"
    assert normalize_skill_key("flink") == "flink"
    assert normalize_skill_key("postgresql") == "sql"


def test_readiness_includes_missing_skills_in_denominator():
    svc = ReadinessService(db=MagicMock())
    role_skill_a = SimpleNamespace(id=uuid.uuid4(), name="SQL", slug="sql")
    role_skill_b = SimpleNamespace(id=uuid.uuid4(), name="Spark", slug="spark")
    req_a = SimpleNamespace(
        importance=SimpleNamespace(value="core"),
        weight=1.0,
    )
    req_b = SimpleNamespace(
        importance=SimpleNamespace(value="core"),
        weight=1.0,
    )
    evidence = {
        "sql": SkillEvidence(
            skill_id=role_skill_a.id,
            skill_name="SQL",
            skill_slug="sql",
            score=90.0,
            effective_score=90.0,
            evidence_strength=EvidenceStrength.HIGH,
            activity_count=5,
            last_activity_at=datetime.now(UTC),
            status="strong",
            sources=[],
        )
    }
    result = svc._role_readiness_from_requirements(
        [(req_a, role_skill_a), (req_b, role_skill_b)],
        evidence,
    )
    assert result["formula_version"] == FORMULA_VERSION
    assert result["is_hiring_probability"] is False
    assert "Spark" in result["missing_skills"]
    assert result["score"] is not None
    assert result["score"] < 90.0
    assert result["core_coverage"]["total"] == 2
    assert result["overall_score_ready"] is True


@pytest.mark.asyncio
async def test_mistake_upsert_idempotent_on_same_event(client, student_auth):
    from app.db.session import AsyncSessionLocal
    from app.repositories.user_repository import UserRepository

    _headers, email = student_auth
    async with AsyncSessionLocal() as db:
        user = await UserRepository(db).get_by_email(email)
        assert user is not None
        problem_id = uuid.uuid4()
        event_id = uuid.uuid4()
        svc = MistakeService(db)
        first = await svc.upsert(
            user_id=user.id,
            source_type=MistakeSourceType.SQL,
            source_id=problem_id,
            title="Idempotent SQL",
            retry_href="/practice/sql/demo",
            source_event_id=event_id,
        )
        assert first.occurrence_count == 1
        first_seen = first.first_seen_at
        last_seen = first.last_seen_at

        await svc.resolve(user, first.id)
        replay = await svc.upsert(
            user_id=user.id,
            source_type=MistakeSourceType.SQL,
            source_id=problem_id,
            title="Idempotent SQL",
            retry_href="/practice/sql/demo",
            source_event_id=event_id,
            reopen_if_resolved=False,
        )
        assert replay.occurrence_count == 1
        assert replay.status == MistakeStatus.RESOLVED
        assert replay.first_seen_at == first_seen
        assert replay.last_seen_at == last_seen

        other = await svc.upsert(
            user_id=user.id,
            source_type=MistakeSourceType.SQL,
            source_id=problem_id,
            title="Idempotent SQL",
            source_event_id=uuid.uuid4(),
            reopen_if_resolved=False,
        )
        assert other.occurrence_count == 2
        assert other.status == MistakeStatus.RESOLVED


@pytest.mark.asyncio
async def test_mistake_concurrent_same_event_does_not_double_count(client, student_auth):
    from app.db.session import AsyncSessionLocal
    from app.repositories.user_repository import UserRepository

    _headers, email = student_auth
    async with AsyncSessionLocal() as db:
        user = await UserRepository(db).get_by_email(email)
        assert user is not None
        problem_id = uuid.uuid4()
        event_id = uuid.uuid4()

        async def _once() -> int:
            async with AsyncSessionLocal() as session:
                svc = MistakeService(session)
                item = await svc.upsert(
                    user_id=user.id,
                    source_type=MistakeSourceType.SQL,
                    source_id=problem_id,
                    title="Concurrent SQL",
                    source_event_id=event_id,
                )
                return item.occurrence_count

        counts = await asyncio.gather(_once(), _once(), _once())
        assert max(counts) == 1

        async with AsyncSessionLocal() as session:
            svc = MistakeService(session)
            final = await svc.upsert(
                user_id=user.id,
                source_type=MistakeSourceType.SQL,
                source_id=problem_id,
                title="Concurrent SQL",
                source_event_id=event_id,
            )
            assert final.occurrence_count == 1


@pytest.mark.asyncio
async def test_mistake_concurrent_distinct_events_create_one_item(client, student_auth):
    """Two distinct failure events race before any item exists."""
    from app.db.session import AsyncSessionLocal
    from app.models.readiness import MistakeItem, MistakeSourceEvent
    from app.repositories.user_repository import UserRepository

    _headers, email = student_auth
    async with AsyncSessionLocal() as db:
        user = await UserRepository(db).get_by_email(email)
        assert user is not None
        problem_id = uuid.uuid4()
        event_a = uuid.uuid4()
        event_b = uuid.uuid4()
        barrier = asyncio.Barrier(2)

        async def _worker(event_id: uuid.UUID) -> uuid.UUID:
            async with AsyncSessionLocal() as session:
                await barrier.wait()
                svc = MistakeService(session)
                item = await svc.upsert(
                    user_id=user.id,
                    source_type=MistakeSourceType.CODING,
                    source_id=problem_id,
                    title="Race coding mistake",
                    source_event_id=event_id,
                )
                return item.id

        ids = await asyncio.gather(_worker(event_a), _worker(event_b))
        assert ids[0] == ids[1]

        async with AsyncSessionLocal() as session:
            item = (
                await session.execute(
                    select(MistakeItem).where(
                        MistakeItem.user_id == user.id,
                        MistakeItem.source_type == MistakeSourceType.CODING,
                        MistakeItem.source_id == problem_id,
                    )
                )
            ).scalar_one()
            assert item.occurrence_count == 2
            event_count = (
                await session.execute(
                    select(func.count())
                    .select_from(MistakeSourceEvent)
                    .where(
                        MistakeSourceEvent.mistake_item_id == item.id,
                        MistakeSourceEvent.source_event_id.in_([event_a, event_b]),
                    )
                )
            ).scalar_one()
            assert int(event_count) == 2


@pytest.fixture
async def learn_seed():
    from app.seed.learn_data import seed_learn_content

    await seed_learn_content()
    yield


@pytest.mark.asyncio
async def test_lesson_attempt_verification_via_service(client, student_auth, learn_seed):
    """Real LearnService / endpoint verification + persisted LessonAttempt / completion."""
    from app.core.security import hash_password
    from app.db.session import AsyncSessionLocal
    from app.models.coding import CodingProblem, CodingSubmission
    from app.models.coding_enums import SubmissionStatus, SubmissionType
    from app.models.enums import UserRole
    from app.models.learn import CourseLesson, LessonAttempt, UserLessonProgress
    from app.models.learn_enums import ProgressStatus
    from app.models.user import User
    from app.repositories.user_repository import UserRepository
    from app.services.learn_service import LearnService

    headers, email = student_auth

    async with AsyncSessionLocal() as db:
        user = await UserRepository(db).get_by_email(email)
        assert user is not None
        other = User(
            email=f"other.owner.{uuid.uuid4().hex[:8]}@jobready.dev",
            username=f"other{uuid.uuid4().hex[:8]}",
            password_hash=hash_password("OtherOwner123!"),
            full_name="Other Owner",
            role=UserRole.STUDENT,
            is_active=True,
        )
        db.add(other)
        await db.flush()

        problem = (await db.execute(select(CodingProblem).limit(1))).scalar_one_or_none()
        if problem is None:
            pytest.skip("No coding problems seeded")
        other_problem = (
            await db.execute(select(CodingProblem).where(CodingProblem.id != problem.id).limit(1))
        ).scalar_one_or_none()
        if other_problem is None:
            pytest.skip("Need at least two coding problems")

        lesson = (
            await db.execute(
                select(CourseLesson).where(CourseLesson.is_published.is_(True)).limit(1)
            )
        ).scalar_one()
        lesson.coding_problem_id = problem.id
        lesson.completion_requires_submit = True
        await db.commit()
        lesson_id = lesson.id
        user_id = user.id
        other_id = other.id
        problem_id = problem.id
        other_problem_id = other_problem.id

    async def _add_submission(
        *,
        owner_id,
        problem_id_,
        submission_type,
        status,
    ) -> uuid.UUID:
        async with AsyncSessionLocal() as db:
            sub = CodingSubmission(
                user_id=owner_id,
                problem_id=problem_id_,
                source_code="print(1)",
                language_id=71,
                language_name="Python",
                submission_type=submission_type,
                status=status,
                passed_tests=1 if status == SubmissionStatus.ACCEPTED else 0,
                total_tests=1,
            )
            db.add(sub)
            await db.commit()
            await db.refresh(sub)
            return sub.id

    async def _attempt(submission_id: uuid.UUID | None = None, **extra) -> dict:
        payload = dict(extra)
        if submission_id is not None:
            payload["coding_submission_id"] = str(submission_id)
        res = await client.post(
            f"/api/v1/lessons/{lesson_id}/attempt",
            headers=headers,
            json=payload,
        )
        assert res.status_code == 200, res.text
        return res.json()

    accepted_run = await _add_submission(
        owner_id=user_id,
        problem_id_=problem_id,
        submission_type=SubmissionType.RUN,
        status=SubmissionStatus.ACCEPTED,
    )
    body = await _attempt(accepted_run, is_correct=True)
    assert body["verified"] is False
    assert body["is_correct"] is None

    unrelated = await _add_submission(
        owner_id=user_id,
        problem_id_=other_problem_id,
        submission_type=SubmissionType.SUBMIT,
        status=SubmissionStatus.ACCEPTED,
    )
    body = await _attempt(unrelated)
    assert body["verified"] is False
    assert body["is_correct"] is None

    wrong_owner = await _add_submission(
        owner_id=other_id,
        problem_id_=problem_id,
        submission_type=SubmissionType.SUBMIT,
        status=SubmissionStatus.ACCEPTED,
    )
    body = await _attempt(wrong_owner)
    assert body["verified"] is False
    assert body["is_correct"] is None

    failed = await _add_submission(
        owner_id=user_id,
        problem_id_=problem_id,
        submission_type=SubmissionType.SUBMIT,
        status=SubmissionStatus.WRONG_ANSWER,
    )
    body = await _attempt(failed)
    assert body["verified"] is False
    assert body["is_correct"] is False

    pending = await _add_submission(
        owner_id=user_id,
        problem_id_=problem_id,
        submission_type=SubmissionType.SUBMIT,
        status=SubmissionStatus.PENDING,
    )
    body = await _attempt(pending)
    assert body["verified"] is False
    assert body["is_correct"] is False

    blocked = await client.post(f"/api/v1/lessons/{lesson_id}/complete", headers=headers)
    assert blocked.status_code == 400, blocked.text

    accepted_submit = await _add_submission(
        owner_id=user_id,
        problem_id_=problem_id,
        submission_type=SubmissionType.SUBMIT,
        status=SubmissionStatus.ACCEPTED,
    )
    body = await _attempt(accepted_submit)
    assert body["verified"] is True
    assert body["is_correct"] is True

    async with AsyncSessionLocal() as db:
        attempts = (
            await db.execute(
                select(LessonAttempt)
                .where(LessonAttempt.user_id == user_id, LessonAttempt.lesson_id == lesson_id)
                .order_by(LessonAttempt.created_at.asc())
            )
        ).scalars().all()
        assert len(attempts) >= 6
        verified_rows = [a for a in attempts if a.is_correct is True]
        assert len(verified_rows) == 1
        assert verified_rows[0].coding_submission_id == accepted_submit

        svc = LearnService(db)
        user_row = await UserRepository(db).get_by_email(email)
        assert user_row is not None
        ok = await svc.record_attempt(
            lesson_id,
            user_row,
            {"coding_submission_id": str(accepted_submit)},
        )
        assert ok["verified"] is True

    complete = await client.post(f"/api/v1/lessons/{lesson_id}/complete", headers=headers)
    assert complete.status_code == 200, complete.text
    assert complete.json()["status"] == "completed"

    async with AsyncSessionLocal() as db:
        progress = (
            await db.execute(
                select(UserLessonProgress).where(
                    UserLessonProgress.user_id == user_id,
                    UserLessonProgress.lesson_id == lesson_id,
                )
            )
        ).scalar_one()
        assert progress.status == ProgressStatus.COMPLETED


@pytest.mark.asyncio
async def test_readiness_overview_exposes_formula_version(client, student_auth):
    headers = student_auth[0]
    resp = await client.get("/api/v1/readiness", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("formula_version") == FORMULA_VERSION
    assert body.get("is_hiring_probability") is False
    assert body.get("overall_score_ready") is False
