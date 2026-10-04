"""Store how many times a student opens a job and how long the page stays open.

Revision ID: 023_job_engagement
Revises: 022_python_runtime_backfill
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "023_job_engagement"
down_revision: Union[str, None] = "022_python_runtime_backfill"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "job_engagements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("open_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("first_opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "job_id", name="uq_job_engagements_user_job"),
    )
    op.create_index("ix_job_engagements_user_id", "job_engagements", ["user_id"])
    op.create_index("ix_job_engagements_job_id", "job_engagements", ["job_id"])


def downgrade() -> None:
    op.drop_index("ix_job_engagements_job_id", table_name="job_engagements")
    op.drop_index("ix_job_engagements_user_id", table_name="job_engagements")
    op.drop_table("job_engagements")
