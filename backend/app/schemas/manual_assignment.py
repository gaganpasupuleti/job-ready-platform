"""Manual assignment submission contracts."""

from uuid import UUID

from pydantic import BaseModel, Field


class ManualAssignmentCreate(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    link: str = Field(min_length=8, max_length=500)
    note: str | None = Field(default=None, max_length=2000)
    question: str | None = Field(default=None, max_length=2000)
    project_id: UUID | None = None


class ManualAssignmentReview(BaseModel):
    review_note: str = Field(min_length=3, max_length=4000)


class ManualAssignmentReport(BaseModel):
    id: str
    student_name: str
    student_email: str
    title: str
    link: str
    kind: str
    note: str | None = None
    question: str | None = None
    project_id: str | None = None
    project_title: str | None = None
    status: str
    review_note: str | None = None
    graded: bool = False
    submitted_at: str | None = None
