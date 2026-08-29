from enum import StrEnum


class SubmissionStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    ACCEPTED = "accepted"
    WRONG_ANSWER = "wrong_answer"
    TIME_LIMIT_EXCEEDED = "time_limit_exceeded"
    MEMORY_LIMIT_EXCEEDED = "memory_limit_exceeded"
    RUNTIME_ERROR = "runtime_error"
    COMPILATION_ERROR = "compilation_error"
    INTERNAL_ERROR = "internal_error"


class SubmissionType(StrEnum):
    RUN = "run"
    SUBMIT = "submit"


class ProblemProgressStatus(StrEnum):
    UNSOLVED = "unsolved"
    ATTEMPTED = "attempted"
    SOLVED = "solved"
