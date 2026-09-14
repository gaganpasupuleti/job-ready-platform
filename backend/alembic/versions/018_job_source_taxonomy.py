"""Store source role family and experience bucket on jobs.

Revision ID: 018_job_source_taxonomy
Revises: 017_job_publication_decisions

Nullable columns so existing listings, saves, and applications stay valid.
Values are copied from the source; they are not inferred from titles.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "018_job_source_taxonomy"
down_revision: Union[str, None] = "017_job_publication_decisions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("role_family", sa.String(64), nullable=True))
    op.add_column("jobs", sa.Column("actual_role_id", sa.String(64), nullable=True))
    op.add_column("jobs", sa.Column("actual_role_name", sa.String(160), nullable=True))
    op.add_column("jobs", sa.Column("experience_bucket", sa.String(64), nullable=True))
    op.create_index("ix_jobs_role_family", "jobs", ["role_family"])
    op.create_index("ix_jobs_experience_bucket", "jobs", ["experience_bucket"])


def downgrade() -> None:
    op.drop_index("ix_jobs_experience_bucket", table_name="jobs")
    op.drop_index("ix_jobs_role_family", table_name="jobs")
    op.drop_column("jobs", "experience_bucket")
    op.drop_column("jobs", "actual_role_name")
    op.drop_column("jobs", "actual_role_id")
    op.drop_column("jobs", "role_family")
