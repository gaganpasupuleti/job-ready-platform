from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import Difficulty, PracticeMode, QuestionType


class SubtopicBrief(BaseModel):
    id: UUID
    name: str
    slug: str


class TopicBrief(BaseModel):
    id: UUID
    name: str
    slug: str
    subtopics: list[SubtopicBrief] = Field(default_factory=list)


class CategoryBrief(BaseModel):
    id: UUID
    name: str
    slug: str
    topics: list[TopicBrief] = Field(default_factory=list)


class DomainBrief(BaseModel):
    id: UUID
    name: str
    slug: str
    categories: list[CategoryBrief] = Field(default_factory=list)


class CatalogResponse(BaseModel):
    domains: list[DomainBrief]


class CreateSessionRequest(BaseModel):
    category_id: UUID | None = None
    topic_id: UUID | None = None
    difficulty: Difficulty | None = None
    question_count: int = Field(default=10, ge=1, le=50)
    mode: PracticeMode = PracticeMode.PRACTICE
    duration_minutes: int | None = Field(default=None, ge=1, le=180)


class SessionSummary(BaseModel):
    id: UUID
    mode: PracticeMode
    status: str
    question_count: int
    score: float
    correct_count: int
    incorrect_count: int
    unanswered_count: int
    started_at: str
    completed_at: str | None = None
    duration_minutes: int | None = None
    expires_at: str | None = None
    remaining_seconds: int | None = None


class SessionDetailResponse(SessionSummary):
    category_id: UUID | None = None
    topic_id: UUID | None = None
    difficulty: Difficulty | None = None
    answered_count: int = 0


class QuestionOptionPublic(BaseModel):
    id: UUID
    option_text: str
    sort_order: int


class QuestionPublic(BaseModel):
    id: UUID
    question_type: QuestionType
    title: str | None
    question_text: str
    difficulty: Difficulty
    marks: float
    negative_marks: float
    estimated_time_seconds: int
    options: list[QuestionOptionPublic]
    topic_name: str | None = None
    skills: list[str] = Field(default_factory=list)


class SessionQuestionResponse(BaseModel):
    question_number: int
    total_questions: int
    question: QuestionPublic
    answered: bool = False
    bookmarked: bool = False
    marked_for_review: bool = False
    selected_option_ids: list[UUID] = Field(default_factory=list)


class AutosaveRequest(BaseModel):
    selected_option_ids: list[UUID] = Field(default_factory=list)
    marked_for_review: bool = False
    time_spent_seconds: int = Field(default=0, ge=0)


class NavigatorItem(BaseModel):
    question_number: int
    answered: bool
    marked_for_review: bool


class SessionNavigatorResponse(BaseModel):
    current_question: int
    items: list[NavigatorItem]


class AnswerRequest(BaseModel):
    selected_option_ids: list[UUID] = Field(default_factory=list)
    time_spent_seconds: int = Field(default=0, ge=0)


class AnswerOptionFeedback(BaseModel):
    id: UUID
    option_text: str
    is_correct: bool


class AnswerFeedback(BaseModel):
    is_correct: bool
    marks_awarded: float
    correct_option_ids: list[UUID]
    selected_option_ids: list[UUID]
    explanation: str | None = None
    options: list[AnswerOptionFeedback] = Field(default_factory=list)
    topic_name: str | None = None
    difficulty: Difficulty | None = None
    skills: list[str] = Field(default_factory=list)
    reveal_feedback: bool = True


class AnswerResponse(BaseModel):
    question_number: int
    answered: bool
    feedback: AnswerFeedback | None = None


class TopicPerformance(BaseModel):
    topic_name: str
    accuracy: float
    total: int
    correct: int


class QuestionReviewItem(BaseModel):
    question_number: int
    question_text: str
    selected_option_ids: list[UUID]
    correct_option_ids: list[UUID]
    selected_option_texts: list[str]
    correct_option_texts: list[str]
    explanation: str | None
    is_correct: bool
    marks_awarded: float


class SessionResultsResponse(BaseModel):
    session: SessionSummary
    accuracy: float
    time_taken_seconds: int
    topic_performance: list[TopicPerformance]
    questions: list[QuestionReviewItem]


class HistoryItem(BaseModel):
    id: UUID
    mode: PracticeMode
    status: str
    question_count: int
    score: float
    correct_count: int
    incorrect_count: int
    started_at: str
    completed_at: str | None = None
    category_name: str | None = None
    topic_name: str | None = None


class HistoryResponse(BaseModel):
    sessions: list[HistoryItem]
