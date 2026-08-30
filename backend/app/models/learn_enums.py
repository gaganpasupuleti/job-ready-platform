"""Enums for Practice Hub, courses, lessons, and projects."""

from enum import StrEnum


class PracticePathType(StrEnum):
    LANGUAGE = "language"
    PROJECT = "project"
    BEGINNER_DSA = "beginner_dsa"
    DATA_STRUCTURE = "data_structure"
    ALGORITHM = "algorithm"
    DIFFICULTY = "difficulty"
    COMPANY = "company"
    INTERVIEW = "interview"
    CUSTOM = "custom"


class PracticePathDifficulty(StrEnum):
    BEGINNER = "beginner"
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    MIXED = "mixed"


class PracticePathItemType(StrEnum):
    CODING_PROBLEM = "coding_problem"
    SQL_PROBLEM = "sql_problem"
    MCQ_TOPIC = "mcq_topic"
    LESSON = "lesson"
    PROJECT = "project"
    CHECKPOINT = "checkpoint"
    COURSE = "course"
    EXTERNAL_ROUTE = "external_route"


class PathAvailability(StrEnum):
    AVAILABLE = "available"
    COMING_SOON = "coming_soon"


class CourseLevel(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class LessonType(StrEnum):
    CONCEPT = "concept"
    INTERACTIVE_CODE = "interactive_code"
    MCQ = "mcq"
    PRACTICE = "practice"
    CHECKPOINT = "checkpoint"


class LessonUnlockMode(StrEnum):
    ALWAYS = "always"
    PREVIOUS_COMPLETE = "previous_complete"


class SolutionRevealPolicy(StrEnum):
    AFTER_COMPLETION = "after_completion"
    ALWAYS = "always"
    NEVER = "never"


class ProgressStatus(StrEnum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    LOCKED = "locked"


class LessonResourceType(StrEnum):
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    ARTICLE = "article"
    FILE = "file"


class LessonFeedbackVote(StrEnum):
    HELPFUL = "helpful"
    NOT_HELPFUL = "not_helpful"
