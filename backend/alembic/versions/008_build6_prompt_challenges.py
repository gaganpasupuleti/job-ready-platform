"""Build 6: prompt challenges and bookmark extension.

Revision ID: 008_build6
Revises: 007_build51
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "008_build6"
down_revision: Union[str, None] = "007_build51"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "prompt_challenges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(180), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("difficulty", sa.String(20), nullable=False),
        sa.Column("task_type", sa.String(40), nullable=False),
        sa.Column("scenario", sa.Text(), nullable=False, server_default=""),
        sa.Column("instructions", sa.Text(), nullable=False, server_default=""),
        sa.Column("input_description", sa.Text(), nullable=False, server_default=""),
        sa.Column("expected_behavior", sa.Text(), nullable=False, server_default=""),
        sa.Column("starter_prompt", sa.Text(), nullable=True),
        sa.Column("reference_prompt", sa.Text(), nullable=True),
        sa.Column("max_prompt_length", sa.Integer(), nullable=False, server_default="8000"),
        sa.Column("mastery_threshold", sa.Integer(), nullable=False, server_default="80"),
        sa.Column("rubric_weights", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("hints", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("common_mistakes", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("evaluation_criteria_summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_prompt_challenges_slug", "prompt_challenges", ["slug"], unique=True)

    op.create_table(
        "prompt_challenge_cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("challenge_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("prompt_challenges.id", ondelete="CASCADE"), nullable=False),
        sa.Column("input_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("variables", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("expected_output", sa.Text(), nullable=True),
        sa.Column("expected_schema", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("evaluation_config", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("hide_input", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("weight", sa.Float(), nullable=False, server_default="1"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_prompt_challenge_cases_challenge_id", "prompt_challenge_cases", ["challenge_id"])

    op.create_table(
        "prompt_submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("challenge_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("prompt_challenges.id", ondelete="CASCADE"), nullable=False),
        sa.Column("prompt_text", sa.Text(), nullable=False),
        sa.Column("is_test", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("overall_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("passed_cases", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_cases", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rubric_breakdown", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("feedback", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_prompt_submissions_user_id", "prompt_submissions", ["user_id"])
    op.create_index("ix_prompt_submissions_challenge_id", "prompt_submissions", ["challenge_id"])

    op.create_table(
        "prompt_submission_case_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("submission_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("prompt_submissions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("prompt_challenge_cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("feedback", sa.Text(), nullable=False, server_default=""),
        sa.Column("check_results", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("revealed", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_prompt_submission_case_results_submission_id", "prompt_submission_case_results", ["submission_id"])

    op.create_table(
        "prompt_problem_progress",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("challenge_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("prompt_challenges.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="attempted"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("best_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("first_attempted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("first_mastered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "challenge_id", name="uq_prompt_problem_progress"),
    )
    op.create_index("ix_prompt_problem_progress_user_id", "prompt_problem_progress", ["user_id"])
    op.create_index("ix_prompt_problem_progress_challenge_id", "prompt_problem_progress", ["challenge_id"])

    op.create_table(
        "prompt_evaluation_rubrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("challenge_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("prompt_challenges.id", ondelete="CASCADE"), nullable=False),
        sa.Column("dimension", sa.String(80), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False, server_default="0"),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_prompt_evaluation_rubrics_challenge_id", "prompt_evaluation_rubrics", ["challenge_id"])

    op.add_column(
        "bookmarks",
        sa.Column("prompt_challenge_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_bookmarks_prompt_challenge_id",
        "bookmarks",
        "prompt_challenges",
        ["prompt_challenge_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_bookmarks_prompt_challenge_id", "bookmarks", ["prompt_challenge_id"])
    op.create_index(
        "uq_user_prompt_challenge_bookmark",
        "bookmarks",
        ["user_id", "prompt_challenge_id"],
        unique=True,
        postgresql_where=sa.text("prompt_challenge_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_user_prompt_challenge_bookmark", table_name="bookmarks")
    op.drop_index("ix_bookmarks_prompt_challenge_id", table_name="bookmarks")
    op.drop_constraint("fk_bookmarks_prompt_challenge_id", "bookmarks", type_="foreignkey")
    op.drop_column("bookmarks", "prompt_challenge_id")
    op.drop_table("prompt_problem_progress")
    op.drop_table("prompt_evaluation_rubrics")
    op.drop_table("prompt_submission_case_results")
    op.drop_table("prompt_submissions")
    op.drop_table("prompt_challenge_cases")
    op.drop_table("prompt_challenges")
