"""Readiness API schemas."""

from pydantic import BaseModel, Field


class RoleBrief(BaseModel):
    id: str
    name: str
    slug: str


class CoreCoverage(BaseModel):
    covered: int
    total: int


class SkillSourceBreakdown(BaseModel):
    source: str
    score: float
    activity_count: int


class SkillReadinessItem(BaseModel):
    skill_id: str | None = None
    skill_name: str | None = None
    skill_slug: str | None = None
    importance: str | None = None
    weight: float | None = None
    readiness: float = 0
    effective_score: float = 0
    evidence_strength: str = "low"
    status: str = "no_evidence"
    sources: list[SkillSourceBreakdown] = Field(default_factory=list)


class WhyBreakdownItem(BaseModel):
    skill: str
    importance: str
    weight_percent: float
    readiness: float
    effective_score: float
    evidence_strength: str


class TrendPoint(BaseModel):
    score: float
    created_at: str
    evidence_strength: str


class RecommendationAction(BaseModel):
    title: str
    description: str
    reason: str
    skill: str | None = None
    priority: str
    href: str
    action_type: str


class ReadinessOverview(BaseModel):
    target_role: RoleBrief | None = None
    score: float | None = None
    has_minimum_evidence: bool = False
    evidence_strength: str = "low"
    core_coverage: CoreCoverage = Field(default_factory=lambda: CoreCoverage(covered=0, total=0))
    skills: list[SkillReadinessItem] = Field(default_factory=list)
    strong_skills: list[str] = Field(default_factory=list)
    developing_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    why_breakdown: list[WhyBreakdownItem] = Field(default_factory=list)
    trend: list[TrendPoint] = Field(default_factory=list)
    recommended_actions: list[RecommendationAction] = Field(default_factory=list)
    message: str | None = None


class SkillProfileItem(BaseModel):
    skill_id: str
    skill: str
    skill_slug: str
    score: float
    effective_score: float
    evidence_strength: str
    activity_count: int
    last_activity_at: str | None = None
    status: str
    sources: list[SkillSourceBreakdown] = Field(default_factory=list)


class RoleComparisonItem(BaseModel):
    role_id: str
    role_name: str
    role_slug: str
    score: float | None = None
    has_minimum_evidence: bool = False
