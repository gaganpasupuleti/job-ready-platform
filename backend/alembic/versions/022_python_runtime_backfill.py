"""Backfill explicit Python runtime metadata on existing local_python assignments.

Revision ID: 022_python_runtime_backfill
Revises: 021_sql_playground_syllabus

Does not invent Python locks from titles. Only tags rows already authored as local_python.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "022_python_runtime_backfill"
down_revision: Union[str, None] = "021_sql_playground_syllabus"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE assignments
            SET requires_runtime = 'python'
            WHERE submission_mode = 'local_python'
              AND (requires_runtime IS NULL OR requires_runtime = '')
            """
        )
    )


def downgrade() -> None:
    # Keep explicit tags; do not wipe author intent on downgrade.
    pass
