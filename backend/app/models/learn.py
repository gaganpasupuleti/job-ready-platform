# ruff: noqa: E501
"""Practice Hub paths, guided courses, lessons, and projects (same jobready_db)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.learn_enums import (
    CourseLevel,
    LessonFeedbackVote,
    LessonResourceType,
    LessonType,
    LessonUnlockMode,
    PathAvailability,
    PracticePathDifficulty,
    PracticePathItemType,
    PracticePathType,
    ProgressStatus,
    ProjectTaskType,
    SolutionRevealPolicy,
)


class PracticePath(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "practice_paths"

    slug: Mapped[str] = mapped_column(String(180), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    short_description: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    path_type: Mapped[PracticePathType] = mapped_column(
        Enum(PracticePathType, name="practice_path_type", native_enum=False),
        nullable=False,
        index=True,
    )
    difficulty: Mapped[PracticePathDifficulty] = mapped_column(
        Enum(PracticePathDifficulty, name="practice_path_difficulty", native_enum=False),
        default=PracticePathDifficulty.BEGINNER,
        nullable=False,
    )
    language: Mapped[str | None] = mapped_column(String(40), nullable=True)
    estimated_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    availability: Mapped[PathAvailability] = mapped_column(
        Enum(PathAvailability, name="path_availability", native_enum=False),
        default=PathAvailability.AVAILABLE,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    icon_key: Mapped[str | None] = mapped_column(String(80), nullable=True)
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True
    )
    skill_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id"), nullable=True
    )
    external_route: Mapped[str | None] = mapped_column(String(255), nullable=True)

    sections: Mapped[list[PracticePathSection]] = relationship(
        back_populates="path",
        cascade="all, delete-orphan",
        order_by="PracticePathSection.sort_order",
    )


class PracticePathSection(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "practice_path_sections"

    path_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("practice_paths.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    section_key: Mapped[str | None] = mapped_column(String(80), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    path: Mapped[PracticePath] = relationship(back_populates="sections")
    items: Mapped[list[PracticePathItem]] = relationship(
        back_populates="section",
        cascade="all, delete-orphan",
        order_by="PracticePathItem.sort_order",
    )


class PracticePathItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "practice_path_items"

    section_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("practice_path_sections.id", ondelete="CASCADE"),
        index=True,
    )
    item_type: Mapped[PracticePathItemType] = mapped_column(
        Enum(PracticePathItemType, name="practice_path_item_type", native_enum=False),
        nullable=False,
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_preview: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    coding_problem_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("coding_problems.id", ondelete="SET NULL"), nullable=True
    )
    sql_problem_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sql_problems.id", ondelete="SET NULL"), nullable=True
    )
    topic_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("topics.id", ondelete="SET NULL"), nullable=True
    )
    course_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="SET NULL"), nullable=True
    )
    lesson_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("course_lessons.id", ondelete="SET NULL"), nullable=True
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )
    external_route: Mapped[str | None] = mapped_column(String(255), nullable=True)

    section: Mapped[PracticePathSection] = relationship(back_populates="items")


class UserPracticePathProgress(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "user_practice_path_progress"
    __table_args__ = (UniqueConstraint("user_id", "path_id", name="uq_user_practice_path"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    path_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("practice_paths.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[ProgressStatus] = mapped_column(
        Enum(ProgressStatus, name="learn_progress_status", native_enum=False),
        default=ProgressStatus.NOT_STARTED,
        nullable=False,
    )
    percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class UserPracticePathItemProgress(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "user_practice_path_item_progress"
    __table_args__ = (UniqueConstraint("user_id", "item_id", name="uq_user_path_item_progress"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("practice_path_items.id", ondelete="CASCADE"), index=True
    )
    path_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("practice_paths.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[ProgressStatus] = mapped_column(
        Enum(ProgressStatus, name="learn_progress_status", native_enum=False, create_constraint=False),
        default=ProgressStatus.COMPLETED,
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Course(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "courses"

    slug: Mapped[str] = mapped_column(String(180), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    level: Mapped[CourseLevel] = mapped_column(
        Enum(CourseLevel, name="course_level", native_enum=False),
        default=CourseLevel.BEGINNER,
        nullable=False,
    )
    primary_language_key: Mapped[str | None] = mapped_column(String(40), nullable=True)
    estimated_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    certificate_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    modules: Mapped[list[CourseModule]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="CourseModule.sort_order",
    )


class CourseModule(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "course_modules"
    __table_args__ = (UniqueConstraint("course_id", "slug", name="uq_course_module_slug"),)

    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), index=True
    )
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    course: Mapped[Course] = relationship(back_populates="modules")
    lessons: Mapped[list[CourseLesson]] = relationship(
        back_populates="module",
        cascade="all, delete-orphan",
        order_by="CourseLesson.sort_order",
    )


class CourseLesson(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "course_lessons"
    __table_args__ = (UniqueConstraint("module_id", "slug", name="uq_course_lesson_slug"),)

    module_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("course_modules.id", ondelete="CASCADE"), index=True
    )
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lesson_type: Mapped[LessonType] = mapped_column(
        Enum(LessonType, name="lesson_type", native_enum=False),
        nullable=False,
    )
    statement_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    estimated_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    unlock_mode: Mapped[LessonUnlockMode] = mapped_column(
        Enum(LessonUnlockMode, name="lesson_unlock_mode", native_enum=False),
        default=LessonUnlockMode.PREVIOUS_COMPLETE,
        nullable=False,
    )
    solution_reveal: Mapped[SolutionRevealPolicy] = mapped_column(
        Enum(SolutionRevealPolicy, name="solution_reveal_policy", native_enum=False),
        default=SolutionRevealPolicy.AFTER_COMPLETION,
        nullable=False,
    )
    solution_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    starter_code: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    coding_problem_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("coding_problems.id", ondelete="SET NULL"), nullable=True
    )
    sql_problem_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sql_problems.id", ondelete="SET NULL"), nullable=True
    )
    question_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("questions.id", ondelete="SET NULL"), nullable=True
    )
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completion_requires_submit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    module: Mapped[CourseModule] = relationship(back_populates="lessons")
    steps: Mapped[list[LessonStep]] = relationship(
        back_populates="lesson", cascade="all, delete-orphan", order_by="LessonStep.sort_order"
    )
    hints: Mapped[list[LessonHint]] = relationship(
        back_populates="lesson", cascade="all, delete-orphan", order_by="LessonHint.sort_order"
    )
    doubts: Mapped[list[LessonDoubt]] = relationship(
        back_populates="lesson", cascade="all, delete-orphan", order_by="LessonDoubt.sort_order"
    )
    resources: Mapped[list[LessonResource]] = relationship(
        back_populates="lesson",
        cascade="all, delete-orphan",
        order_by="LessonResource.sort_order",
    )


class LessonStep(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "lesson_steps"

    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("course_lessons.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body_md: Mapped[str] = mapped_column(Text, nullable=False, default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    lesson: Mapped[CourseLesson] = relationship(back_populates="steps")


class LessonHint(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "lesson_hints"

    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("course_lessons.id", ondelete="CASCADE"), index=True
    )
    hint_text: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unlock_after_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    lesson: Mapped[CourseLesson] = relationship(back_populates="hints")


class LessonDoubt(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "lesson_doubts"

    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("course_lessons.id", ondelete="CASCADE"), index=True
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    lesson: Mapped[CourseLesson] = relationship(back_populates="doubts")


class LessonResource(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "lesson_resources"

    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("course_lessons.id", ondelete="CASCADE"), index=True
    )
    resource_type: Mapped[LessonResourceType] = mapped_column(
        Enum(LessonResourceType, name="lesson_resource_type", native_enum=False),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    lesson: Mapped[CourseLesson] = relationship(back_populates="resources")


class UserCourseProgress(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "user_course_progress"
    __table_args__ = (UniqueConstraint("user_id", "course_id", name="uq_user_course_progress"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[ProgressStatus] = mapped_column(
        Enum(
            ProgressStatus,
            name="learn_progress_status",
            native_enum=False,
            create_constraint=False,
        ),
        default=ProgressStatus.NOT_STARTED,
        nullable=False,
    )
    percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_lesson_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("course_lessons.id", ondelete="SET NULL"), nullable=True
    )
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class UserLessonProgress(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "user_lesson_progress"
    __table_args__ = (UniqueConstraint("user_id", "lesson_id", name="uq_user_lesson_progress"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("course_lessons.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[ProgressStatus] = mapped_column(
        Enum(
            ProgressStatus,
            name="learn_progress_status",
            native_enum=False,
            create_constraint=False,
        ),
        default=ProgressStatus.NOT_STARTED,
        nullable=False,
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class LessonAttempt(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "lesson_attempts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("course_lessons.id", ondelete="CASCADE"), index=True
    )
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    coding_submission_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("coding_submissions.id", ondelete="SET NULL"), nullable=True
    )


class LessonFeedback(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "lesson_feedback"
    __table_args__ = (UniqueConstraint("user_id", "lesson_id", name="uq_lesson_feedback"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("course_lessons.id", ondelete="CASCADE"), index=True
    )
    vote: Mapped[LessonFeedbackVote | None] = mapped_column(
        Enum(LessonFeedbackVote, name="lesson_feedback_vote", native_enum=False),
        nullable=True,
    )
    report_issue: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class Project(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "projects"

    slug: Mapped[str] = mapped_column(String(180), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    short_description: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    difficulty: Mapped[PracticePathDifficulty] = mapped_column(
        Enum(
            PracticePathDifficulty,
            name="practice_path_difficulty",
            native_enum=False,
            create_constraint=False,
        ),
        default=PracticePathDifficulty.BEGINNER,
        nullable=False,
    )
    technology: Mapped[str | None] = mapped_column(String(80), nullable=True)
    category_key: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    estimated_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    availability: Mapped[PathAvailability] = mapped_column(
        Enum(
            PathAvailability,
            name="path_availability",
            native_enum=False,
            create_constraint=False,
        ),
        default=PathAvailability.COMING_SOON,
        nullable=False,
    )
    prerequisites: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    skills: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    final_objective: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    modules: Mapped[list[ProjectModule]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="ProjectModule.sort_order",
    )


class ProjectModule(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "project_modules"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    project: Mapped[Project] = relationship(back_populates="modules")
    tasks: Mapped[list[ProjectTask]] = relationship(
        back_populates="module", cascade="all, delete-orphan", order_by="ProjectTask.sort_order"
    )


class ProjectTask(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "project_tasks"

    module_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project_modules.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    task_type: Mapped[ProjectTaskType] = mapped_column(
        Enum(ProjectTaskType, name="project_task_type", native_enum=False),
        default=ProjectTaskType.CONCEPT,
        nullable=False,
    )
    lesson_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("course_lessons.id", ondelete="SET NULL"), nullable=True
    )
    coding_problem_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("coding_problems.id", ondelete="SET NULL"), nullable=True
    )
    sql_problem_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sql_problems.id", ondelete="SET NULL"), nullable=True
    )
    topic_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("topics.id", ondelete="SET NULL"), nullable=True
    )
    question_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("questions.id", ondelete="SET NULL"), nullable=True
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    checklist_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    reference_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    estimated_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    scenario_slug: Mapped[str | None] = mapped_column(String(180), nullable=True)

    module: Mapped[ProjectModule] = relationship(back_populates="tasks")


class UserProjectProgress(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "user_project_progress"
    __table_args__ = (UniqueConstraint("user_id", "project_id", name="uq_user_project_progress"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[ProgressStatus] = mapped_column(
        Enum(
            ProgressStatus,
            name="learn_progress_status",
            native_enum=False,
            create_constraint=False,
        ),
        default=ProgressStatus.NOT_STARTED,
        nullable=False,
    )
    percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project_tasks.id", ondelete="SET NULL"), nullable=True
    )
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class UserProjectTaskProgress(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "user_project_task_progress"
    __table_args__ = (UniqueConstraint("user_id", "task_id", name="uq_user_project_task_progress"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project_tasks.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[ProgressStatus] = mapped_column(
        Enum(
            ProgressStatus,
            name="learn_progress_status",
            native_enum=False,
            create_constraint=False,
        ),
        default=ProgressStatus.NOT_STARTED,
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    checklist_state: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
