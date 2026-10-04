"""Store manual assignment links for later review.

Revision ID: 019_manual_assignment_submissions
Revises: 018_job_source_taxonomy

A submission is a link and an optional question. It does not complete a project
and it is not a grade.

The revision id is 33 characters. Alembic creates alembic_version.version_num
as VARCHAR(32), so the stamp after this upgrade would fail. Widen that column
before the new id is written. Downgrade leaves the wider column in place:
the 33-character id is still stored when downgrade() runs, and shrinking it
first would reject that value.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "019_manual_assignment_submissions"
down_revision: Union[str, None] = "018_job_source_taxonomy"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(64)")
    op.create_table(
        "manual_assignment_submissions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("link", sa.String(length=500), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("question", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_manual_assignment_submissions_user_id",
        "manual_assignment_submissions",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_manual_assignment_submissions_user_id", table_name="manual_assignment_submissions")
    op.drop_table("manual_assignment_submissions")
