"""Join the master runtime line with the library line.

Revision ID: 029_join_runtime_and_library
Revises: 022_python_runtime_backfill, 028_library_pdf_upload

019_learning_studio and 019_manual_assignment_submissions both revise
018_job_source_taxonomy. Master continued through content history, the SQL
syllabus, and the Python runtime backfill. This branch continued through
manual assignments, feedback, notifications, email, and library. The two
heads are real history, not a duplicate of the same change.

This revision does not change schema. It records that both lines are present
so later upgrades have one head.
"""

from typing import Sequence, Union

revision: str = "029_join_runtime_and_library"
down_revision: Union[str, Sequence[str], None] = (
    "022_python_runtime_backfill",
    "028_library_pdf_upload",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
