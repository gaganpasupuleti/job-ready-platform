"""Application-owned catalog publication decisions.

Revision ID: 017_job_publication_decisions
Revises: 016_practice_answer_uniqueness

The Jobs server collector is not in this workspace, so source
approved_status is not a durable review record. Decisions live here,
keyed by source board and source job_id.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "017_job_publication_decisions"
down_revision: Union[str, None] = "016_practice_answer_uniqueness"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "job_publication_decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source", sa.String(40), nullable=False),
        sa.Column("source_job_id", sa.String(80), nullable=False),
        sa.Column("decision", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("source", "source_job_id", name="uq_job_publication_source_job"),
    )


def downgrade() -> None:
    op.drop_table("job_publication_decisions")
