"""Build 7: deterministic scenario challenges.

Revision ID: 009_build7
Revises: 008_build6
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "009_build7"
down_revision: Union[str, None] = "008_build6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "scenario_challenges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(180), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("domain_key", sa.String(40), nullable=False),
        sa.Column("scenario_type", sa.String(40), nullable=False),
        sa.Column("difficulty", sa.String(20), nullable=False),
        sa.Column("context_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("evidence_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("unofficial_cert_tag", sa.String(80), nullable=True),
        sa.Column("mastery_threshold", sa.Integer(), nullable=False, server_default="80"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_scenario_challenges_slug", "scenario_challenges", ["slug"], unique=True)
    op.create_index("ix_scenario_challenges_domain_key", "scenario_challenges", ["domain_key"])

    op.create_table(
        "scenario_steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("challenge_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenario_challenges.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("context_snippet", sa.Text(), nullable=False, server_default=""),
        sa.Column("is_critical", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("explanation", sa.Text(), nullable=False, server_default=""),
        sa.Column("scoring_weight", sa.Float(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_scenario_steps_challenge_id", "scenario_steps", ["challenge_id"])

    op.create_table(
        "scenario_options",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("step_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenario_steps.id", ondelete="CASCADE"), nullable=False),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("explanation", sa.Text(), nullable=False, server_default=""),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_scenario_options_step_id", "scenario_options", ["step_id"])

    op.create_table(
        "scenario_submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("challenge_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenario_challenges.id", ondelete="CASCADE"), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("correct_decisions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_steps", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("missed_critical", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("explanation", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_scenario_submissions_user_id", "scenario_submissions", ["user_id"])
    op.create_index("ix_scenario_submissions_challenge_id", "scenario_submissions", ["challenge_id"])

    op.create_table(
        "scenario_step_answers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("submission_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenario_submissions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenario_steps.id", ondelete="CASCADE"), nullable=False),
        sa.Column("option_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenario_options.id", ondelete="CASCADE"), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_scenario_step_answers_submission_id", "scenario_step_answers", ["submission_id"])

    op.create_table(
        "scenario_progress",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("challenge_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenario_challenges.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="attempted"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("best_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "challenge_id", name="uq_scenario_progress"),
    )
    op.create_index("ix_scenario_progress_user_id", "scenario_progress", ["user_id"])


def downgrade() -> None:
    op.drop_table("scenario_progress")
    op.drop_table("scenario_step_answers")
    op.drop_table("scenario_submissions")
    op.drop_table("scenario_options")
    op.drop_table("scenario_steps")
    op.drop_table("scenario_challenges")
