from enum import StrEnum


class UserRole(StrEnum):
    STUDENT = "student"
    ADMIN = "admin"
    TRAINER = "trainer"


class QuestionType(StrEnum):
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    NUMERIC = "numeric"
    FILL_BLANK = "fill_blank"
    CODING = "coding"
    SQL = "sql"
    WRITTEN = "written"
    VOICE = "voice"
    CASE_STUDY = "case_study"
    PROMPT_CHALLENGE = "prompt_challenge"


class Difficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class PracticeMode(StrEnum):
    PRACTICE = "practice"
    EXAM = "exam"


class SessionStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
