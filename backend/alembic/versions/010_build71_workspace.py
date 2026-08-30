"""Build 7.1: path item completion and project task checklist state.

Revision ID: 010_build71
Revises: 009_build7
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "010_build71"
down_revision: Union[str, None] = "009_build7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_practice_path_item_progress",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("practice_path_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("path_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("practice_paths.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(40), nullable=False, server_default="completed"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "item_id", name="uq_user_path_item_progress"),
    )
    op.create_index("ix_user_path_item_progress_user_id", "user_practice_path_item_progress", ["user_id"])
    op.create_index("ix_user_path_item_progress_path_id", "user_practice_path_item_progress", ["path_id"])

    op.add_column(
        "user_project_task_progress",
        sa.Column(
            "checklist_state",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.add_column("project_tasks", sa.Column("scenario_slug", sa.String(180), nullable=True))
    op.add_column(
        "coding_problems",
        sa.Column(
            "hints_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "coding_problems",
        sa.Column("solution_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("coding_problems", "solution_json")
    op.drop_column("coding_problems", "hints_json")
    op.drop_column("project_tasks", "scenario_slug")
    op.drop_column("user_project_task_progress", "checklist_state")
    op.drop_table("user_practice_path_item_progress")
