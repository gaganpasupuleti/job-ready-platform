from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import Difficulty
from app.models.sql_enums import SqlDialect, SqlProgressStatus, SqlSubmissionStatus


class SqlColumnSchema(BaseModel):
    column_name: str
    data_type: str
    is_nullable: bool = True
    sort_order: int = 0


class SqlTableSchemaPublic(BaseModel):
    table_name: str
    display_name: str | None = None
    description: str | None = None
    columns: list[SqlColumnSchema] = Field(default_factory=list)


class SqlTablePreview(BaseModel):
    table_name: str
    columns: list[str]
    rows: list[list[Any]]
    truncated: bool = False


class SqlProblemListItem(BaseModel):
    id: UUID
    slug: str
    title: str
    difficulty: Difficulty
    topic_id: UUID
    topic_name: str | None = None
    topic_slug: str | None = None
    tags: list[str] = Field(default_factory=list)
    role_tags: list[str] = Field(default_factory=list)
    estimated_time_seconds: int = 300
    progress_status: SqlProgressStatus | None = None
    acceptance_rate: float | None = None
    attempt_count: int | None = None


class SqlProblemDetail(BaseModel):
    id: UUID
    slug: str
    title: str
    description: str
    difficulty: Difficulty
    database_dialect: SqlDialect = SqlDialect.POSTGRESQL
    topic_id: UUID
    topic_name: str | None = None
    topic_slug: str | None = None
    tags: list[str] = Field(default_factory=list)
    role_tags: list[str] = Field(default_factory=list)
    scenario: str | None = None
    task_description: str
    expected_columns: list[str] = Field(default_factory=list)
    sample_expected_rows: list[list[Any]] = Field(default_factory=list)
    hints: list[str] = Field(default_factory=list)
    estimated_time_seconds: int = 300
    order_sensitive: bool = False
    schema_tables: list[SqlTableSchemaPublic] = Field(default_factory=list)
    progress_status: SqlProgressStatus | None = None
    bookmarked: bool = False
    solution_unlocked: bool = False
    execution_available: bool = True


class SqlRunRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=20000)


class SqlRunResponse(BaseModel):
    columns: list[str] = Field(default_factory=list)
    rows: list[list[Any]] = Field(default_factory=list)
    row_count: int = 0
    execution_time_ms: float | None = None
    truncated: bool = False
    error: str | None = None
    status: str = "ok"


class SqlSubmitResponse(BaseModel):
    submission_id: UUID | None = None
    status: SqlSubmissionStatus
    message: str
    execution_time_ms: float | None = None
    result_row_count: int | None = None
    feedback: dict[str, Any] | None = None
    columns: list[str] = Field(default_factory=list)
    rows: list[list[Any]] = Field(default_factory=list)
    truncated: bool = False
    error: str | None = None
    solution_unlocked: bool = False


class SqlSubmissionListItem(BaseModel):
    id: UUID
    problem_id: UUID
    problem_slug: str
    problem_title: str
    difficulty: Difficulty | None = None
    topic_name: str | None = None
    status: SqlSubmissionStatus
    result_row_count: int | None = None
    execution_time_ms: float | None = None
    submitted_at: datetime


class SqlSubmissionDetail(BaseModel):
    id: UUID
    problem_id: UUID
    problem_slug: str
    problem_title: str
    difficulty: Difficulty | None = None
    query_text: str
    status: SqlSubmissionStatus
    result_row_count: int | None = None
    execution_time_ms: float | None = None
    error_message: str | None = None
    feedback: dict[str, Any] | None = None
    submitted_at: datetime


class DifficultyBreakdown(BaseModel):
    solved: int = 0
    total: int = 0
    attempted: int = 0


class TopicBreakdown(BaseModel):
    topic_slug: str
    topic_name: str
    solved: int = 0
    total: int = 0


