"""Build 4: SQL practice engine tables and bookmark extension."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004_build4"
down_revision: Union[str, None] = "003_build31"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sql_problems",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(150), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("difficulty", sa.String(20), nullable=False),
        sa.Column("database_dialect", sa.String(30), nullable=False, server_default="postgresql"),
        sa.Column("domain_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("domains.id"), nullable=False),
        sa.Column(
            "category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("categories.id"), nullable=False
        ),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("topics.id"), nullable=False),
        sa.Column(
            "subtopic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subtopics.id"), nullable=True
        ),
        sa.Column("tags", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("role_tags", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("scenario", sa.Text(), nullable=True),
        sa.Column("task_description", sa.Text(), nullable=False),
        sa.Column("expected_columns", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("order_sensitive", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("solution_query", sa.Text(), nullable=False),
        sa.Column("solution_explanation", sa.Text(), nullable=True),
        sa.Column("alternate_solution", sa.Text(), nullable=True),
        sa.Column("key_concepts", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("hints", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("sample_expected_rows", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("estimated_time_seconds", sa.Integer(), nullable=False, server_default="300"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_sample", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_sql_problems_slug", "sql_problems", ["slug"], unique=True)
    op.create_index("ix_sql_problems_domain_id", "sql_problems", ["domain_id"])
    op.create_index("ix_sql_problems_category_id", "sql_problems", ["category_id"])
    op.create_index("ix_sql_problems_topic_id", "sql_problems", ["topic_id"])
    op.create_index("ix_sql_problems_difficulty", "sql_problems", ["difficulty"])

    op.create_table(
        "sql_problem_tables",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "problem_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sql_problems.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("table_name", sa.String(100), nullable=False),
        sa.Column("display_name", sa.String(100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_sql_problem_tables_problem_id", "sql_problem_tables", ["problem_id"])

    op.create_table(
        "sql_problem_columns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "table_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sql_problem_tables.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("column_name", sa.String(100), nullable=False),
        sa.Column("data_type", sa.String(50), nullable=False),
        sa.Column("is_nullable", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_sql_problem_columns_table_id", "sql_problem_columns", ["table_id"])

    op.create_table(
        "sql_problem_seed_rows",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "table_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sql_problem_tables.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("row_data", postgresql.JSONB(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_sample", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.create_index("ix_sql_problem_seed_rows_table_id", "sql_problem_seed_rows", ["table_id"])

    op.create_table(
        "sql_expected_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "problem_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sql_problems.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("columns", postgresql.JSONB(), nullable=False),
        sa.Column("rows", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "sql_submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "problem_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sql_problems.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("result_row_count", sa.Integer(), nullable=True),
        sa.Column("execution_time_ms", sa.Float(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("feedback", postgresql.JSONB(), nullable=True),
        sa.Column(
            "submitted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_sql_submissions_user_id", "sql_submissions", ["user_id"])
    op.create_index("ix_sql_submissions_problem_id", "sql_submissions", ["problem_id"])

    op.create_table(
        "sql_problem_progress",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "problem_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sql_problems.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(20), nullable=False, server_default="attempted"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("first_attempted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("first_solved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("best_execution_time_ms", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "problem_id", name="uq_sql_progress_user_problem"),
    )
    op.create_index("ix_sql_problem_progress_user_id", "sql_problem_progress", ["user_id"])
    op.create_index("ix_sql_problem_progress_problem_id", "sql_problem_progress", ["problem_id"])

    op.add_column(
        "bookmarks",
        sa.Column("sql_problem_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_bookmarks_sql_problem_id",
        "bookmarks",
        "sql_problems",
        ["sql_problem_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_bookmarks_sql_problem_id", "bookmarks", ["sql_problem_id"])
    op.create_index(
        "uq_user_sql_problem_bookmark",
        "bookmarks",
        ["user_id", "sql_problem_id"],
        unique=True,
        postgresql_where=sa.text("sql_problem_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_user_sql_problem_bookmark", table_name="bookmarks")
    op.drop_index("ix_bookmarks_sql_problem_id", table_name="bookmarks")
    op.drop_constraint("fk_bookmarks_sql_problem_id", "bookmarks", type_="foreignkey")
    op.drop_column("bookmarks", "sql_problem_id")

    op.drop_table("sql_problem_progress")
    op.drop_table("sql_submissions")
    op.drop_table("sql_expected_results")
    op.drop_table("sql_problem_seed_rows")
    op.drop_table("sql_problem_columns")
    op.drop_table("sql_problem_tables")
    op.drop_table("sql_problems")
