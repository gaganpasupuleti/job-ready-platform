"""Build 5.1: project task types, progress, and metadata.

Revision ID: 007_build51
Revises: 006_build5
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "007_build51"
down_revision: Union[str, None] = "006_build5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column("prerequisites", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
    )
    op.add_column(
        "projects",
        sa.Column("skills", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
    )
    op.add_column("projects", sa.Column("final_objective", sa.Text(), nullable=True))
    op.add_column("projects", sa.Column("reference_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    op.add_column(
        "project_tasks",
        sa.Column("task_type", sa.String(30), nullable=False, server_default="concept"),
    )
    op.add_column(
        "project_tasks",
        sa.Column("sql_problem_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sql_problems.id", ondelete="SET NULL"), nullable=True),
    )
    op.add_column(
        "project_tasks",
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("topics.id", ondelete="SET NULL"), nullable=True),
    )
    op.add_column(
        "project_tasks",
        sa.Column("question_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("questions.id", ondelete="SET NULL"), nullable=True),
    )
    op.add_column(
        "project_tasks",
        sa.Column("body_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.add_column(
        "project_tasks",
        sa.Column("checklist_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
    )
    op.add_column("project_tasks", sa.Column("reference_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("project_tasks", sa.Column("estimated_minutes", sa.Integer(), nullable=True))

    op.add_column("user_project_progress", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("user_practice_path_progress", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        "user_project_task_progress",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("project_tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="not_started"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "task_id", name="uq_user_project_task_progress"),
    )
    op.create_index("ix_user_project_task_progress_user_id", "user_project_task_progress", ["user_id"])
    op.create_index("ix_user_project_task_progress_task_id", "user_project_task_progress", ["task_id"])


def downgrade() -> None:
    op.drop_index("ix_user_project_task_progress_task_id", table_name="user_project_task_progress")
    op.drop_index("ix_user_project_task_progress_user_id", table_name="user_project_task_progress")
    op.drop_table("user_project_task_progress")
    op.drop_column("user_practice_path_progress", "completed_at")
    op.drop_column("user_project_progress", "completed_at")
    op.drop_column("project_tasks", "estimated_minutes")
    op.drop_column("project_tasks", "reference_json")
    op.drop_column("project_tasks", "checklist_json")
    op.drop_column("project_tasks", "body_json")
    op.drop_column("project_tasks", "question_id")
    op.drop_column("project_tasks", "topic_id")
    op.drop_column("project_tasks", "sql_problem_id")
    op.drop_column("project_tasks", "task_type")
    op.drop_column("projects", "reference_json")
    op.drop_column("projects", "final_objective")
    op.drop_column("projects", "skills")
    op.drop_column("projects", "prerequisites")