class SqlProgressSummary(BaseModel):
    total_problems: int
    solved_count: int
    attempted_count: int
    easy: DifficultyBreakdown = Field(default_factory=DifficultyBreakdown)
    medium: DifficultyBreakdown = Field(default_factory=DifficultyBreakdown)
    hard: DifficultyBreakdown = Field(default_factory=DifficultyBreakdown)
    topics: list[TopicBreakdown] = Field(default_factory=list)


class SqlSolutionResponse(BaseModel):
    solution_query: str
    solution_explanation: str | None = None
    alternate_solution: str | None = None
    key_concepts: list[str] = Field(default_factory=list)


class SqlExecutionStatusResponse(BaseModel):
    available: bool
    status: str = "available"  # available | disabled | sandbox_unavailable
    dialect: str = "postgresql"
    message: str | None = None
    timeout_ms: int | None = None
    max_rows: int | None = None


# --- Admin schemas ---


class AdminSqlColumnInput(BaseModel):
    column_name: str
    data_type: str
    is_nullable: bool = True
    sort_order: int = 0


class AdminSqlTableInput(BaseModel):
    table_name: str
    display_name: str | None = None
    description: str | None = None
    sort_order: int = 0
    columns: list[AdminSqlColumnInput] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)


class AdminSqlProblemCreate(BaseModel):
    slug: str
    title: str
    description: str
    difficulty: Difficulty
    domain_id: UUID
    category_id: UUID
    topic_id: UUID
    subtopic_id: UUID | None = None
    tags: list[str] = Field(default_factory=list)
    role_tags: list[str] = Field(default_factory=list)
    scenario: str | None = None
    task_description: str
    expected_columns: list[str] = Field(default_factory=list)
    order_sensitive: bool = False
    solution_query: str
    solution_explanation: str | None = None
    alternate_solution: str | None = None
    key_concepts: list[str] = Field(default_factory=list)
    hints: list[str] = Field(default_factory=list)
    sample_expected_rows: list[list[Any]] = Field(default_factory=list)
    estimated_time_seconds: int = 300
    is_active: bool = True
    is_sample: bool = True
    tables: list[AdminSqlTableInput] = Field(default_factory=list)
    expected_rows: list[list[Any]] = Field(default_factory=list)


class AdminSqlProblemUpdate(BaseModel):
    slug: str | None = None
    title: str | None = None
    description: str | None = None
    difficulty: Difficulty | None = None
    domain_id: UUID | None = None
    category_id: UUID | None = None
    topic_id: UUID | None = None
    subtopic_id: UUID | None = None
    tags: list[str] | None = None
    role_tags: list[str] | None = None
    scenario: str | None = None
    task_description: str | None = None
    expected_columns: list[str] | None = None
    order_sensitive: bool | None = None
    solution_query: str | None = None
    solution_explanation: str | None = None
    alternate_solution: str | None = None
    key_concepts: list[str] | None = None
    hints: list[str] | None = None
    sample_expected_rows: list[list[Any]] | None = None
    estimated_time_seconds: int | None = None
    is_active: bool | None = None
    is_sample: bool | None = None
    tables: list[AdminSqlTableInput] | None = None
    expected_rows: list[list[Any]] | None = None


class AdminSqlProblemDetail(BaseModel):
    id: UUID
    slug: str
    title: str
    description: str
    difficulty: Difficulty
    database_dialect: SqlDialect
    domain_id: UUID
    category_id: UUID
    topic_id: UUID
    subtopic_id: UUID | None = None
    tags: list[str]
    role_tags: list[str]
    scenario: str | None
    task_description: str
    expected_columns: list[str]
    order_sensitive: bool
    solution_query: str
    solution_explanation: str | None
    alternate_solution: str | None
    key_concepts: list[str]
    hints: list[str]
    sample_expected_rows: list[list[Any]]
    estimated_time_seconds: int
    is_active: bool
    is_sample: bool
    tables: list[AdminSqlTableInput]
    expected_rows: list[list[Any]]


class AdminSqlProblemListResponse(BaseModel):
    items: list[SqlProblemListItem]
    total: int


class AdminSqlValidateResponse(BaseModel):
    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    solution_columns: list[str] = Field(default_factory=list)
    solution_row_count: int | None = None
