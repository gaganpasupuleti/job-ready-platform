from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import Difficulty
from app.models.practice import Bookmark
from app.models.sql_enums import SqlProgressStatus, SqlSubmissionStatus
from app.models.sql_practice import (
    SqlExpectedResult,
    SqlProblem,
    SqlProblemColumn,
    SqlProblemProgress,
    SqlProblemSeedRow,
    SqlProblemTable,
    SqlSubmission,
)
from app.models.taxonomy import Topic


class SqlPracticeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_problems(
        self,
        *,
        search: str | None = None,
        difficulty: Difficulty | None = None,
        topic_slug: str | None = None,
        tag: str | None = None,
        status: SqlProgressStatus | None = None,
        user_id: UUID | None = None,
        skip: int = 0,
        limit: int = 50,
        active_only: bool = True,
    ) -> tuple[list[SqlProblem], int]:
        stmt = select(SqlProblem)
        if active_only:
            stmt = stmt.where(SqlProblem.is_active.is_(True))
        if difficulty:
            stmt = stmt.where(SqlProblem.difficulty == difficulty)
        if search:
            like = f"%{search}%"
            stmt = stmt.where(or_(SqlProblem.title.ilike(like), SqlProblem.slug.ilike(like)))
        if topic_slug:
            stmt = stmt.join(Topic, Topic.id == SqlProblem.topic_id).where(Topic.slug == topic_slug)
        if tag:
            stmt = stmt.where(SqlProblem.tags.contains([tag]))

        if status and user_id:
            if status == SqlProgressStatus.UNSOLVED:
                solved_or_attempted = select(SqlProblemProgress.problem_id).where(
                    SqlProblemProgress.user_id == user_id
                )
                stmt = stmt.where(SqlProblem.id.notin_(solved_or_attempted))
            else:
                stmt = stmt.join(
                    SqlProblemProgress,
                    (SqlProblemProgress.problem_id == SqlProblem.id)
                    & (SqlProblemProgress.user_id == user_id),
                ).where(SqlProblemProgress.status == status)

        count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(SqlProblem.difficulty, SqlProblem.title).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().unique().all()), total

    async def get_by_id(self, problem_id: UUID, *, load_dataset: bool = False) -> SqlProblem | None:
        stmt = select(SqlProblem).where(SqlProblem.id == problem_id)
        if load_dataset:
            stmt = stmt.options(
                selectinload(SqlProblem.tables).selectinload(SqlProblemTable.columns),
                selectinload(SqlProblem.tables).selectinload(SqlProblemTable.seed_rows),
                selectinload(SqlProblem.expected_result),
            )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str, *, load_dataset: bool = False) -> SqlProblem | None:
        stmt = select(SqlProblem).where(SqlProblem.slug == slug)
        if load_dataset:
            stmt = stmt.options(
                selectinload(SqlProblem.tables).selectinload(SqlProblemTable.columns),
                selectinload(SqlProblem.tables).selectinload(SqlProblemTable.seed_rows),
                selectinload(SqlProblem.expected_result),
            )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_topic(self, topic_id: UUID) -> Topic | None:
        result = await self.db.execute(select(Topic).where(Topic.id == topic_id))
        return result.scalar_one_or_none()

    async def get_progress(self, user_id: UUID, problem_id: UUID) -> SqlProblemProgress | None:
        result = await self.db.execute(
            select(SqlProblemProgress).where(
                SqlProblemProgress.user_id == user_id,
                SqlProblemProgress.problem_id == problem_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_progress_for_user(self, user_id: UUID) -> list[SqlProblemProgress]:
        result = await self.db.execute(
            select(SqlProblemProgress).where(SqlProblemProgress.user_id == user_id)
        )
        return list(result.scalars().all())

    async def upsert_progress(
        self,
        user_id: UUID,
        problem_id: UUID,
        *,
        solved: bool,
        execution_time_ms: float | None = None,
    ) -> SqlProblemProgress:
        progress = await self.get_progress(user_id, problem_id)
        now = datetime.now(timezone.utc)
        if progress is None:
            progress = SqlProblemProgress(
                user_id=user_id,
                problem_id=problem_id,
                status=SqlProgressStatus.SOLVED if solved else SqlProgressStatus.ATTEMPTED,
                attempt_count=1,
                first_attempted_at=now,
                last_attempt_at=now,
                first_solved_at=now if solved else None,
                best_execution_time_ms=execution_time_ms if solved else None,
            )
            self.db.add(progress)
        else:
            progress.attempt_count += 1
            progress.last_attempt_at = now
            if progress.first_attempted_at is None:
                progress.first_attempted_at = now
            if solved:
                if progress.status != SqlProgressStatus.SOLVED:
                    progress.status = SqlProgressStatus.SOLVED
                    progress.first_solved_at = now
                if execution_time_ms is not None:
                    if (
                        progress.best_execution_time_ms is None
                        or execution_time_ms < progress.best_execution_time_ms
                    ):
                        progress.best_execution_time_ms = execution_time_ms
            elif progress.status != SqlProgressStatus.SOLVED:
                progress.status = SqlProgressStatus.ATTEMPTED
        await self.db.flush()
        return progress

    async def save_submission(self, submission: SqlSubmission) -> SqlSubmission:
        self.db.add(submission)
        await self.db.flush()
        return submission

    async def get_submission(self, submission_id: UUID) -> SqlSubmission | None:
        result = await self.db.execute(
            select(SqlSubmission).where(SqlSubmission.id == submission_id)
        )
        return result.scalar_one_or_none()

    async def list_submissions(
        self,
        user_id: UUID,
        *,
        problem_id: UUID | None = None,
        status: SqlSubmissionStatus | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[SqlSubmission], int]:
        stmt = select(SqlSubmission).where(SqlSubmission.user_id == user_id)
        if problem_id:
            stmt = stmt.where(SqlSubmission.problem_id == problem_id)
        if status:
            stmt = stmt.where(SqlSubmission.status == status)
        count = (
            await self.db.execute(select(func.count()).select_from(stmt.order_by(None).subquery()))
        ).scalar_one()
        stmt = stmt.order_by(SqlSubmission.submitted_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), count

    async def is_bookmarked(self, user_id: UUID, sql_problem_id: UUID) -> bool:
        result = await self.db.execute(
            select(Bookmark.id).where(
                Bookmark.user_id == user_id, Bookmark.sql_problem_id == sql_problem_id
            )
        )
        return result.scalar_one_or_none() is not None

    async def toggle_bookmark(self, user_id: UUID, sql_problem_id: UUID) -> bool:
        result = await self.db.execute(
            select(Bookmark).where(
                Bookmark.user_id == user_id, Bookmark.sql_problem_id == sql_problem_id
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            await self.db.delete(existing)
            await self.db.flush()
            return False
        self.db.add(Bookmark(user_id=user_id, sql_problem_id=sql_problem_id))
        await self.db.flush()
        return True

    async def list_bookmarks(self, user_id: UUID) -> list[SqlProblem]:
        stmt = (
            select(SqlProblem)
            .join(Bookmark, Bookmark.sql_problem_id == SqlProblem.id)
            .where(Bookmark.user_id == user_id)
            .order_by(Bookmark.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def acceptance_rates(self, problem_ids: list[UUID]) -> dict[UUID, float]:
        if not problem_ids:
            return {}
        stmt = (
            select(
                SqlSubmission.problem_id,
                (
                    func.sum(
                        case(
                            (SqlSubmission.status == SqlSubmissionStatus.ACCEPTED, 1),
                            else_=0,
                        )
                    )
                    * 100.0
                    / func.nullif(func.count(), 0)
                ).label("rate"),
            )
            .where(SqlSubmission.problem_id.in_(problem_ids))
            .group_by(SqlSubmission.problem_id)
        )
        result = await self.db.execute(stmt)
        return {row.problem_id: float(row.rate or 0) for row in result.all()}

    async def save_problem(self, problem: SqlProblem) -> SqlProblem:
        self.db.add(problem)
        await self.db.flush()
        return problem

    async def delete_problem(self, problem: SqlProblem) -> None:
        await self.db.delete(problem)
        await self.db.flush()

    async def replace_dataset(
        self,
        problem: SqlProblem,
        tables_data: list[dict],
        expected_columns: list[str],
        expected_rows: list[list],
    ) -> None:
        # Clear existing
        for table in list(problem.tables):
            await self.db.delete(table)
        if problem.expected_result:
            await self.db.delete(problem.expected_result)
        await self.db.flush()

        for t_idx, t in enumerate(tables_data):
            table = SqlProblemTable(
                problem_id=problem.id,
                table_name=t["table_name"],
                display_name=t.get("display_name"),
                description=t.get("description"),
                sort_order=t.get("sort_order", t_idx),
            )
            self.db.add(table)
            await self.db.flush()
            for c_idx, col in enumerate(t.get("columns", [])):
                self.db.add(
                    SqlProblemColumn(
                        table_id=table.id,
                        column_name=col["column_name"],
                        data_type=col["data_type"],
                        is_nullable=col.get("is_nullable", True),
                        sort_order=col.get("sort_order", c_idx),
                    )
                )
            for r_idx, row in enumerate(t.get("rows", [])):
                self.db.add(
                    SqlProblemSeedRow(
                        table_id=table.id,
                        row_data=row,
                        sort_order=r_idx,
                        is_sample=True,
                    )
                )

        self.db.add(
            SqlExpectedResult(
                problem_id=problem.id,
                columns=expected_columns,
                rows=expected_rows,
            )
        )
        await self.db.flush()

    async def count_by_difficulty(self) -> dict[str, int]:
        stmt = (
            select(SqlProblem.difficulty, func.count())
            .where(SqlProblem.is_active.is_(True))
            .group_by(SqlProblem.difficulty)
        )
        result = await self.db.execute(stmt)
        return {str(diff.value if hasattr(diff, "value") else diff): count for diff, count in result.all()}
