"""Deterministic readiness formulas — documented in docs/READINESS.md."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from app.models.readiness_enums import EvidenceStrength, SkillReadinessStatus

# Default source weights (per-skill overrides may apply in SkillEvidenceService)
DEFAULT_SOURCE_WEIGHTS: dict[str, float] = {
    "mcq": 0.15,
    "coding": 0.20,
    "sql": 0.20,
    "prompt": 0.15,
    "scenario": 0.15,
    "course": 0.05,
    "project": 0.20,
    "interview": 0.10,
    "practice_path": 0.10,
}

# Per-skill category source weight boosts (skill slug -> {source: multiplier})
SKILL_SOURCE_MULTIPLIERS: dict[str, dict[str, float]] = {
    "sql": {"sql": 1.5, "mcq": 0.8},
    "python": {"coding": 1.4, "project": 1.2},
    "aws": {"scenario": 1.3, "mcq": 0.9},
    "communication": {"interview": 1.8, "mcq": 0.5},
}

DIFFICULTY_MULTIPLIER = {"easy": 1.0, "medium": 1.15, "hard": 1.3}

RECENCY_BUCKETS = [
    (30, 1.0),
    (90, 0.95),
    (180, 0.90),
    (99999, 0.85),
]

EVIDENCE_STRENGTH_FACTORS = {
    EvidenceStrength.LOW: 0.75,
    EvidenceStrength.MEDIUM: 0.90,
    EvidenceStrength.HIGH: 1.0,
}

IMPORTANCE_WEIGHTS = {
    "core": 1.0,
    "important": 0.7,
    "nice_to_have": 0.4,
}

STATUS_THRESHOLDS = {
    "strong": 80,
    "developing": 60,
    "needs_work": 1,
}

MIN_ROLE_EVIDENCE_ITEMS = 3
MIN_JOB_MAPPED_SKILLS = 2

JOB_MATCH_WEIGHTS = {
    "required": 0.70,
    "preferred": 0.15,
    "role": 0.10,
    "preference": 0.05,
}

COVERAGE_STATUS_THRESHOLDS = {
    "covered": 80,
    "developing": 60,
}


def recency_multiplier(recorded_at: datetime | None) -> float:
    if recorded_at is None:
        return 0.85
    days = max(0, (datetime.now(UTC) - recorded_at.replace(tzinfo=UTC)).days)
    for max_days, mult in RECENCY_BUCKETS:
        if days <= max_days:
            return mult
    return 0.85


def difficulty_multiplier(difficulty: str | None) -> float:
    if not difficulty:
        return 1.0
    return DIFFICULTY_MULTIPLIER.get(difficulty.lower(), 1.0)


def evidence_strength_from_signals(
    activity_count: int,
    source_diversity: int,
) -> EvidenceStrength:
    """Transparent evidence strength from activity count and source diversity."""
    score = activity_count + source_diversity * 2
    if score >= 8:
        return EvidenceStrength.HIGH
    if score >= 3:
        return EvidenceStrength.MEDIUM
    return EvidenceStrength.LOW


def effective_score(readiness: float, strength: EvidenceStrength) -> float:
    return round(readiness * EVIDENCE_STRENGTH_FACTORS[strength], 1)


def skill_status(score: float, has_evidence: bool) -> SkillReadinessStatus:
    if not has_evidence or score <= 0:
        return SkillReadinessStatus.NO_EVIDENCE
    if score >= STATUS_THRESHOLDS["strong"]:
        return SkillReadinessStatus.STRONG
    if score >= STATUS_THRESHOLDS["developing"]:
        return SkillReadinessStatus.DEVELOPING
    return SkillReadinessStatus.NEEDS_WORK


def coverage_status(readiness: float) -> Literal["covered", "developing", "missing"]:
    if readiness >= COVERAGE_STATUS_THRESHOLDS["covered"]:
        return "covered"
    if readiness >= COVERAGE_STATUS_THRESHOLDS["developing"]:
        return "developing"
    if readiness > 0:
        return "developing"
    return "missing"


def weighted_average(items: list[tuple[float, float]]) -> float:
    """Weighted average; items are (value, weight)."""
    if not items:
        return 0.0
    total_w = sum(w for _, w in items)
    if total_w <= 0:
        return 0.0
    return round(sum(v * w for v, w in items) / total_w, 1)
