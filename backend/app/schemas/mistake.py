"""Mistake book API schemas."""

from typing import Any

from pydantic import BaseModel, Field


class MistakeItemResponse(BaseModel):
    id: str
    source_type: str
    source_id: str
    title: str
    summary: str | None = None
    mistake_type: str
    occurrence_count: int
    status: str
    first_seen_at: str
    last_seen_at: str
    retry_href: str | None = None
    context: dict[str, Any] | None = None


class MistakeSummary(BaseModel):
    open_count: int
    repeated_count: int
    resolved_count: int
    top_weak_topics: list[dict[str, Any]] = Field(default_factory=list)


class RetrySessionRequest(BaseModel):
    question_ids: list[str] = Field(..., min_length=1, max_length=50)
