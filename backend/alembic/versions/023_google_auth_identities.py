"""Optional passwords and Google sign-in identities.

Revision ID: 023_google_auth_identities
Revises: 023_job_engagement
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "023_google_auth_identities"
down_revision: Union[str, None] = "023_job_engagement"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("users", "password_hash", existing_type=sa.String(length=255), nullable=True)
    op.create_table(
        "user_auth_identities",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("provider_subject", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "provider",
            "provider_subject",
            name="uq_user_auth_identities_provider_subject",
        ),
        sa.UniqueConstraint(
            "user_id",
            "provider",
            name="uq_user_auth_identities_user_provider",
        ),
    )
    op.create_index("ix_user_auth_identities_user_id", "user_auth_identities", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_user_auth_identities_user_id", table_name="user_auth_identities")
    op.drop_table("user_auth_identities")
    op.execute(sa.text("UPDATE users SET password_hash = '' WHERE password_hash IS NULL"))
    op.alter_column("users", "password_hash", existing_type=sa.String(length=255), nullable=False)
