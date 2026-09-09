"""Sprint 1: mistake idempotency, readiness denominator/aliases, formula version."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

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
async def test_readiness_overview_exposes_formula_version(client, student_auth):
    headers = student_auth[0]
    resp = await client.get("/api/v1/readiness", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("formula_version") == FORMULA_VERSION
    assert body.get("is_hiring_probability") is False
    assert body.get("overall_score_ready") is True
