"""Build 9 jobs domain — postings, saved jobs, applications, ingestion."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.job_enums import (
    ApplicationPriority,
    ApplicationStatus,
    EmploymentType,
    IngestionRunStatus,
    JobRoleMappingSource,
    JobSkillImportance,
    JobSourceType,
    JobStatus,
    WorkMode,
)


class JobSource(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "job_sources"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    source_type: Mapped[JobSourceType] = mapped_column(
        Enum(JobSourceType, name="job_source_type", native_enum=False, values_callable=lambda enum: [e.value for e in enum]),
        nullable=False,
    )
    base_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Job(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Job posting — table `jobs` (expanded from content-factory stub)."""

    __tablename__ = "jobs"

    slug: Mapped[str] = mapped_column(String(180), unique=True, index=True, nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_sources.id", ondelete="SET NULL"), nullable=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_title: Mapped[str] = mapped_column(String(255), index=True, nullable=False)

    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True
    )
    company_name_raw: Mapped[str | None] = mapped_column(String(255), nullable=True)

    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    requirements_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    responsibilities_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    employment_type: Mapped[EmploymentType | None] = mapped_column(
        Enum(EmploymentType, name="job_employment_type", native_enum=False, values_callable=lambda enum: [e.value for e in enum]),
        nullable=True,
    )
    work_mode: Mapped[WorkMode | None] = mapped_column(
        Enum(WorkMode, name="job_work_mode", native_enum=False, values_callable=lambda enum: [e.value for e in enum]),
        nullable=True,
    )

    experience_min_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    experience_max_years: Mapped[int | None] = mapped_column(Integer, nullable=True)

    salary_min: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    salary_max: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    salary_currency: Mapped[str | None] = mapped_column(String(8), nullable=True)

    location_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    country: Mapped[str | None] = mapped_column(String(120), nullable=True)
    state: Mapped[str | None] = mapped_column(String(120), nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)

    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    apply_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status", native_enum=False, values_callable=lambda enum: [e.value for e in enum]),
        default=JobStatus.ACTIVE,
        nullable=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_remote: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    content_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    source: Mapped[JobSource | None] = relationship("JobSource")
    skills: Mapped[list["JobSkill"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    roles: Mapped[list["JobRoleMap"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    locations: Mapped[list["JobLocation"]] = relationship(back_populates="job", cascade="all, delete-orphan")


# Backward-compatible alias used by interview content factory
JobListing = Job


class JobSkill(Base):
    __tablename__ = "job_skills"
    __table_args__ = (UniqueConstraint("job_id", "skill_id", name="uq_job_skills_job_skill"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True
    )
    importance: Mapped[JobSkillImportance] = mapped_column(
        Enum(JobSkillImportance, name="job_skill_importance", native_enum=False, values_callable=lambda enum: [e.value for e in enum]),
        default=JobSkillImportance.MENTIONED,
        nullable=False,
    )

    job: Mapped[Job] = relationship(back_populates="skills")


class JobRoleMap(Base):
    __tablename__ = "job_role_mappings"
    __table_args__ = (UniqueConstraint("job_id", "role_id", name="uq_job_role_mappings_job_role"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_roles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    mapping_source: Mapped[JobRoleMappingSource] = mapped_column(
        Enum(JobRoleMappingSource, name="job_role_mapping_source", native_enum=False, values_callable=lambda enum: [e.value for e in enum]),
        default=JobRoleMappingSource.RULE,
        nullable=False,
    )

    job: Mapped[Job] = relationship(back_populates="roles")


class JobLocation(Base):
    __tablename__ = "job_locations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    location_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    state: Mapped[str | None] = mapped_column(String(120), nullable=True)
    country: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_remote: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    job: Mapped[Job] = relationship(back_populates="locations")


class SavedJob(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "saved_jobs"
    __table_args__ = (UniqueConstraint("user_id", "job_id", name="uq_saved_jobs_user_job"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )


class JobApplication(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "job_applications"
    __table_args__ = (UniqueConstraint("user_id", "job_id", name="uq_job_applications_user_job"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )

    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, name="application_status", native_enum=False, values_callable=lambda enum: [e.value for e in enum]),
        default=ApplicationStatus.SAVED,
        nullable=False,
        index=True,
    )
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_follow_up_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    source_of_application: Mapped[str | None] = mapped_column(String(120), nullable=True)
    application_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    salary_expected: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    priority: Mapped[ApplicationPriority] = mapped_column(
        Enum(ApplicationPriority, name="application_priority", native_enum=False, values_callable=lambda enum: [e.value for e in enum]),
        default=ApplicationPriority.MEDIUM,
        nullable=False,
    )


class ApplicationStatusHistory(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "application_status_history"

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("job_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_status: Mapped[ApplicationStatus | None] = mapped_column(
        Enum(ApplicationStatus, name="application_status_hist", native_enum=False, values_callable=lambda enum: [e.value for e in enum]),
        nullable=True,
    )
    to_status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, name="application_status_hist_to", native_enum=False, values_callable=lambda enum: [e.value for e in enum]),
        nullable=False,
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class JobIngestionRun(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "job_ingestion_runs"

    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_sources.id", ondelete="SET NULL"), nullable=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[IngestionRunStatus] = mapped_column(
        Enum(IngestionRunStatus, name="ingestion_run_status", native_enum=False, values_callable=lambda enum: [e.value for e in enum]),
        nullable=False,
    )
    records_seen: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_skipped: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    source_file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)


class JobIngestionError(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "job_ingestion_errors"

    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("job_ingestion_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    row_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_type: Mapped[str] = mapped_column(String(80), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    raw_payload_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )


class UserJobPreference(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "user_job_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    target_role_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_roles.id", ondelete="SET NULL"), nullable=True
    )
    preferred_locations_json: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    remote_preference: Mapped[WorkMode | None] = mapped_column(
        Enum(WorkMode, name="user_remote_preference", native_enum=False, values_callable=lambda enum: [e.value for e in enum]),
        nullable=True,
    )
