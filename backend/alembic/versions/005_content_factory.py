"""Content Factory: interview Q&A staging, packs, and jobs catalog stub."""

# ruff: noqa: E501, I001, UP007, UP035

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005_content_factory"
down_revision: Union[str, None] = "004_build4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(180), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_jobs_slug", "jobs", ["slug"], unique=True)

    op.create_table(
        "interview_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(180), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("question_type", sa.String(40), nullable=False),
        sa.Column("difficulty", sa.String(20), nullable=False),
        sa.Column("experience_level", sa.String(30), nullable=False),
        sa.Column("expected_answer", sa.Text(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("source_type", sa.String(40), nullable=False, server_default="manual"),
        sa.Column("review_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("domain_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("domains.id"), nullable=True),
        sa.Column(
            "category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("categories.id"), nullable=True
        ),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("topics.id"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_interview_questions_slug", "interview_questions", ["slug"], unique=True)
    op.create_index(
        "ix_interview_questions_content_hash", "interview_questions", ["content_hash"], unique=True
    )
    op.create_index("ix_interview_questions_review_status", "interview_questions", ["review_status"])

    op.create_table(
        "interview_answer_points",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "question_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("interview_questions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("point_text", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_interview_answer_points_question_id", "interview_answer_points", ["question_id"])

    op.create_table(
        "interview_question_skills",
        sa.Column(
            "question_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("interview_questions.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "skill_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("skills.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.UniqueConstraint("question_id", "skill_id", name="uq_interview_question_skill"),
    )
    op.create_table(
        "interview_question_roles",
        sa.Column(
            "question_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("interview_questions.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "role_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("job_roles.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.UniqueConstraint("question_id", "role_id", name="uq_interview_question_role"),
    )
    op.create_table(
        "interview_question_companies",
        sa.Column(
            "question_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("interview_questions.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.UniqueConstraint("question_id", "company_id", name="uq_interview_question_company"),
    )
    op.create_table(
        "interview_question_jobs",
        sa.Column(
            "question_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("interview_questions.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("jobs.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.UniqueConstraint("question_id", "job_id", name="uq_interview_question_job"),
    )

    op.create_table(
        "interview_packs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(180), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("experience_level", sa.String(30), nullable=True),
        sa.Column(
            "target_role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("job_roles.id"), nullable=True
        ),
        sa.Column(
            "target_company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id"),
            nullable=True,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_interview_packs_slug", "interview_packs", ["slug"], unique=True)

    op.create_table(
        "interview_pack_questions",
        sa.Column(
            "pack_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("interview_packs.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "question_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("interview_questions.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("section_name", sa.String(150), nullable=True),
        sa.UniqueConstraint("pack_id", "question_id", name="uq_interview_pack_question"),
    )

    op.create_table(
        "content_generation_batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("batch_date", sa.Date(), nullable=False),
        sa.Column("content_type", sa.String(40), nullable=False, server_default="interview_qa"),
        sa.Column("target_domain", sa.String(150), nullable=True),
        sa.Column("target_role", sa.String(150), nullable=True),
        sa.Column("target_company", sa.String(150), nullable=True),
        sa.Column("target_skill", sa.String(150), nullable=True),
        sa.Column("requested_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("generated_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("accepted_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rejected_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("generator", sa.String(50), nullable=False, server_default="cursor"),
        sa.Column("source_filename", sa.String(255), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_content_generation_batches_batch_date", "content_generation_batches", ["batch_date"])

    op.create_table(
        "content_generation_candidates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "batch_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("content_generation_batches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("content_type", sa.String(40), nullable=False, server_default="interview_qa"),
        sa.Column("payload_json", postgresql.JSONB(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("validation_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("review_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("validation_errors", postgresql.JSONB(), nullable=True),
        sa.Column(
            "published_question_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("interview_questions.id"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_content_generation_candidates_batch_id", "content_generation_candidates", ["batch_id"]
    )
    op.create_index(
        "ix_content_generation_candidates_content_hash",
        "content_generation_candidates",
        ["content_hash"],
    )
    op.create_index(
        "ix_content_generation_candidates_review_status",
        "content_generation_candidates",
        ["review_status"],
    )


def downgrade() -> None:
    op.drop_table("content_generation_candidates")
    op.drop_table("content_generation_batches")
    op.drop_table("interview_pack_questions")
    op.drop_table("interview_packs")
    op.drop_table("interview_question_jobs")
    op.drop_table("interview_question_companies")
    op.drop_table("interview_question_roles")
    op.drop_table("interview_question_skills")
    op.drop_table("interview_answer_points")
    op.drop_table("interview_questions")
    op.drop_table("jobs")
