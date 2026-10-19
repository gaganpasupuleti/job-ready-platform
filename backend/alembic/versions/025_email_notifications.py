"""Email outbox and per-user email preferences.

Revision ID: 025_email_notifications
Revises: 024_in_app_notifications

This revision continues the notification branch only. It does not merge
022_python_runtime_backfill. Existing reviews and replies are not copied
into the outbox.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "025_email_notifications"
down_revision: Union[str, None] = "024_in_app_notifications"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "email_preferences",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("assignment_review_enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("support_reply_enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_table(
        "email_outbox",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("recipient_user_id", sa.Uuid(), nullable=False),
        sa.Column("recipient_email", sa.String(length=255), nullable=False),
        sa.Column("notification_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("event_key", sa.String(length=160), nullable=False),
        sa.Column("channel", sa.String(length=16), nullable=False),
        sa.Column("destination_path", sa.String(length=300), nullable=False),
        sa.Column("subject", sa.String(length=200), nullable=False),
        sa.Column("text_body", sa.Text(), nullable=False),
        sa.Column("html_body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("reason", sa.String(length=64), nullable=True),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("claim_token", sa.Uuid(), nullable=True),
        sa.Column("provider_message_id", sa.String(length=255), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "event_type IN ('assignment_review', 'support_reply')",
            name="ck_email_outbox_event_type",
        ),
        sa.CheckConstraint("channel = 'email'", name="ck_email_outbox_channel"),
        sa.CheckConstraint(
            "status IN ('queued', 'sending', 'accepted', 'failed', 'ambiguous', 'suppressed')",
            name="ck_email_outbox_status",
        ),
        sa.CheckConstraint("attempt_count >= 0", name="ck_email_outbox_attempts"),
        sa.CheckConstraint("status <> 'accepted' OR provider_message_id IS NOT NULL", name="ck_email_outbox_accepted"),
        sa.ForeignKeyConstraint(["notification_id"], ["notifications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recipient_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("channel", "event_key", name="uq_email_outbox_channel_event"),
    )
    op.create_index("ix_email_outbox_recipient", "email_outbox", ["recipient_user_id"])
    op.create_index(
        "ix_email_outbox_queued",
        "email_outbox",
        ["next_attempt_at", "id"],
        postgresql_where=sa.text("status = 'queued'"),
    )


def downgrade() -> None:
    op.drop_index("ix_email_outbox_queued", table_name="email_outbox")
    op.drop_index("ix_email_outbox_recipient", table_name="email_outbox")
    op.drop_table("email_outbox")
    op.drop_table("email_preferences")
