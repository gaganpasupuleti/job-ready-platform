"""Mistake source events — DB-enforced idempotency for mistake recording.

Revision ID: 015_mistake_source_events
Revises: 014_phase12_listing_type
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "015_mistake_source_events"
down_revision: Union[str, None] = "014_phase12_listing_type"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "mistake_source_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_type", sa.String(40), nullable=False),
        sa.Column("source_event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "mistake_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mistake_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "user_id",
            "source_type",
            "source_event_id",
            name="uq_mistake_source_event",
        ),
    )
    op.create_index(
        "ix_mistake_source_events_mistake_item_id",
        "mistake_source_events",
        ["mistake_item_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_mistake_source_events_mistake_item_id", table_name="mistake_source_events")
    op.drop_table("mistake_source_events")
