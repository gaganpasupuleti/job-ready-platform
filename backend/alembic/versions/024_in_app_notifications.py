"""In-app notifications for assignment reviews and support replies.

Revision ID: 024_in_app_notifications
Revises: 023_student_feedback

This revision continues the assignment and feedback branch only. It does not
merge 022_python_runtime_backfill. Existing reviews and replies are not copied
into this table.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "024_in_app_notifications"
down_revision: Union[str, None] = "023_student_feedback"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SHAPE = (
    "("
    "event_type = 'assignment_review' "
    "AND source_type = 'assignment_submission' "
    "AND message = 'Your assignment has been reviewed.' "
    "AND destination_path ~ '^/practice/projects#submission-[0-9a-fA-F-]{36}$'"
    ") OR ("
    "event_type = 'support_reply' "
    "AND source_type = 'support_ticket' "
    "AND message = 'You have a new reply on your request.' "
    "AND destination_path ~ '^/support/requests/[0-9a-fA-F-]{36}$'"
    ")"
)


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("recipient_user_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("event_key", sa.String(length=160), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("message", sa.String(length=160), nullable=False),
        sa.Column("destination_path", sa.String(length=300), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "event_type IN ('assignment_review', 'support_reply')",
            name="ck_notifications_event_type",
        ),
        sa.CheckConstraint(_SHAPE, name="ck_notifications_shape"),
        sa.ForeignKeyConstraint(["recipient_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_key", name="uq_notifications_event_key"),
    )
    op.create_index("ix_notifications_recipient_user_id", "notifications", ["recipient_user_id"])
    op.create_index("ix_notifications_recipient_created", "notifications", ["recipient_user_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_notifications_recipient_created", table_name="notifications")
    op.drop_index("ix_notifications_recipient_user_id", table_name="notifications")
    op.drop_table("notifications")
