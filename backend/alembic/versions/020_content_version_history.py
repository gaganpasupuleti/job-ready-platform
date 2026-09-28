"""Bind SQL grading and assignment/project history to a content version.

Revision ID: 020_content_version_history
Revises: 019_learning_studio

Does not reuse 018 or 019. Existing submissions stay. New columns are
nullable or defaulted so current rows keep their stored results.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "020_content_version_history"
down_revision: Union[str, None] = "019_learning_studio"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sql_problems",
        sa.Column("content_version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column("sql_submissions", sa.Column("content_version", sa.Integer(), nullable=True))
    op.add_column("sql_problem_progress", sa.Column("content_version", sa.Integer(), nullable=True))
    op.add_column(
        "assignment_submissions",
        sa.Column("brief_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "user_project_task_progress",
        sa.Column("brief_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("user_project_task_progress", "brief_snapshot")
    op.drop_column("assignment_submissions", "brief_snapshot")
    op.drop_column("sql_problem_progress", "content_version")
    op.drop_column("sql_submissions", "content_version")
    op.drop_column("sql_problems", "content_version")
