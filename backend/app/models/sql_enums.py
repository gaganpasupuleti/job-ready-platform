from enum import StrEnum


class SqlDialect(StrEnum):
    POSTGRESQL = "postgresql"


class SqlSubmissionStatus(StrEnum):
    ACCEPTED = "accepted"
    WRONG_ANSWER = "wrong_answer"
    SQL_ERROR = "sql_error"
    TIMEOUT = "timeout"
    EXECUTION_DISABLED = "execution_disabled"
    INTERNAL_ERROR = "internal_error"


class SqlProgressStatus(StrEnum):
    UNSOLVED = "unsolved"
    ATTEMPTED = "attempted"
    SOLVED = "solved"
