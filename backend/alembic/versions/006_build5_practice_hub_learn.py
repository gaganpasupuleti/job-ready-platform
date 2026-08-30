"""Build 5: Practice Hub, courses, lessons, projects.

Revision ID: 006_build5
Revises: 005_content_factory
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# ruff: noqa: E501

revision: str = "006_build5"
down_revision: Union[str, None] = "005_content_factory"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "courses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(180), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("level", sa.String(30), nullable=False, server_default="beginner"),
        sa.Column("primary_language_key", sa.String(40), nullable=True),
        sa.Column("estimated_minutes", sa.Integer(), nullable=True),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_featured", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("certificate_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_courses_slug", "courses", ["slug"], unique=True)

    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(180), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("short_description", sa.String(500), nullable=False, server_default=""),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("difficulty", sa.String(20), nullable=False, server_default="beginner"),
        sa.Column("technology", sa.String(80), nullable=True),
        sa.Column("category_key", sa.String(80), nullable=False),
        sa.Column("estimated_minutes", sa.Integer(), nullable=True),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_featured", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("availability", sa.String(30), nullable=False, server_default="coming_soon"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_projects_slug", "projects", ["slug"], unique=True)
    op.create_index("ix_projects_category_key", "projects", ["category_key"])

    op.create_table(
        "course_modules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("course_id", "slug", name="uq_course_module_slug"),
    )
    op.create_index("ix_course_modules_course_id", "course_modules", ["course_id"])

    op.create_table(
        "course_lessons",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("module_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("course_modules.id", ondelete="CASCADE"), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lesson_type", sa.String(40), nullable=False),
        sa.Column("statement_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("estimated_minutes", sa.Integer(), nullable=True),
        sa.Column("unlock_mode", sa.String(40), nullable=False, server_default="previous_complete"),
        sa.Column("solution_reveal", sa.String(40), nullable=False, server_default="after_completion"),
        sa.Column("solution_json", postgresql.JSONB(), nullable=True),
        sa.Column("starter_code", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("coding_problem_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("coding_problems.id", ondelete="SET NULL"), nullable=True),
        sa.Column("sql_problem_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sql_problems.id", ondelete="SET NULL"), nullable=True),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("questions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("completion_requires_submit", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("module_id", "slug", name="uq_course_lesson_slug"),
    )
    op.create_index("ix_course_lessons_module_id", "course_lessons", ["module_id"])

    for table, cols in [
        ("lesson_steps", [("title", sa.String(255)), ("body_md", sa.Text())]),
        ("lesson_hints", [("hint_text", sa.Text()), ("unlock_after_attempts", sa.Integer())]),
        ("lesson_doubts", [("question", sa.Text()), ("answer", sa.Text())]),
    ]:
        columns = [
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("lesson_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("course_lessons.id", ondelete="CASCADE"), nullable=False),
        ]
        for name, col in cols:
            if name == "unlock_after_attempts":
                columns.append(sa.Column(name, col, nullable=False, server_default="0"))
            elif name == "body_md":
                columns.append(sa.Column(name, col, nullable=False, server_default=""))
            else:
                columns.append(sa.Column(name, col, nullable=False))
        columns.extend(
            [
                sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
                sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
                sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            ]
        )
        op.create_table(table, *columns)
        op.create_index(f"ix_{table}_lesson_id", table, ["lesson_id"])

    op.create_table(
        "lesson_resources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("lesson_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("course_lessons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resource_type", sa.String(30), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_lesson_resources_lesson_id", "lesson_resources", ["lesson_id"])

    op.create_table(
        "lesson_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lesson_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("course_lessons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("payload_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_correct", sa.Boolean(), nullable=True),
        sa.Column("coding_submission_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("coding_submissions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_lesson_attempts_user_id", "lesson_attempts", ["user_id"])
    op.create_index("ix_lesson_attempts_lesson_id", "lesson_attempts", ["lesson_id"])

    op.create_table(
        "lesson_feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lesson_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("course_lessons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vote", sa.String(20), nullable=True),
        sa.Column("report_issue", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "lesson_id", name="uq_lesson_feedback"),
    )
    op.create_index("ix_lesson_feedback_user_id", "lesson_feedback", ["user_id"])
    op.create_index("ix_lesson_feedback_lesson_id", "lesson_feedback", ["lesson_id"])

    op.create_table(
        "user_lesson_progress",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lesson_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("course_lessons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="not_started"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "lesson_id", name="uq_user_lesson_progress"),
    )
    op.create_index("ix_user_lesson_progress_user_id", "user_lesson_progress", ["user_id"])
    op.create_index("ix_user_lesson_progress_lesson_id", "user_lesson_progress", ["lesson_id"])

    op.create_table(
        "user_course_progress",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="not_started"),
        sa.Column("percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("current_lesson_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("course_lessons.id", ondelete="SET NULL"), nullable=True),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "course_id", name="uq_user_course_progress"),
    )
    op.create_index("ix_user_course_progress_user_id", "user_course_progress", ["user_id"])
    op.create_index("ix_user_course_progress_course_id", "user_course_progress", ["course_id"])

    op.create_table(
        "project_modules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_project_modules_project_id", "project_modules", ["project_id"])

    op.create_table(
        "project_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("module_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("project_modules.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lesson_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("course_lessons.id", ondelete="SET NULL"), nullable=True),
        sa.Column("coding_problem_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("coding_problems.id", ondelete="SET NULL"), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_project_tasks_module_id", "project_tasks", ["module_id"])

    op.create_table(
        "user_project_progress",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="not_started"),
        sa.Column("percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("project_tasks.id", ondelete="SET NULL"), nullable=True),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "project_id", name="uq_user_project_progress"),
    )
    op.create_index("ix_user_project_progress_user_id", "user_project_progress", ["user_id"])
    op.create_index("ix_user_project_progress_project_id", "user_project_progress", ["project_id"])

    op.create_table(
        "practice_paths",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(180), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("short_description", sa.String(500), nullable=False, server_default=""),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("path_type", sa.String(40), nullable=False),
        sa.Column("difficulty", sa.String(20), nullable=False, server_default="beginner"),
        sa.Column("language", sa.String(40), nullable=True),
        sa.Column("estimated_minutes", sa.Integer(), nullable=True),
        sa.Column("availability", sa.String(30), nullable=False, server_default="available"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_featured", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("icon_key", sa.String(80), nullable=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=True),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("skills.id"), nullable=True),
        sa.Column("external_route", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_practice_paths_slug", "practice_paths", ["slug"], unique=True)
    op.create_index("ix_practice_paths_path_type", "practice_paths", ["path_type"])

    op.create_table(
        "practice_path_sections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("path_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("practice_paths.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("section_key", sa.String(80), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_practice_path_sections_path_id", "practice_path_sections", ["path_id"])

    op.create_table(
        "practice_path_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("section_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("practice_path_sections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_type", sa.String(40), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_preview", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("coding_problem_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("coding_problems.id", ondelete="SET NULL"), nullable=True),
        sa.Column("sql_problem_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sql_problems.id", ondelete="SET NULL"), nullable=True),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("topics.id", ondelete="SET NULL"), nullable=True),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="SET NULL"), nullable=True),
        sa.Column("lesson_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("course_lessons.id", ondelete="SET NULL"), nullable=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="SET NULL"), nullable=True),
        sa.Column("external_route", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_practice_path_items_section_id", "practice_path_items", ["section_id"])

    op.create_table(
        "user_practice_path_progress",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("path_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("practice_paths.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="not_started"),
        sa.Column("percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "path_id", name="uq_user_practice_path"),
    )
    op.create_index("ix_user_practice_path_progress_user_id", "user_practice_path_progress", ["user_id"])
    op.create_index("ix_user_practice_path_progress_path_id", "user_practice_path_progress", ["path_id"])


def downgrade() -> None:
    for table in [
        "user_practice_path_progress",
        "practice_path_items",
        "practice_path_sections",
        "practice_paths",
        "user_project_progress",
        "project_tasks",
        "project_modules",
        "user_course_progress",
        "user_lesson_progress",
        "lesson_feedback",
        "lesson_attempts",
        "lesson_resources",
        "lesson_doubts",
        "lesson_hints",
        "lesson_steps",
        "course_lessons",
        "course_modules",
        "projects",
        "courses",
    ]:
        op.drop_table(table)
