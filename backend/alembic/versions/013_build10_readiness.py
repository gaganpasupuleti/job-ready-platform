"""Build 10 readiness, job match, mistake book.

Revision ID: 013_build10
Revises: 012_build9
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "013_build10"
down_revision: Union[str, None] = "012_build9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "role_skill_requirements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("job_roles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("skills.id", ondelete="CASCADE"), nullable=False),
        sa.Column("importance", sa.String(40), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("minimum_readiness", sa.Float(), nullable=True),
        sa.Column("source", sa.String(40), nullable=False, server_default="seed"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("role_id", "skill_id", name="uq_role_skill_requirement"),
    )
    op.create_index("ix_role_skill_requirements_role_id", "role_skill_requirements", ["role_id"])
    op.create_index("ix_role_skill_requirements_skill_id", "role_skill_requirements", ["skill_id"])

    op.create_table(
        "mistake_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_type", sa.String(40), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("skills.id", ondelete="SET NULL"), nullable=True),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("topics.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("mistake_type", sa.String(80), nullable=False, server_default="incorrect"),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("occurrence_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(40), nullable=False, server_default="open"),
        sa.Column("latest_context_json", postgresql.JSONB(), nullable=True),
        sa.Column("retry_href", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "source_type", "source_id", name="uq_mistake_user_source"),
    )
    op.create_index("ix_mistake_items_user_id", "mistake_items", ["user_id"])
    op.create_index("ix_mistake_items_source_type", "mistake_items", ["source_type"])
    op.create_index("ix_mistake_items_status", "mistake_items", ["status"])
    op.create_index("ix_mistake_items_skill_id", "mistake_items", ["skill_id"])

    op.create_table(
        "user_role_readiness_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("job_roles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("evidence_strength", sa.String(20), nullable=False),
        sa.Column("breakdown_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_user_role_readiness_snapshots_user_role",
        "user_role_readiness_snapshots",
        ["user_id", "role_id"],
    )
    op.create_index(
        "ix_user_role_readiness_snapshots_created_at",
        "user_role_readiness_snapshots",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_table("user_role_readiness_snapshots")
    op.drop_table("mistake_items")
    op.drop_table("role_skill_requirements")
