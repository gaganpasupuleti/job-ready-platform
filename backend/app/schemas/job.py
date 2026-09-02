"""Pydantic schemas for Build 9 jobs domain."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.job_enums import (
    ApplicationPriority,
    ApplicationStatus,
    EmploymentType,
    IngestionRunStatus,
    JobSkillImportance,
    JobSourceType,
    JobStatus,
    WorkMode,
)


class JobSkillPublic(BaseModel):
    id: UUID
    name: str
    slug: str
    importance: JobSkillImportance


class JobRolePublic(BaseModel):
    id: UUID
    name: str
    slug: str
    mapping_source: str | None = None


class JobCard(BaseModel):
    id: UUID
    slug: str
    title: str
    company_name: str
    company_slug: str | None = None
    location_text: str | None = None
    work_mode: WorkMode | None = None
    employment_type: EmploymentType | None = None
    experience_min_years: int | None = None
    experience_max_years: int | None = None
    posted_at: datetime | None = None
    status: JobStatus
    is_remote: bool | None = None
    top_skills: list[str] = []
    is_saved: bool = False
    requirement_coverage: float | None = None
    has_sufficient_mapping: bool | None = None
    missing_skill_count: int | None = None


class JobListResponse(BaseModel):
    items: list[JobCard]
    total: int
    page: int
    limit: int


class JobPracticeLink(BaseModel):
    label: str
    path: str
    reason: str | None = None


class JobDetail(BaseModel):
    id: UUID
    slug: str
    title: str
    company_name: str
    company_slug: str | None = None
    company_id: UUID | None = None
    description: str
    requirements_text: str | None = None
    responsibilities_text: str | None = None
    employment_type: EmploymentType | None = None
    work_mode: WorkMode | None = None
    experience_min_years: int | None = None
    experience_max_years: int | None = None
    salary_min: Decimal | None = None
    salary_max: Decimal | None = None
    salary_currency: str | None = None
    location_text: str | None = None
    country: str | None = None
    state: str | None = None
    city: str | None = None
    source_url: str | None = None
    apply_url: str | None = None
    posted_at: datetime | None = None
    expires_at: datetime | None = None
    status: JobStatus
    is_remote: bool | None = None
    source_name: str | None = None
    skills: list[JobSkillPublic] = []
    roles: list[JobRolePublic] = []
    is_saved: bool = False
    application_id: UUID | None = None
    application_status: ApplicationStatus | None = None
    practice_links: list[JobPracticeLink] = []
    interview_prep_url: str | None = None
    company_prep_url: str | None = None
    match: dict[str, Any] | None = None


class SavedJobItem(BaseModel):
    id: UUID
    job_id: UUID
    saved_at: datetime
    job: JobCard


class ApplicationSummary(BaseModel):
    id: UUID
    job_id: UUID
    job_title: str
    company_name: str
    status: ApplicationStatus
    applied_at: datetime | None = None
    next_follow_up_at: datetime | None = None
    priority: ApplicationPriority
    job_status: JobStatus


class ApplicationDetail(BaseModel):
    id: UUID
    job_id: UUID
    status: ApplicationStatus
    applied_at: datetime | None = None
    next_follow_up_at: datetime | None = None
    source_of_application: str | None = None
    application_url: str | None = None
    notes: str | None = None
    salary_expected: Decimal | None = None
    priority: ApplicationPriority
    created_at: datetime
    updated_at: datetime
    job: JobDetail


class ApplicationStatusHistoryItem(BaseModel):
    id: UUID
    from_status: ApplicationStatus | None = None
    to_status: ApplicationStatus
    note: str | None = None
    changed_at: datetime


class ApplicationUpdate(BaseModel):
    status: ApplicationStatus | None = None
    next_follow_up_at: datetime | None = None
    notes: str | None = None
    salary_expected: Decimal | None = None
    priority: ApplicationPriority | None = None
    application_url: str | None = None
    source_of_application: str | None = None


class ApplicationStatusChange(BaseModel):
    to_status: ApplicationStatus
    note: str | None = None


class JobsSummary(BaseModel):
    saved_count: int
    applications_total: int
    applied_count: int
    interview_count: int
    offer_count: int
    rejected_count: int
    follow_ups_due: int
    follow_ups_today: int
    follow_ups_overdue: int


class JobPreferenceUpdate(BaseModel):
    target_role_slug: str | None = None
    preferred_locations: list[str] | None = None
    remote_preference: WorkMode | None = None


class JobSourcePublic(BaseModel):
    id: UUID
    name: str
    slug: str
    source_type: JobSourceType
    is_active: bool


class AdminJobCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    company_name: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=10)
    requirements_text: str | None = None
    responsibilities_text: str | None = None
    employment_type: EmploymentType | None = None
    work_mode: WorkMode | None = None
    experience_min_years: int | None = Field(default=None, ge=0, le=50)
    experience_max_years: int | None = Field(default=None, ge=0, le=50)
    location_text: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    is_remote: bool | None = None
    source_url: str | None = None
    apply_url: str | None = None
    posted_at: datetime | None = None
    expires_at: datetime | None = None
    skills: list[str] = []
    roles: list[str] = []
    status: JobStatus = JobStatus.ACTIVE


class AdminJobUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    company_name: str | None = None
    description: str | None = None
    requirements_text: str | None = None
    responsibilities_text: str | None = None
    employment_type: EmploymentType | None = None
    work_mode: WorkMode | None = None
    experience_min_years: int | None = Field(default=None, ge=0, le=50)
    experience_max_years: int | None = Field(default=None, ge=0, le=50)
    location_text: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    is_remote: bool | None = None
    source_url: str | None = None
    apply_url: str | None = None
    posted_at: datetime | None = None
    expires_at: datetime | None = None
    skills: list[str] | None = None
    roles: list[str] | None = None
    status: JobStatus | None = None


class ImportPreviewRow(BaseModel):
    row_number: int
    title: str
    company: str
    action: str
    errors: list[str] = []


class ImportPreviewResponse(BaseModel):
    run_id: UUID | None = None
    rows: list[ImportPreviewRow]
    valid_count: int
    error_count: int
    create_count: int
    update_count: int
    duplicate_count: int


class ImportConfirmResponse(BaseModel):
    run_id: UUID
    status: IngestionRunStatus
    records_created: int
    records_updated: int
    records_skipped: int
    records_failed: int


class IngestionRunPublic(BaseModel):
    id: UUID
    source_id: UUID | None = None
    source_name: str | None = None
    started_at: datetime
    completed_at: datetime | None = None
    status: IngestionRunStatus
    records_seen: int
    records_created: int
    records_updated: int
    records_skipped: int
    records_failed: int
    source_file_name: str | None = None


class ImportConfirmRequest(BaseModel):
    preview_id: UUID
    filename: str | None = None


class IngestionErrorPublic(BaseModel):
    id: UUID
    row_number: int | None = None
    external_id: str | None = None
    error_type: str
    message: str
