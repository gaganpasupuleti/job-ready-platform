"""Library PDF object keys and last-page progress.

Revision ID: 027_library_pdf_progress
Revises: 026_library_metadata

This revision continues the notification branch only. It does not merge
022_python_runtime_backfill.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "027_library_pdf_progress"
down_revision: Union[str, None] = "026_library_metadata"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("library_books", "external_url", existing_type=sa.String(length=2000), nullable=True)
    op.drop_constraint("ck_library_books_https", "library_books", type_="check")
    op.create_check_constraint(
        "ck_library_books_https",
        "library_books",
        "external_url IS NULL OR external_url LIKE 'https://%'",
    )
    op.add_column("library_books", sa.Column("storage_key", sa.String(length=400), nullable=True))
    op.create_check_constraint(
        "ck_library_books_source",
        "library_books",
        "(external_url IS NOT NULL AND storage_key IS NULL) OR (external_url IS NULL AND storage_key IS NOT NULL)",
    )
    op.alter_column("library_reading_statuses", "status", existing_type=sa.String(length=16), nullable=True)
    op.drop_constraint("ck_library_reading_status", "library_reading_statuses", type_="check")
    op.create_check_constraint(
        "ck_library_reading_status",
        "library_reading_statuses",
        "status IS NULL OR status IN ('not_started', 'reading', 'completed')",
    )
    op.add_column("library_reading_statuses", sa.Column("last_page", sa.Integer(), nullable=True))
    op.create_check_constraint(
        "ck_library_reading_last_page",
        "library_reading_statuses",
        "last_page IS NULL OR last_page >= 1",
    )


def downgrade() -> None:
    op.drop_constraint("ck_library_reading_last_page", "library_reading_statuses", type_="check")
    op.drop_column("library_reading_statuses", "last_page")
    op.drop_constraint("ck_library_reading_status", "library_reading_statuses", type_="check")
    op.create_check_constraint(
        "ck_library_reading_status",
        "library_reading_statuses",
        "status IN ('not_started', 'reading', 'completed')",
    )
    op.alter_column("library_reading_statuses", "status", existing_type=sa.String(length=16), nullable=False)
    op.drop_constraint("ck_library_books_source", "library_books", type_="check")
    op.drop_column("library_books", "storage_key")
    op.drop_constraint("ck_library_books_https", "library_books", type_="check")
    op.create_check_constraint("ck_library_books_https", "library_books", "external_url LIKE 'https://%'")
    op.alter_column("library_books", "external_url", existing_type=sa.String(length=2000), nullable=False)
