from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import Difficulty, QuestionType


class AdminOptionInput(BaseModel):
    id: UUID | None = None
    option_text: str
    is_correct: bool = False
    sort_order: int = 0


class AdminQuestionCreate(BaseModel):
    question_type: QuestionType
    title: str | None = None
    question_text: str
    explanation: str | None = None
    difficulty: Difficulty
    domain_id: UUID
    category_id: UUID
    topic_id: UUID
    subtopic_id: UUID | None = None
    marks: float = 1.0
    negative_marks: float = 0.0
    estimated_time_seconds: int = 60
    is_active: bool = True
    is_premium: bool = False
    skill_ids: list[UUID] = Field(default_factory=list)
    role_ids: list[UUID] = Field(default_factory=list)
    company_ids: list[UUID] = Field(default_factory=list)
    options: list[AdminOptionInput]


class AdminQuestionUpdate(BaseModel):
    question_type: QuestionType | None = None
    title: str | None = None
    question_text: str | None = None
    explanation: str | None = None
    difficulty: Difficulty | None = None
    domain_id: UUID | None = None
    category_id: UUID | None = None
    topic_id: UUID | None = None
    subtopic_id: UUID | None = None
    marks: float | None = None
    negative_marks: float | None = None
    estimated_time_seconds: int | None = None
    is_active: bool | None = None
    is_premium: bool | None = None
    skill_ids: list[UUID] | None = None
    role_ids: list[UUID] | None = None
    company_ids: list[UUID] | None = None
    options: list[AdminOptionInput] | None = None


class AdminQuestionListItem(BaseModel):
    id: UUID
    title: str | None
    question_text: str
    question_type: QuestionType
    difficulty: Difficulty
    domain_name: str
    category_name: str
    topic_name: str
    is_active: bool
    is_sample: bool


class AdminQuestionListResponse(BaseModel):
    questions: list[AdminQuestionListItem]
    total: int


class AdminQuestionDetail(BaseModel):
    id: UUID
    question_type: QuestionType
    title: str | None
    question_text: str
    explanation: str | None
    difficulty: Difficulty
    domain_id: UUID
    category_id: UUID
    topic_id: UUID
    subtopic_id: UUID | None
    marks: float
    negative_marks: float
    estimated_time_seconds: int
    is_active: bool
    is_premium: bool
    is_sample: bool
    skill_ids: list[UUID]
    role_ids: list[UUID]
    company_ids: list[UUID]
    options: list[AdminOptionInput]


class TaxonomyNodeCreate(BaseModel):
    name: str
    slug: str
    description: str | None = None
    is_active: bool = True


class TaxonomyItem(BaseModel):
    id: UUID
    name: str
    slug: str
    is_active: bool


class TaxonomyTreeResponse(BaseModel):
    domains: list[dict]
