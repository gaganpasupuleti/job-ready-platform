"""Pydantic schemas for prompt challenges and AI progress."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class PromptChallengeCard(BaseModel):
    id: UUID
    slug: str
    title: str
    description: str
    difficulty: str
    task_type: str
    mastery_threshold: int
    best_score: float = 0
    status: str | None = None
    bookmarked: bool = False


class PromptCasePublic(BaseModel):
    id: UUID
    input_text: str | None = None
    variables: dict[str, Any] = Field(default_factory=dict)
    is_hidden: bool = False
    weight: float = 1
    sort_order: int = 0


class PromptChallengeDetail(BaseModel):
    id: UUID
    slug: str
    title: str
    description: str
    difficulty: str
    task_type: str
    scenario: str
    instructions: str
    input_description: str
    expected_behavior: str
    starter_prompt: str | None = None
    max_prompt_length: int
    mastery_threshold: int
    evaluation_criteria_summary: str
    hints: list[Any] = Field(default_factory=list)
    common_mistakes: list[Any] = Field(default_factory=list)
    public_cases: list[PromptCasePublic] = Field(default_factory=list)
    hidden_case_count: int = 0
    bookmarked: bool = False
    best_score: float = 0
    status: str | None = None


class PromptEvaluateRequest(BaseModel):
    prompt_text: str


class PromptCaseResultOut(BaseModel):
    case_id: UUID
    passed: bool
    score: float
    feedback: str
    revealed: bool = True
    check_results: list[dict[str, Any]] = Field(default_factory=list)


class PromptEvaluateResponse(BaseModel):
    overall_score: float
    passed_cases: int
    total_cases: int
    rubric_breakdown: dict[str, float]
    feedback: str
    case_results: list[PromptCaseResultOut]
    mastered: bool = False
    submission_id: UUID | None = None
    is_test: bool = False


class PromptSubmissionListItem(BaseModel):
    id: UUID
    challenge_id: UUID
    challenge_title: str
    difficulty: str
    overall_score: float
    passed_cases: int
    total_cases: int
    is_test: bool
    created_at: datetime


class PromptSubmissionDetail(PromptEvaluateResponse):
    id: UUID
    challenge_title: str
    difficulty: str
    prompt_text: str
    created_at: datetime


class PromptBookmarkItem(BaseModel):
    id: UUID
    slug: str
    title: str
    difficulty: str
    task_type: str


class AIProgressTopic(BaseModel):
    key: str
    label: str
    mcq_attempts: int = 0
    mcq_accuracy: float | None = None
    prompt_attempts: int = 0
    prompt_mastered: int = 0
    best_prompt_score: float = 0


class AIProgressResponse(BaseModel):
    topics: list[AIProgressTopic]
    weak_topics: list[str] = Field(default_factory=list)
    continue_href: str | None = None
    prompt_attempted: int = 0
    prompt_mastered: int = 0


class PromptChallengeAdminIn(BaseModel):
    slug: str
    title: str
    description: str = ""
    difficulty: str = "easy"
    task_type: str
    scenario: str = ""
    instructions: str = ""
    input_description: str = ""
    expected_behavior: str = ""
    starter_prompt: str | None = None
    reference_prompt: str | None = None
    max_prompt_length: int = 8000
    mastery_threshold: int = 80
    rubric_weights: dict[str, Any] = Field(default_factory=dict)
    hints: list[Any] = Field(default_factory=list)
    common_mistakes: list[Any] = Field(default_factory=list)
    evaluation_criteria_summary: str = ""
    is_active: bool = False
    cases: list[dict[str, Any]] = Field(default_factory=list)
