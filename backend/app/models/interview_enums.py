from enum import StrEnum


class InterviewQuestionType(StrEnum):
    TECHNICAL = "technical"
    HR = "hr"
    BEHAVIORAL = "behavioral"
    SCENARIO = "scenario"
    CONCEPTUAL = "conceptual"
    TROUBLESHOOTING = "troubleshooting"
    ARCHITECTURE = "architecture"
    SITUATIONAL = "situational"


class ExperienceLevel(StrEnum):
    FRESHER = "fresher"
    JUNIOR = "junior"
    INTERMEDIATE = "intermediate"
    SENIOR = "senior"


class ContentSourceType(StrEnum):
    MANUAL = "manual"
    CURSOR_GENERATED = "cursor_generated"
    IMPORTED = "imported"


class ContentReviewStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ContentValidationStatus(StrEnum):
    PENDING = "pending"
    VALID = "valid"
    INVALID = "invalid"


class ContentBatchStatus(StrEnum):
    PENDING = "pending"
    IMPORTED = "imported"
    COMPLETED = "completed"
    FAILED = "failed"


class ContentType(StrEnum):
    INTERVIEW_QA = "interview_qa"
    COURSE = "course"
    LESSON = "lesson"
    PRACTICE_PATH = "practice_path"
    PROJECT = "project"
