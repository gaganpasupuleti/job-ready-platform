import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import Difficulty
from app.models.sql_enums import SqlDialect, SqlProgressStatus, SqlSubmissionStatus


class SqlProblem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "sql_problems"

    slug: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[Difficulty] = mapped_column(
        Enum(Difficulty, name="difficulty", native_enum=False, create_constraint=False),
        nullable=False,
    )
    database_dialect: Mapped[SqlDialect] = mapped_column(
        Enum(SqlDialect, name="sql_dialect", native_enum=False),
        default=SqlDialect.POSTGRESQL,
        nullable=False,
    )
    domain_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("domains.id"), index=True, nullable=False
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id"), index=True, nullable=False
    )
    topic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("topics.id"), index=True, nullable=False
    )
    subtopic_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subtopics.id"), nullable=True
    )
    tags: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    role_tags: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    scenario: Mapped[str | None] = mapped_column(Text, nullable=True)
    task_description: Mapped[str] = mapped_column(Text, nullable=False)
    expected_columns: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    order_sensitive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    solution_query: Mapped[str] = mapped_column(Text, nullable=False)
    solution_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    alternate_solution: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_concepts: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    hints: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    sample_expected_rows: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    estimated_time_seconds: Mapped[int] = mapped_column(Integer, default=300, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_sample: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    tables: Mapped[list["SqlProblemTable"]] = relationship(
        back_populates="problem",
        cascade="all, delete-orphan",
        order_by="SqlProblemTable.sort_order",
    )
    expected_result: Mapped["SqlExpectedResult | None"] = relationship(
        back_populates="problem",
        cascade="all, delete-orphan",
        uselist=False,
    )


class SqlProblemTable(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "sql_problem_tables"

    problem_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sql_problems.id", ondelete="CASCADE"), index=True
    )
    table_name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    problem: Mapped["SqlProblem"] = relationship(back_populates="tables")
    columns: Mapped[list["SqlProblemColumn"]] = relationship(
        back_populates="table",
        cascade="all, delete-orphan",
        order_by="SqlProblemColumn.sort_order",
    )
    seed_rows: Mapped[list["SqlProblemSeedRow"]] = relationship(
        back_populates="table",
        cascade="all, delete-orphan",
        order_by="SqlProblemSeedRow.sort_order",
    )


class SqlProblemColumn(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "sql_problem_columns"

    table_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sql_problem_tables.id", ondelete="CASCADE"), index=True
    )
    column_name: Mapped[str] = mapped_column(String(100), nullable=False)
    data_type: Mapped[str] = mapped_column(String(50), nullable=False)
    is_nullable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    table: Mapped["SqlProblemTable"] = relationship(back_populates="columns")


class SqlProblemSeedRow(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "sql_problem_seed_rows"

    table_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sql_problem_tables.id", ondelete="CASCADE"), index=True
    )
    row_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_sample: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    table: Mapped["SqlProblemTable"] = relationship(back_populates="seed_rows")


class SqlExpectedResult(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "sql_expected_results"

    problem_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sql_problems.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    columns: Mapped[list] = mapped_column(JSONB, nullable=False)
    rows: Mapped[list] = mapped_column(JSONB, nullable=False)

    problem: Mapped["SqlProblem"] = relationship(back_populates="expected_result")


class SqlSubmission(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "sql_submissions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    problem_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sql_problems.id", ondelete="CASCADE"), index=True
    )
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[SqlSubmissionStatus] = mapped_column(
        Enum(SqlSubmissionStatus, name="sql_submission_status", native_enum=False),
        nullable=False,
    )
    result_row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    execution_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    feedback: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SqlProblemProgress(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "sql_problem_progress"
    __table_args__ = (UniqueConstraint("user_id", "problem_id", name="uq_sql_progress_user_problem"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    problem_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sql_problems.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[SqlProgressStatus] = mapped_column(
        Enum(SqlProgressStatus, name="sql_progress_status", native_enum=False),
        default=SqlProgressStatus.ATTEMPTED,
        nullable=False,
    )
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    first_attempted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    first_solved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    best_execution_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
