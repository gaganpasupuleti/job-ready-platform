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
    INTERVIEW_PACK = "interview_pack"


class InterviewSessionMode(StrEnum):
    STUDY = "study"
    MOCK = "mock"
    RAPID_REVIEW = "rapid_review"


class InterviewSessionSource(StrEnum):
    PACK = "pack"
    CUSTOM_FILTER = "custom_filter"
    RETRY_REVIEW = "retry_review"


class InterviewSessionStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class InterviewSessionQuestionStatus(StrEnum):
    UNSEEN = "unseen"
    VIEWED = "viewed"
    REVIEWED = "reviewed"
    COMPLETED = "completed"


class InterviewConfidence(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class InterviewSelfRating(StrEnum):
    NEEDS_REVIEW = "needs_review"
    PARTIAL = "partial"
    GOOD = "good"
    STRONG = "strong"
