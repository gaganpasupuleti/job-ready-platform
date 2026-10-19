"""Allow a library book to have neither link nor PDF while a file is uploaded.

Revision ID: 028_library_pdf_upload
Revises: 027_library_pdf_progress

This revision continues the library branch only. It does not merge
022_python_runtime_backfill.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "028_library_pdf_upload"
down_revision: Union[str, None] = "027_library_pdf_progress"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("ck_library_books_source", "library_books", type_="check")
    op.create_check_constraint(
        "ck_library_books_source",
        "library_books",
        "external_url IS NULL OR storage_key IS NULL",
    )


def downgrade() -> None:
    op.drop_constraint("ck_library_books_source", "library_books", type_="check")
    op.create_check_constraint(
        "ck_library_books_source",
        "library_books",
        "(external_url IS NOT NULL AND storage_key IS NULL) OR (external_url IS NULL AND storage_key IS NOT NULL)",
    )
