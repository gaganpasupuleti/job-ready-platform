"""Schemas for deterministic scenario challenges."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ScenarioOptionPublic(BaseModel):
    id: UUID
    label: str
    sort_order: int


class ScenarioStepPublic(BaseModel):
    id: UUID
    sort_order: int
    prompt: str
    context_snippet: str
    is_critical: bool
    options: list[ScenarioOptionPublic]


class ScenarioCard(BaseModel):
    id: UUID
    slug: str
    title: str
    description: str
    domain_key: str
    scenario_type: str
    difficulty: str
    unofficial_cert_tag: str | None = None
    best_score: float = 0
    status: str | None = None


class ScenarioDetail(BaseModel):
    id: UUID
    slug: str
    title: str
    description: str
    domain_key: str
    scenario_type: str
    difficulty: str
    context_text: str
    evidence_json: dict[str, Any] = Field(default_factory=dict)
    unofficial_cert_tag: str | None = None
    unofficial_disclaimer: str = "Unofficial preparation. Not affiliated with any certification vendor."
    mastery_threshold: int
    steps: list[ScenarioStepPublic]
    best_score: float = 0
    status: str | None = None


class ScenarioAnswerIn(BaseModel):
    step_id: UUID
    option_id: UUID


class ScenarioSubmitRequest(BaseModel):
    answers: list[ScenarioAnswerIn]


class ScenarioStepResult(BaseModel):
    step_id: UUID
    option_id: UUID
    is_correct: bool
    explanation: str
    is_critical: bool


class ScenarioSubmitResponse(BaseModel):
    overall_score: float
    correct_decisions: int
    total_steps: int
    missed_critical: list[str]
    explanation: str
    step_results: list[ScenarioStepResult]
    mastered: bool
    submission_id: UUID


class ScenarioAdminIn(BaseModel):
    slug: str
    title: str
    description: str = ""
    domain_key: str
    scenario_type: str
    difficulty: str = "medium"
    context_text: str = ""
    evidence_json: dict[str, Any] = Field(default_factory=dict)
    unofficial_cert_tag: str | None = None
    mastery_threshold: int = 80
    is_active: bool = False
    steps: list[dict[str, Any]] = Field(default_factory=list)


class DomainProgressTopic(BaseModel):
    key: str
    label: str
    mcq_attempts: int = 0
    mcq_accuracy: float | None = None
    scenario_attempts: int = 0
    scenario_best: float = 0


class DomainProgressResponse(BaseModel):
    domain: str
    topics: list[DomainProgressTopic]
    weak_topics: list[str] = Field(default_factory=list)
    continue_href: str | None = None
    scenario_attempted: int = 0
    scenario_mastered: int = 0
    paths: list[dict[str, Any]] = Field(default_factory=list)
    projects: list[dict[str, Any]] = Field(default_factory=list)
