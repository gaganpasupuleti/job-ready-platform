from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.coding_enums import ProblemProgressStatus, SubmissionStatus, SubmissionType
from app.models.enums import Difficulty


class LanguageInfo(BaseModel):
    id: int
    name: str


class SampleTestCasePublic(BaseModel):
    id: UUID
    name: str | None
    input: str
    expected_output: str
    explanation: str | None = None


class CodingProblemListItem(BaseModel):
    id: UUID
    slug: str
    title: str
    difficulty: Difficulty
    domain_id: UUID
    category_id: UUID
    topic_id: UUID
    topic_name: str | None = None
    topic_slug: str | None = None
    tags: list[str] = Field(default_factory=list)
    attempts: int | None = None
    acceptance_rate: float | None = None
    progress_status: ProblemProgressStatus | None = None
    bookmarked: bool | None = None


class DifficultyBreakdown(BaseModel):
    solved: int
    attempted: int
    total: int


class TopicBreakdown(BaseModel):
    topic_slug: str
    topic_name: str
    solved: int
    total: int


class CodingProgressSummary(BaseModel):
    total_problems: int
    solved_count: int
    attempted_count: int
    easy: DifficultyBreakdown | None = None
    medium: DifficultyBreakdown | None = None
    hard: DifficultyBreakdown | None = None
    topics: list[TopicBreakdown] = Field(default_factory=list)
    items: list[CodingProblemListItem]


class ExecutionStatusResponse(BaseModel):
    enabled: bool = False
    available: bool
    provider: str = "none"
    message: str | None = None
    languages: list[dict] = Field(default_factory=list)


class BookmarkedProblemItem(CodingProblemListItem):
    bookmarked_at: datetime | None = None


class CodingProblemListResponse(BaseModel):
    items: list[CodingProblemListItem]
    total: int


class CodingProblemDetail(BaseModel):
    id: UUID
    slug: str
    title: str
    description: str
    difficulty: Difficulty
    constraints: str | None
    input_format: str | None = None
    output_format: str | None = None
    tags: list[str] = Field(default_factory=list)
    time_limit_ms: int
    memory_limit_kb: int
    starter_code: dict[str, str]
    sample_test_cases: list[SampleTestCasePublic]
    supported_languages: list[LanguageInfo]
    progress_status: ProblemProgressStatus | None = None
    bookmarked: bool = False
    execution_available: bool = True
    hints: list[str] = Field(default_factory=list)
    solution_unlocked: bool = False
    solution: dict | None = None


class RunSubmitRequest(BaseModel):
    source_code: str = Field(min_length=1)
    language_id: int


class TestResultPublic(BaseModel):
    test_number: int
    name: str | None = None
    status: SubmissionStatus
    input: str | None = None
    expected_output: str | None = None
    stdout: str | None = None
    stderr: str | None = None
    execution_time_ms: float | None = None
    memory_kb: int | None = None
    is_hidden: bool = False


class ExecutionResponse(BaseModel):
    submission_id: UUID | None = None
    submission_type: SubmissionType
    status: SubmissionStatus
    passed_tests: int
    total_tests: int
    execution_time_ms: float | None = None
    memory_kb: int | None = None
    results: list[TestResultPublic]


class SubmissionListItem(BaseModel):
    id: UUID
    problem_id: UUID
    problem_title: str
    problem_difficulty: Difficulty | None = None
    language_name: str
    language_id: int
    submission_type: SubmissionType
    status: SubmissionStatus
    passed_tests: int
    total_tests: int
    execution_time_ms: float | None = None
    memory_kb: int | None = None
    created_at: datetime


class SubmissionListResponse(BaseModel):
    items: list[SubmissionListItem]
    total: int


class SubmissionDetail(ExecutionResponse):
    id: UUID
    problem_id: UUID
    problem_title: str
    problem_difficulty: Difficulty | None = None
    source_code: str
    language_id: int
    language_name: str
    created_at: datetime
    hidden_summary: str | None = None


class AdminTestCaseCreate(BaseModel):
    name: str | None = None
    input: str = ""
    expected_output: str
    is_hidden: bool = False
    is_sample: bool = False
    sort_order: int = 0
    explanation: str | None = None


class AdminTestCaseUpdate(BaseModel):
    name: str | None = None
    input: str | None = None
    expected_output: str | None = None
    is_hidden: bool | None = None
    is_sample: bool | None = None
    sort_order: int | None = None
    explanation: str | None = None


class AdminTestCaseDetail(AdminTestCaseCreate):
    id: UUID
    problem_id: UUID


class AdminCodingProblemCreate(BaseModel):
    slug: str
    title: str
    description: str
    difficulty: Difficulty
    domain_id: UUID
    category_id: UUID
    topic_id: UUID
    constraints: str | None = None
    input_format: str | None = None
    output_format: str | None = None
    tags: list[str] = Field(default_factory=list)
    supported_language_ids: list[int] = Field(default_factory=list)
    time_limit_ms: int = 2000
    memory_limit_kb: int = 262144
    starter_code: dict[str, str] = Field(default_factory=dict)
    is_active: bool = True
    is_sample: bool = True
    test_cases: list[AdminTestCaseCreate] = Field(default_factory=list)


class AdminCodingProblemUpdate(BaseModel):
    slug: str | None = None
    title: str | None = None
    description: str | None = None
    difficulty: Difficulty | None = None
    domain_id: UUID | None = None
    category_id: UUID | None = None
    topic_id: UUID | None = None
    constraints: str | None = None
    input_format: str | None = None
    output_format: str | None = None
    tags: list[str] | None = None
    supported_language_ids: list[int] | None = None
    time_limit_ms: int | None = None
    memory_limit_kb: int | None = None
    starter_code: dict[str, str] | None = None
    is_active: bool | None = None
    is_sample: bool | None = None


class AdminCodingProblemDetail(BaseModel):
    id: UUID
    slug: str
    title: str
    description: str
    difficulty: Difficulty
    domain_id: UUID
    category_id: UUID
    topic_id: UUID
    constraints: str | None
    input_format: str | None = None
    output_format: str | None = None
    tags: list[str] = Field(default_factory=list)
    supported_language_ids: list[int] = Field(default_factory=list)
    time_limit_ms: int
    memory_limit_kb: int
    starter_code: dict[str, str]
    is_active: bool
    is_sample: bool
    test_cases: list[AdminTestCaseDetail]


class AdminCodingProblemListResponse(BaseModel):
    items: list[CodingProblemListItem]
    total: int
