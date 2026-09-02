"""Build 10 readiness domain enums."""

from enum import StrEnum


class RoleSkillImportance(StrEnum):
    CORE = "core"
    IMPORTANT = "important"
    NICE_TO_HAVE = "nice_to_have"


class RoleSkillSource(StrEnum):
    MANUAL = "manual"
    SEED = "seed"


class MistakeSourceType(StrEnum):
    MCQ = "mcq"
    SQL = "sql"
    CODING = "coding"
    PROMPT = "prompt"
    SCENARIO = "scenario"
    INTERVIEW = "interview"


class MistakeStatus(StrEnum):
    OPEN = "open"
    REVIEWED = "reviewed"
    RESOLVED = "resolved"


class EvidenceStrength(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SkillReadinessStatus(StrEnum):
    STRONG = "strong"
    DEVELOPING = "developing"
    NEEDS_WORK = "needs_work"
    NO_EVIDENCE = "no_evidence"


class EvidenceSourceType(StrEnum):
    MCQ = "mcq"
    CODING = "coding"
    SQL = "sql"
    PROMPT = "prompt"
    SCENARIO = "scenario"
    COURSE = "course"
    PROJECT = "project"
    INTERVIEW = "interview"
    PRACTICE_PATH = "practice_path"
