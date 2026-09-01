"""Build 9 jobs domain migration.

Revision ID: 012_build9
Revises: 011_build8
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "012_build9"
down_revision: Union[str, None] = "011_build8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "job_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("slug", sa.String(80), nullable=False),
        sa.Column("source_type", sa.String(40), nullable=False),
        sa.Column("base_url", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_job_sources_slug", "job_sources", ["slug"], unique=True)

    # Expand jobs table from content-factory stub
    op.add_column("jobs", sa.Column("external_id", sa.String(255), nullable=True))
    op.add_column(
        "jobs",
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("job_sources.id", ondelete="SET NULL"), nullable=True),
    )
    op.add_column("jobs", sa.Column("normalized_title", sa.String(255), nullable=True))
    op.add_column("jobs", sa.Column("company_name_raw", sa.String(255), nullable=True))
    op.add_column("jobs", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("jobs", sa.Column("requirements_text", sa.Text(), nullable=True))
    op.add_column("jobs", sa.Column("responsibilities_text", sa.Text(), nullable=True))
    op.add_column("jobs", sa.Column("employment_type", sa.String(40), nullable=True))
    op.add_column("jobs", sa.Column("work_mode", sa.String(40), nullable=True))
    op.add_column("jobs", sa.Column("experience_min_years", sa.Integer(), nullable=True))
    op.add_column("jobs", sa.Column("experience_max_years", sa.Integer(), nullable=True))
    op.add_column("jobs", sa.Column("salary_min", sa.Numeric(14, 2), nullable=True))
    op.add_column("jobs", sa.Column("salary_max", sa.Numeric(14, 2), nullable=True))
    op.add_column("jobs", sa.Column("salary_currency", sa.String(8), nullable=True))
    op.add_column("jobs", sa.Column("location_text", sa.String(255), nullable=True))
    op.add_column("jobs", sa.Column("country", sa.String(120), nullable=True))
    op.add_column("jobs", sa.Column("state", sa.String(120), nullable=True))
    op.add_column("jobs", sa.Column("city", sa.String(120), nullable=True))
    op.add_column("jobs", sa.Column("source_url", sa.String(1000), nullable=True))
    op.add_column("jobs", sa.Column("apply_url", sa.String(1000), nullable=True))
    op.add_column("jobs", sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("jobs", sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("jobs", sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("jobs", sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("jobs", sa.Column("status", sa.String(40), nullable=True))
    op.add_column("jobs", sa.Column("is_remote", sa.Boolean(), nullable=True))
    op.add_column("jobs", sa.Column("content_hash", sa.String(64), nullable=True))

    op.execute(
        """
        UPDATE jobs SET
            normalized_title = lower(trim(title)),
            description = coalesce(description, ''),
            first_seen_at = created_at,
            last_seen_at = updated_at,
            status = CASE WHEN is_active THEN 'active' ELSE 'archived' END,
            content_hash = md5(slug::text)
        """
    )
    op.alter_column("jobs", "normalized_title", nullable=False)
    op.alter_column("jobs", "description", nullable=False, server_default="")
    op.alter_column("jobs", "first_seen_at", nullable=False)
    op.alter_column("jobs", "last_seen_at", nullable=False)
    op.alter_column("jobs", "status", nullable=False, server_default="active")
    op.alter_column("jobs", "content_hash", nullable=False)

    op.create_index("ix_jobs_status", "jobs", ["status"])
    op.create_index("ix_jobs_posted_at", "jobs", ["posted_at"])
    op.create_index("ix_jobs_normalized_title", "jobs", ["normalized_title"])
    op.create_index("ix_jobs_company_id", "jobs", ["company_id"])
    op.create_index("ix_jobs_content_hash", "jobs", ["content_hash"])
    op.create_index("ix_jobs_external_id", "jobs", ["external_id"])

    op.create_table(
        "job_skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("skills.id", ondelete="CASCADE"), nullable=False),
        sa.Column("importance", sa.String(40), nullable=False, server_default="mentioned"),
        sa.UniqueConstraint("job_id", "skill_id", name="uq_job_skills_job_skill"),
    )
    op.create_index("ix_job_skills_job_id", "job_skills", ["job_id"])
    op.create_index("ix_job_skills_skill_id", "job_skills", ["skill_id"])

    op.create_table(
        "job_role_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("job_roles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("mapping_source", sa.String(40), nullable=False, server_default="rule"),
        sa.UniqueConstraint("job_id", "role_id", name="uq_job_role_mappings_job_role"),
    )
    op.create_index("ix_job_role_mappings_job_id", "job_role_mappings", ["job_id"])
    op.create_index("ix_job_role_mappings_role_id", "job_role_mappings", ["role_id"])

    op.create_table(
        "job_locations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("location_text", sa.String(255), nullable=True),
        sa.Column("city", sa.String(120), nullable=True),
        sa.Column("state", sa.String(120), nullable=True),
        sa.Column("country", sa.String(120), nullable=True),
        sa.Column("is_remote", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.create_index("ix_job_locations_job_id", "job_locations", ["job_id"])

    op.create_table(
        "saved_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "job_id", name="uq_saved_jobs_user_job"),
    )
    op.create_index("ix_saved_jobs_user_id", "saved_jobs", ["user_id"])
    op.create_index("ix_saved_jobs_job_id", "saved_jobs", ["job_id"])

    op.create_table(
        "job_applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(40), nullable=False, server_default="saved"),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_follow_up_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_of_application", sa.String(120), nullable=True),
        sa.Column("application_url", sa.String(1000), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("salary_expected", sa.Numeric(14, 2), nullable=True),
        sa.Column("priority", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "job_id", name="uq_job_applications_user_job"),
    )
    op.create_index("ix_job_applications_user_id", "job_applications", ["user_id"])
    op.create_index("ix_job_applications_status", "job_applications", ["status"])
    op.create_index("ix_job_applications_next_follow_up_at", "job_applications", ["next_follow_up_at"])

    op.create_table(
        "application_status_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("job_applications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_status", sa.String(40), nullable=True),
        sa.Column("to_status", sa.String(40), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_application_status_history_application_id", "application_status_history", ["application_id"])

    op.create_table(
        "job_ingestion_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("job_sources.id", ondelete="SET NULL"), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("records_seen", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_created", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_updated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_skipped", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source_file_name", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "job_ingestion_errors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("job_ingestion_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=True),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("error_type", sa.String(80), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("raw_payload_json", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_job_ingestion_errors_run_id", "job_ingestion_errors", ["run_id"])

    op.create_table(
        "user_job_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("target_role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("job_roles.id", ondelete="SET NULL"), nullable=True),
        sa.Column("preferred_locations_json", postgresql.JSONB(), nullable=True),
        sa.Column("remote_preference", sa.String(40), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("user_job_preferences")
    op.drop_table("job_ingestion_errors")
    op.drop_table("job_ingestion_runs")
    op.drop_table("application_status_history")
    op.drop_table("job_applications")
    op.drop_table("saved_jobs")
    op.drop_table("job_locations")
    op.drop_table("job_role_mappings")
    op.drop_table("job_skills")

    op.drop_index("ix_jobs_external_id", table_name="jobs")
    op.drop_index("ix_jobs_content_hash", table_name="jobs")
    op.drop_index("ix_jobs_company_id", table_name="jobs")
    op.drop_index("ix_jobs_normalized_title", table_name="jobs")
    op.drop_index("ix_jobs_posted_at", table_name="jobs")
    op.drop_index("ix_jobs_status", table_name="jobs")

    for col in [
        "content_hash", "is_remote", "status", "last_seen_at", "first_seen_at",
        "expires_at", "posted_at", "apply_url", "source_url", "city", "state", "country",
        "location_text", "salary_currency", "salary_max", "salary_min",
        "experience_max_years", "experience_min_years", "work_mode", "employment_type",
        "responsibilities_text", "requirements_text", "description", "company_name_raw",
        "normalized_title", "source_id", "external_id",
    ]:
        op.drop_column("jobs", col)

    op.drop_table("job_sources")
