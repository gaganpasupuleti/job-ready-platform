"""Library book metadata, bookmarks, and reading status.

Revision ID: 026_library_metadata
Revises: 025_email_notifications

This revision continues the notification branch only. It does not merge
022_python_runtime_backfill. It stores external https links, not files.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "026_library_metadata"
down_revision: Union[str, None] = "025_email_notifications"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "library_books",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("author", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(length=4000), nullable=False, server_default=""),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("external_url", sa.String(length=2000), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "status IN ('draft', 'published', 'archived')",
            name="ck_library_books_status",
        ),
        sa.CheckConstraint(
            "external_url LIKE 'https://%'",
            name="ck_library_books_https",
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_library_books_status", "library_books", ["status"])
    op.create_index("ix_library_books_category", "library_books", ["category"])
    op.create_table(
        "library_bookmarks",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("book_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["library_books.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "book_id"),
    )
    op.create_table(
        "library_reading_statuses",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("book_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "status IN ('not_started', 'reading', 'completed')",
            name="ck_library_reading_status",
        ),
        sa.ForeignKeyConstraint(["book_id"], ["library_books.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "book_id"),
    )


def downgrade() -> None:
    op.drop_table("library_reading_statuses")
    op.drop_table("library_bookmarks")
    op.drop_index("ix_library_books_category", table_name="library_books")
    op.drop_index("ix_library_books_status", table_name="library_books")
    op.drop_table("library_books")
