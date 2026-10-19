from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

TicketCategory = Literal["bug", "improvement", "feature_request", "general"]
TicketStatus = Literal["new", "in_review", "planned", "in_progress", "resolved", "closed"]

_SENSITIVE_MARKERS = ("token", "secret", "password", "bearer", "access_token", "refresh_token")


def clean_page_path(value: str | None) -> str | None:
    if value is None:
        return None
    path = value.strip()
    if not path:
        return None
    lowered = path.lower()
    if any(mark in path for mark in ("?", "#", " ", "\n", "\r", "\t")) or "://" in path:
        raise ValueError("Page path must be a pathname without a query string or fragment")
    if not path.startswith("/") or len(path) > 300:
        raise ValueError("Page path must be a pathname of at most 300 characters")
    if any(marker in lowered for marker in _SENSITIVE_MARKERS):
        raise ValueError("Page path must not include sensitive URL data")
    return path


def _request_id(value: str) -> str:
    text = value.strip()
    if len(text) < 8 or len(text) > 80 or not all(char.isalnum() or char in "_-" for char in text):
        raise ValueError("Request id must be 8 to 80 letters, numbers, underscores, or hyphens")
    return text


class SupportTicketCreate(BaseModel):
    category: TicketCategory
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1, max_length=4000)
    page_path: str | None = None
    client_request_id: str

    @field_validator("title", "description")
    @classmethod
    def strip_required(cls, value: str, info) -> str:
        text = value.strip()
        minimum = 3 if info.field_name == "title" else 10
        if len(text) < minimum:
            label = "Title" if info.field_name == "title" else "Description"
            raise ValueError(f"{label} is too short")
        return text

    @field_validator("page_path")
    @classmethod
    def validate_page(cls, value: str | None) -> str | None:
        return clean_page_path(value)

    @field_validator("client_request_id")
    @classmethod
    def validate_request_id(cls, value: str) -> str:
        return _request_id(value)


class SupportReplyCreate(BaseModel):
    body: str = Field(min_length=1, max_length=4000)
    client_request_id: str

    @field_validator("body")
    @classmethod
    def strip_body(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("Reply is too short")
        if len(text) > 4000:
            raise ValueError("Reply is too long")
        return text

    @field_validator("client_request_id")
    @classmethod
    def validate_request_id(cls, value: str) -> str:
        return _request_id(value)


class SupportStatusUpdate(BaseModel):
    status: TicketStatus
    client_request_id: str

    @field_validator("client_request_id")
    @classmethod
    def validate_request_id(cls, value: str) -> str:
        return _request_id(value)


class SupportTimelineItem(BaseModel):
    id: UUID
    kind: Literal["reply", "status"]
    author_name: str
    author_role: str
    body: str | None = None
    from_status: str | None = None
    to_status: str | None = None
    created_at: datetime


class SupportTicketSummary(BaseModel):
    id: UUID
    reference: str
    category: str
    title: str
    status: str
    page_path: str | None
    created_at: datetime
    updated_at: datetime


class SupportTicketDetail(SupportTicketSummary):
    description: str
    timeline: list[SupportTimelineItem]


class AdminSupportTicketSummary(SupportTicketSummary):
    student_name: str
    student_email: str


class AdminSupportTicketDetail(SupportTicketDetail):
    student_name: str
    student_email: str
