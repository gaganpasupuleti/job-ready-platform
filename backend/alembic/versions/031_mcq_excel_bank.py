"""MCQ Excel bank import: option explanations, bank metadata, import runs."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "031_mcq_excel_bank"
down_revision: Union[str, None] = "030_merge_auth_and_library_heads"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("question_options", sa.Column("explanation", sa.Text(), nullable=True))
    op.add_column("questions", sa.Column("bank_key", sa.String(length=80), nullable=True))
    op.add_column("questions", sa.Column("hint", sa.Text(), nullable=True))
    op.add_column(
        "questions",
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "questions",
        sa.Column(
            "publication_status",
            sa.String(length=20),
            nullable=True,
        ),
    )
    op.create_index("ix_questions_bank_key", "questions", ["bank_key"], unique=False)

    op.create_table(
        "mcq_bank_registry",
        sa.Column("bank_key", sa.String(length=80), primary_key=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("question_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_published_at", sa.DateTime(timezone=True), nullable=True),
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
    )

    op.create_table(
        "mcq_import_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("bank_key", sa.String(length=80), nullable=False, index=True),
        sa.Column("import_mode", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="staged"),
        sa.Column("workbook_checksum", sa.String(length=64), nullable=False),
        sa.Column("bank_version_at_preview", sa.Integer(), nullable=False),
        sa.Column("staged_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("preview_summary", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("row_errors", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("allow_empty_replace", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "mcq_question_revisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "question_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("questions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("content_key", sa.String(length=160), nullable=False, index=True),
        sa.Column("bank_key", sa.String(length=80), nullable=True),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "import_run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mcq_import_runs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("mcq_question_revisions")
    op.drop_table("mcq_import_runs")
    op.drop_table("mcq_bank_registry")
    op.drop_index("ix_questions_bank_key", table_name="questions")
    op.drop_column("questions", "publication_status")
    op.drop_column("questions", "revision")
    op.drop_column("questions", "hint")
    op.drop_column("questions", "bank_key")
    op.drop_column("question_options", "explanation")
