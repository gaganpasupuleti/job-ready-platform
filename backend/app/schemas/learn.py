# ruff: noqa: E501
"""Pydantic schemas for Practice Hub, courses, lessons, projects."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class PracticePathCard(BaseModel):
    id: UUID
    slug: str
    title: str
    short_description: str
    path_type: str
    difficulty: str
    language: str | None = None
    estimated_minutes: int | None = None
    availability: str
    is_featured: bool = False
    external_route: str | None = None
    item_count: int = 0
    progress_percent: int = 0


class PracticeHubSection(BaseModel):
    key: str
    label: str
    paths: list[PracticePathCard] = Field(default_factory=list)


class ContinueLearningItem(BaseModel):
    kind: str
    title: str
    subtitle: str | None = None
    progress_percent: int = 0
    href: str
    last_activity_at: datetime | None = None


class PracticeHubResponse(BaseModel):
    sections: list[PracticeHubSection]
    continue_learning: list[ContinueLearningItem] = Field(default_factory=list)
    recently_practiced: list[ContinueLearningItem] = Field(default_factory=list)
    recommended: list[PracticePathCard] = Field(default_factory=list)
    search_hint: str = "Search paths, courses, and projects"


class PracticePathItemOut(BaseModel):
    id: UUID
    item_type: str
    title: str | None = None
    sort_order: int
    href: str | None = None
    coding_problem_id: UUID | None = None
    course_id: UUID | None = None
    lesson_id: UUID | None = None
    project_id: UUID | None = None
    external_route: str | None = None


class PracticePathSectionOut(BaseModel):
    id: UUID
    title: str
    section_key: str | None = None
    sort_order: int
    items: list[PracticePathItemOut] = Field(default_factory=list)


class PracticePathDetail(BaseModel):
    id: UUID
    slug: str
    title: str
    short_description: str
    description: str | None = None
    path_type: str
    difficulty: str
    language: str | None = None
    estimated_minutes: int | None = None
    availability: str
    external_route: str | None = None
    progress_percent: int = 0
    sections: list[PracticePathSectionOut] = Field(default_factory=list)


class CourseListItem(BaseModel):
    id: UUID
    slug: str
    title: str
    summary: str
    level: str
    primary_language_key: str | None = None
    estimated_minutes: int | None = None
    lesson_count: int = 0
    progress_percent: int = 0
    is_featured: bool = False


class LessonNavItem(BaseModel):
    id: UUID
    slug: str
    title: str
    lesson_type: str
    sort_order: int
    status: str
    module_slug: str
    module_title: str


class ModuleOut(BaseModel):
    id: UUID
    slug: str
    title: str
    sort_order: int
    summary: str | None = None
    lessons: list[LessonNavItem] = Field(default_factory=list)
    completed_count: int = 0
    lesson_count: int = 0


class CourseDetail(BaseModel):
    id: UUID
    slug: str
    title: str
    summary: str
    level: str
    primary_language_key: str | None = None
    estimated_minutes: int | None = None
    progress_percent: int = 0
    status: str = "not_started"
    continue_href: str | None = None
    modules: list[ModuleOut] = Field(default_factory=list)


class LessonHintOut(BaseModel):
    id: UUID
    hint_text: str
    sort_order: int
    unlocked: bool = True


class LessonDoubtOut(BaseModel):
    id: UUID
    question: str
    answer: str
    sort_order: int


class LessonResourceOut(BaseModel):
    id: UUID
    resource_type: str
    title: str
    url: str
    description: str | None = None


class LessonStepOut(BaseModel):
    id: UUID
    title: str
    body_md: str
    sort_order: int


class LessonDetail(BaseModel):
    id: UUID
    slug: str
    title: str
    lesson_type: str
    statement_json: dict[str, Any]
    starter_code: dict[str, Any] = Field(default_factory=dict)
    coding_problem_id: UUID | None = None
    coding_problem_slug: str | None = None
    question_id: UUID | None = None
    status: str
    attempts: int = 0
    solution_unlocked: bool = False
    solution_json: dict[str, Any] | None = None
    hints: list[LessonHintOut] = Field(default_factory=list)
    doubts: list[LessonDoubtOut] = Field(default_factory=list)
    resources: list[LessonResourceOut] = Field(default_factory=list)
    steps: list[LessonStepOut] = Field(default_factory=list)
    progress_blocks: list[LessonNavItem] = Field(default_factory=list)
    prev_href: str | None = None
    next_href: str | None = None
    course_slug: str
    module_slug: str
    completion_requires_submit: bool = False
    can_mark_complete: bool = True


class LessonFeedbackIn(BaseModel):
    vote: str | None = None
    report_issue: bool = False
    note: str | None = None


class ProjectCard(BaseModel):
    id: UUID
    slug: str
    title: str
    short_description: str
    difficulty: str
    technology: str | None = None
    category_key: str
    availability: str
    estimated_minutes: int | None = None
    task_count: int = 0
    progress_percent: int = 0
    href: str


class ProjectTaskOut(BaseModel):
    id: UUID
    title: str
    sort_order: int
    summary: str | None = None
    task_type: str = "concept"
    status: str = "not_started"
    href: str | None = None
    lesson_id: UUID | None = None
    coding_problem_id: UUID | None = None
    sql_problem_id: UUID | None = None
    topic_id: UUID | None = None
    body_json: dict[str, Any] = Field(default_factory=dict)
    checklist_json: list[Any] = Field(default_factory=list)
    reference_json: dict[str, Any] | None = None
    estimated_minutes: int | None = None


class ProjectModuleOut(BaseModel):
    id: UUID
    title: str
    sort_order: int
    tasks: list[ProjectTaskOut] = Field(default_factory=list)


class ProjectDetail(BaseModel):
    id: UUID
    slug: str
    title: str
    short_description: str
    description: str | None = None
    difficulty: str
    technology: str | None = None
    category_key: str
    availability: str
    estimated_minutes: int | None = None
    prerequisites: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    final_objective: str | None = None
    reference_json: dict[str, Any] | None = None
    progress_percent: int = 0
    status: str = "not_started"
    completed_task_count: int = 0
    task_count: int = 0
    current_task_id: UUID | None = None
    current_task_href: str | None = None
    continue_href: str | None = None
    last_activity_at: datetime | None = None
    completed_at: datetime | None = None
    modules: list[ProjectModuleOut] = Field(default_factory=list)


class SearchHit(BaseModel):
    kind: str
    slug: str
    title: str
    subtitle: str | None = None
    href: str


class SearchResponse(BaseModel):
    items: list[SearchHit] = Field(default_factory=list)


class PracticePathAdminIn(BaseModel):
    slug: str
    title: str
    short_description: str = ""
    description: str | None = None
    path_type: str
    difficulty: str = "beginner"
    language: str | None = None
    estimated_minutes: int | None = None
    availability: str = "available"
    is_active: bool = True
    is_featured: bool = False
    sort_order: int = 0
    external_route: str | None = None


class CourseAdminIn(BaseModel):
    slug: str
    title: str
    summary: str = ""
    level: str = "beginner"
    primary_language_key: str | None = None
    estimated_minutes: int | None = None
    is_published: bool = False
    is_featured: bool = False
    sort_order: int = 0


class ModuleAdminIn(BaseModel):
    slug: str
    title: str
    sort_order: int = 0
    summary: str | None = None


class LessonAdminIn(BaseModel):
    slug: str
    title: str
    sort_order: int = 0
    lesson_type: str
    statement_json: dict[str, Any] = Field(default_factory=dict)
    starter_code: dict[str, Any] = Field(default_factory=dict)
    solution_json: dict[str, Any] | None = None
    solution_reveal: str = "after_completion"
    unlock_mode: str = "previous_complete"
    coding_problem_id: UUID | None = None
    question_id: UUID | None = None
    is_published: bool = False
    completion_requires_submit: bool = False
    estimated_minutes: int | None = None
    hints: list[dict[str, Any]] = Field(default_factory=list)
    doubts: list[dict[str, Any]] = Field(default_factory=list)


class ProjectAdminIn(BaseModel):
    slug: str
    title: str
    short_description: str = ""
    description: str | None = None
    difficulty: str = "beginner"
    technology: str | None = None
    category_key: str
    estimated_minutes: int | None = None
    is_published: bool = False
    is_featured: bool = False
    sort_order: int = 0
    availability: str = "available"
    prerequisites: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    final_objective: str | None = None
    reference_json: dict[str, Any] | None = None


class ProjectModuleAdminIn(BaseModel):
    title: str
    sort_order: int = 0


class ProjectTaskAdminIn(BaseModel):
    title: str
    sort_order: int = 0
    task_type: str = "concept"
    summary: str | None = None
    coding_problem_id: UUID | None = None
    sql_problem_id: UUID | None = None
    topic_id: UUID | None = None
    lesson_id: UUID | None = None
    question_id: UUID | None = None
    body_json: dict[str, Any] = Field(default_factory=dict)
    checklist_json: list[Any] = Field(default_factory=list)
    reference_json: dict[str, Any] | None = None
    estimated_minutes: int | None = None


class PracticePathSectionAdminIn(BaseModel):
    title: str
    section_key: str | None = None
    sort_order: int = 0


class PracticePathItemAdminIn(BaseModel):
    item_type: str
    title: str | None = None
    sort_order: int = 0
    coding_problem_id: UUID | None = None
    sql_problem_id: UUID | None = None
    topic_id: UUID | None = None
    course_id: UUID | None = None
    lesson_id: UUID | None = None
    project_id: UUID | None = None
    external_route: str | None = None
    is_preview: bool = False

