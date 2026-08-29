import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import Difficulty
from app.models.coding_enums import ProblemProgressStatus, SubmissionStatus, SubmissionType


class CodingProblem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "coding_problems"

    slug: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[Difficulty] = mapped_column(
        Enum(Difficulty, name="difficulty", native_enum=False, create_constraint=False),
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
    constraints: Mapped[str | None] = mapped_column(Text, nullable=True)
    input_format: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_format: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    supported_language_ids: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    time_limit_ms: Mapped[int] = mapped_column(Integer, default=2000, nullable=False)
    memory_limit_kb: Mapped[int] = mapped_column(Integer, default=262144, nullable=False)
    starter_code: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_sample: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    test_cases: Mapped[list["CodingTestCase"]] = relationship(
        back_populates="problem",
        cascade="all, delete-orphan",
        order_by="CodingTestCase.sort_order",
    )


class CodingTestCase(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "coding_test_cases"

    problem_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("coding_problems.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    input: Mapped[str] = mapped_column(Text, default="", nullable=False)
    expected_output: Mapped[str] = mapped_column(Text, nullable=False)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    problem: Mapped["CodingProblem"] = relationship(back_populates="test_cases")


class CodingSubmission(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "coding_submissions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    problem_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("coding_problems.id", ondelete="CASCADE"), index=True
    )
    source_code: Mapped[str] = mapped_column(Text, nullable=False)
    language_id: Mapped[int] = mapped_column(Integer, nullable=False)
    language_name: Mapped[str] = mapped_column(String(50), nullable=False)
    submission_type: Mapped[SubmissionType] = mapped_column(
        Enum(SubmissionType, name="submission_type", native_enum=False),
        nullable=False,
    )
    status: Mapped[SubmissionStatus] = mapped_column(
        Enum(SubmissionStatus, name="submission_status", native_enum=False),
        nullable=False,
    )
    passed_tests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    execution_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    memory_kb: Mapped[int | None] = mapped_column(Integer, nullable=True)

    results: Mapped[list["CodingSubmissionResult"]] = relationship(
        back_populates="submission",
        cascade="all, delete-orphan",
        order_by="CodingSubmissionResult.test_number",
    )


class CodingSubmissionResult(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "coding_submission_results"

    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("coding_submissions.id", ondelete="CASCADE"), index=True
    )
    test_case_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("coding_test_cases.id", ondelete="SET NULL"), nullable=True
    )
    test_number: Mapped[int] = mapped_column(Integer, nullable=False)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[SubmissionStatus] = mapped_column(
        Enum(
            SubmissionStatus,
            name="submission_status",
            native_enum=False,
            create_constraint=False,
        ),
        nullable=False,
    )
    stdout: Mapped[str | None] = mapped_column(Text, nullable=True)
    stderr: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    memory_kb: Mapped[int | None] = mapped_column(Integer, nullable=True)

    submission: Mapped["CodingSubmission"] = relationship(back_populates="results")


class CodingProblemProgress(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "coding_problem_progress"
    __table_args__ = (UniqueConstraint("user_id", "problem_id", name="uq_user_problem_progress"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    problem_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("coding_problems.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[ProblemProgressStatus] = mapped_column(
        Enum(ProblemProgressStatus, name="problem_progress_status", native_enum=False),
        default=ProblemProgressStatus.UNSOLVED,
        nullable=False,
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    best_submission_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("coding_submissions.id", ondelete="SET NULL"), nullable=True
    )
    solved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    first_attempted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    best_runtime_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
