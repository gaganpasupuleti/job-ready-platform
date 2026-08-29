"""Build 3.1: coding tags, progress timestamps, bookmarks, exam timer."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_build31"
down_revision: Union[str, None] = "002_build3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("coding_problems", sa.Column("input_format", sa.Text(), nullable=True))
    op.add_column("coding_problems", sa.Column("output_format", sa.Text(), nullable=True))
    op.add_column(
        "coding_problems",
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
    )
    op.add_column(
        "coding_problems",
        sa.Column(
            "supported_language_ids",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="[71, 62, 54, 63]",
            nullable=False,
        ),
    )

    op.add_column(
        "coding_problem_progress",
        sa.Column("first_attempted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "coding_problem_progress",
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "coding_problem_progress",
        sa.Column("best_runtime_ms", sa.Float(), nullable=True),
    )

    op.add_column("practice_sessions", sa.Column("duration_minutes", sa.Integer(), nullable=True))
    op.add_column("practice_sessions", sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))

    op.add_column(
        "practice_answers",
        sa.Column("marked_for_review", sa.Boolean(), server_default="false", nullable=False),
    )

    op.alter_column("bookmarks", "question_id", existing_type=postgresql.UUID(), nullable=True)
    op.add_column("bookmarks", sa.Column("problem_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_bookmarks_problem_id",
        "bookmarks",
        "coding_problems",
        ["problem_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_bookmarks_problem_id", "bookmarks", ["problem_id"], unique=False)
    op.drop_constraint("uq_user_question_bookmark", "bookmarks", type_="unique")
    op.create_index(
        "uq_user_question_bookmark",
        "bookmarks",
        ["user_id", "question_id"],
        unique=True,
        postgresql_where=sa.text("question_id IS NOT NULL"),
    )
    op.create_index(
        "uq_user_problem_bookmark",
        "bookmarks",
        ["user_id", "problem_id"],
        unique=True,
        postgresql_where=sa.text("problem_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_user_problem_bookmark", table_name="bookmarks")
    op.drop_index("uq_user_question_bookmark", table_name="bookmarks")
    op.create_unique_constraint("uq_user_question_bookmark", "bookmarks", ["user_id", "question_id"])
    op.drop_index("ix_bookmarks_problem_id", table_name="bookmarks")
    op.drop_constraint("fk_bookmarks_problem_id", "bookmarks", type_="foreignkey")
    op.drop_column("bookmarks", "problem_id")
    op.alter_column("bookmarks", "question_id", existing_type=postgresql.UUID(), nullable=False)

    op.drop_column("practice_answers", "marked_for_review")
    op.drop_column("practice_sessions", "expires_at")
    op.drop_column("practice_sessions", "duration_minutes")
    op.drop_column("coding_problem_progress", "best_runtime_ms")
    op.drop_column("coding_problem_progress", "last_attempt_at")
    op.drop_column("coding_problem_progress", "first_attempted_at")
    op.drop_column("coding_problems", "supported_language_ids")
    op.drop_column("coding_problems", "tags")
    op.drop_column("coding_problems", "output_format")
    op.drop_column("coding_problems", "input_format")
