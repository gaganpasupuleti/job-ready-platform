"""Playground runtime metadata and syllabus entries.

Revision ID: 021_sql_playground_syllabus
Revises: 020_content_version_history

Local preparation only. Do not apply this to production in the same change.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "021_sql_playground_syllabus"
down_revision: Union[str, None] = "020_content_version_history"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("assignments", sa.Column("requires_runtime", sa.String(length=40), nullable=True))
    op.create_table(
        "learning_syllabus_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content_key", sa.String(length=160), nullable=False),
        sa.Column("track", sa.String(length=40), nullable=False),
        sa.Column("track_title", sa.String(length=120), nullable=False),
        sa.Column("unit", sa.String(length=80), nullable=False),
        sa.Column("unit_title", sa.String(length=160), nullable=False),
        sa.Column("unit_position", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("material_key", sa.String(length=160), nullable=True),
        sa.Column("question_keys", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("prerequisites", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("estimated_minutes", sa.Integer(), nullable=True),
        sa.Column("video_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("is_published", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("content_key"),
    )


def downgrade() -> None:
    op.drop_table("learning_syllabus_entries")
    op.drop_column("assignments", "requires_runtime")
