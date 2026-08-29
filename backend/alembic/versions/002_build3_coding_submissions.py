"""Build 3: coding problems, test cases, submissions, progress."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002_build3"
down_revision: Union[str, None] = "001_build2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "coding_problems",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slug", sa.String(length=150), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "difficulty",
            sa.Enum("easy", "medium", "hard", name="difficulty", native_enum=False),
            nullable=False,
        ),
        sa.Column("domain_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("constraints", sa.Text(), nullable=True),
        sa.Column("time_limit_ms", sa.Integer(), nullable=False),
        sa.Column("memory_limit_kb", sa.Integer(), nullable=False),
        sa.Column("starter_code", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_sample", sa.Boolean(), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["domain_id"], ["domains.id"]),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_coding_problems_slug", "coding_problems", ["slug"], unique=False)
    op.create_index("ix_coding_problems_domain_id", "coding_problems", ["domain_id"], unique=False)
    op.create_index("ix_coding_problems_category_id", "coding_problems", ["category_id"], unique=False)
    op.create_index("ix_coding_problems_topic_id", "coding_problems", ["topic_id"], unique=False)

    op.create_table(
        "coding_test_cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("problem_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=True),
        sa.Column("input", sa.Text(), nullable=False),
        sa.Column("expected_output", sa.Text(), nullable=False),
        sa.Column("is_hidden", sa.Boolean(), nullable=False),
        sa.Column("is_sample", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["problem_id"], ["coding_problems.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_coding_test_cases_problem_id", "coding_test_cases", ["problem_id"], unique=False)

    op.create_table(
        "coding_submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("problem_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_code", sa.Text(), nullable=False),
        sa.Column("language_id", sa.Integer(), nullable=False),
        sa.Column("language_name", sa.String(length=50), nullable=False),
        sa.Column(
            "submission_type",
            sa.Enum("run", "submit", name="submission_type", native_enum=False),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "running",
                "accepted",
                "wrong_answer",
                "time_limit_exceeded",
                "memory_limit_exceeded",
                "runtime_error",
                "compilation_error",
                "internal_error",
                name="submission_status",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("passed_tests", sa.Integer(), nullable=False),
        sa.Column("total_tests", sa.Integer(), nullable=False),
        sa.Column("execution_time_ms", sa.Float(), nullable=True),
        sa.Column("memory_kb", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["problem_id"], ["coding_problems.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_coding_submissions_user_id", "coding_submissions", ["user_id"], unique=False)
    op.create_index("ix_coding_submissions_problem_id", "coding_submissions", ["problem_id"], unique=False)

    op.create_table(
        "coding_submission_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("submission_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("test_case_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("test_number", sa.Integer(), nullable=False),
        sa.Column("is_hidden", sa.Boolean(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "running",
                "accepted",
                "wrong_answer",
                "time_limit_exceeded",
                "memory_limit_exceeded",
                "runtime_error",
                "compilation_error",
                "internal_error",
                name="submission_status",
                native_enum=False,
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("stdout", sa.Text(), nullable=True),
        sa.Column("stderr", sa.Text(), nullable=True),
        sa.Column("execution_time_ms", sa.Float(), nullable=True),
        sa.Column("memory_kb", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["submission_id"], ["coding_submissions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["test_case_id"], ["coding_test_cases.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_coding_submission_results_submission_id",
        "coding_submission_results",
        ["submission_id"],
        unique=False,
    )

    op.create_table(
        "coding_problem_progress",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("problem_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            sa.Enum("unsolved", "attempted", "solved", name="problem_progress_status", native_enum=False),
            nullable=False,
        ),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("best_submission_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("solved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["best_submission_id"], ["coding_submissions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["problem_id"], ["coding_problems.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "problem_id", name="uq_user_problem_progress"),
    )
    op.create_index("ix_coding_problem_progress_user_id", "coding_problem_progress", ["user_id"], unique=False)
    op.create_index("ix_coding_problem_progress_problem_id", "coding_problem_progress", ["problem_id"], unique=False)


def downgrade() -> None:
    op.drop_table("coding_problem_progress")
    op.drop_table("coding_submission_results")
    op.drop_table("coding_submissions")
    op.drop_table("coding_test_cases")
    op.drop_table("coding_problems")
    op.execute("DROP TYPE IF EXISTS problem_progress_status")
    op.execute("DROP TYPE IF EXISTS submission_type")
    op.execute("DROP TYPE IF EXISTS submission_status")
