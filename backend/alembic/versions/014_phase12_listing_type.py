"""Phase 1.2: job listing_type for real vs sample_demo provenance.

Revision ID: 014_phase12_listing_type
Revises: 013_build10
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "014_phase12_listing_type"
down_revision: Union[str, None] = "013_build10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "jobs",
        sa.Column("listing_type", sa.String(40), nullable=True),
    )
    op.create_index("ix_jobs_listing_type", "jobs", ["listing_type"])
    # Backfill: Phase 1.1 sample titles / SAMPLE DEMO descriptions → sample_demo
    op.execute(
        """
        UPDATE jobs
        SET listing_type = 'sample_demo'
        WHERE listing_type IS NULL
          AND (
            title ILIKE '%SAMPLE DEMO%'
            OR description ILIKE '%[SAMPLE DEMO]%'
            OR description ILIKE '%Sample demo%'
            OR external_id ILIKE 'phase11-%'
          )
        """
    )
    op.execute(
        """
        UPDATE jobs
        SET listing_type = 'curated_import'
        WHERE listing_type IS NULL
        """
    )


def downgrade() -> None:
    op.drop_index("ix_jobs_listing_type", table_name="jobs")
    op.drop_column("jobs", "listing_type")
