"""Enums for Build 9 jobs domain."""

from enum import StrEnum


class JobSourceType(StrEnum):
    MANUAL = "manual"
    IMPORT = "import"
    DONOR = "donor"
    API = "api"
    CAREER_SITE = "career_site"


class JobListingType(StrEnum):
    """Provenance / visibility kind — not the ingestion channel (JobSourceType)."""

    REAL = "real"
    SAMPLE_DEMO = "sample_demo"
    CURATED_IMPORT = "curated_import"
    MANUAL = "manual"
    CAREER_SITE = "career_site"


class JobStatus(StrEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    ARCHIVED = "archived"


class JobSkillImportance(StrEnum):
    REQUIRED = "required"
    PREFERRED = "preferred"
    MENTIONED = "mentioned"


class JobRoleMappingSource(StrEnum):
    MANUAL = "manual"
    RULE = "rule"
    IMPORTED = "imported"


class WorkMode(StrEnum):
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"
    UNKNOWN = "unknown"


class EmploymentType(StrEnum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    UNKNOWN = "unknown"


class ApplicationStatus(StrEnum):
    SAVED = "saved"
    PREPARING = "preparing"
    APPLIED = "applied"
    SCREENING = "screening"
    ASSESSMENT = "assessment"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    ACCEPTED = "accepted"
    GHOSTED = "ghosted"


class ApplicationPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class IngestionRunStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"
