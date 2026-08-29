from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppException
from app.models.enums import Difficulty
from app.models.sql_enums import SqlDialect, SqlProgressStatus, SqlSubmissionStatus
from app.models.sql_practice import SqlProblem, SqlSubmission
from app.models.user import User
from app.repositories.sql_practice_repository import SqlPracticeRepository
from app.schemas.sql_practice import (
    AdminSqlProblemCreate,
    AdminSqlProblemDetail,
    AdminSqlProblemListResponse,
    AdminSqlProblemUpdate,
    AdminSqlTableInput,
    AdminSqlValidateResponse,
    DifficultyBreakdown,
    SqlColumnSchema,
    SqlExecutionStatusResponse,
    SqlProblemDetail,
    SqlProblemListItem,
    SqlProgressSummary,
    SqlRunResponse,
    SqlSolutionResponse,
    SqlSubmissionDetail,
    SqlSubmissionListItem,
    SqlSubmitResponse,
    SqlTablePreview,
    SqlTableSchemaPublic,
    TopicBreakdown,
)
from app.services.sql_execution import (
    compare_results,
    get_sql_executor,
    validate_sql_query,
)
from app.services.sql_execution.executor import SqlSandboxExecutor


class SqlPracticeService:
    def __init__(self, db: AsyncSession, executor: SqlSandboxExecutor | None = None):
        self.db = db
        self.repo = SqlPracticeRepository(db)
        self.executor = executor or get_sql_executor()

    def execution_status(self) -> SqlExecutionStatusResponse:
        available = self.executor.is_available()
        return SqlExecutionStatusResponse(
            available=available,
            dialect="postgresql",
            message=None if available else "SQL execution is currently unavailable.",
            timeout_ms=settings.sql_query_timeout_ms,
            max_rows=settings.sql_max_rows,
        )

    async def list_problems(
        self,
        user: User,
        *,
        search: str | None = None,
        difficulty: str | None = None,
        topic_slug: str | None = None,
        tag: str | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> dict[str, Any]:
        diff = Difficulty(difficulty) if difficulty else None
        prog = SqlProgressStatus(status) if status else None
        problems, total = await self.repo.list_problems(
            search=search,
            difficulty=diff,
            topic_slug=topic_slug,
            tag=tag,
            status=prog,
            user_id=user.id,
            skip=skip,
            limit=limit,
        )
        progress_map = {p.problem_id: p for p in await self.repo.list_progress_for_user(user.id)}
        rates = await self.repo.acceptance_rates([p.id for p in problems])
        items = []
        for problem in problems:
            topic = await self.repo.get_topic(problem.topic_id)
            prog_row = progress_map.get(problem.id)
            items.append(
                SqlProblemListItem(
                    id=problem.id,
                    slug=problem.slug,
                    title=problem.title,
                    difficulty=problem.difficulty,
                    topic_id=problem.topic_id,
                    topic_name=topic.name if topic else None,
                    topic_slug=topic.slug if topic else None,
                    tags=list(problem.tags or []),
                    role_tags=list(problem.role_tags or []),
                    estimated_time_seconds=problem.estimated_time_seconds,
                    progress_status=prog_row.status if prog_row else SqlProgressStatus.UNSOLVED,
                    acceptance_rate=rates.get(problem.id),
                    attempt_count=prog_row.attempt_count if prog_row else 0,
                )
            )
        return {"items": items, "total": total}

    async def get_problem(self, user: User, slug_or_id: str) -> SqlProblemDetail:
        problem = await self._resolve_problem(slug_or_id, load_dataset=True)
        if not problem or not problem.is_active:
            raise AppException("SQL problem not found", status_code=404)
        return await self._to_public_detail(user, problem)

    async def get_schema(self, user: User, problem_id: UUID) -> list[SqlTableSchemaPublic]:
        problem = await self.repo.get_by_id(problem_id, load_dataset=True)
        if not problem or not problem.is_active:
            raise AppException("SQL problem not found", status_code=404)
        return self._schema_tables(problem)

    async def get_table_preview(
        self, user: User, problem_id: UUID, table_name: str, limit: int = 10
    ) -> SqlTablePreview:
        problem = await self.repo.get_by_id(problem_id, load_dataset=True)
        if not problem or not problem.is_active:
            raise AppException("SQL problem not found", status_code=404)
        table = next((t for t in problem.tables if t.table_name == table_name), None)
        if table is None:
            raise AppException("Table not found", status_code=404)
        cols = [c.column_name for c in sorted(table.columns, key=lambda c: c.sort_order)]
        sample_rows = sorted(table.seed_rows, key=lambda r: r.sort_order)
        truncated = len(sample_rows) > limit
        rows = [[r.row_data.get(c) for c in cols] for r in sample_rows[:limit]]
        return SqlTablePreview(
            table_name=table.table_name, columns=cols, rows=rows, truncated=truncated
        )

    async def run_query(self, user: User, problem_id: UUID, query: str) -> SqlRunResponse:
        if not self.executor.is_available():
            raise AppException("SQL execution is currently unavailable.", status_code=503)
        problem = await self.repo.get_by_id(problem_id, load_dataset=True)
        if not problem or not problem.is_active:
            raise AppException("SQL problem not found", status_code=404)

        safety = validate_sql_query(query, max_length=settings.sql_max_query_length)
        if safety:
            return SqlRunResponse(error=safety, status="sql_error")

        result = await self.executor.execute(query, self._dataset_payload(problem))
        if result.disabled:
            raise AppException(result.error or "SQL execution unavailable", status_code=503)
        if result.timed_out:
            return SqlRunResponse(
                error=result.error or "Query timed out.",
                status="timeout",
                execution_time_ms=result.execution_time_ms,
            )
        if result.error:
            return SqlRunResponse(
                error=result.error,
                status="sql_error",
                execution_time_ms=result.execution_time_ms,
            )
        return SqlRunResponse(
            columns=result.columns,
            rows=result.rows,
            row_count=result.row_count,
            execution_time_ms=result.execution_time_ms,
            truncated=result.truncated,
            status="ok",
        )

    async def submit_query(self, user: User, problem_id: UUID, query: str) -> SqlSubmitResponse:
        if not self.executor.is_available():
            submission = SqlSubmission(
                user_id=user.id,
                problem_id=problem_id,
                query_text=query,
                status=SqlSubmissionStatus.EXECUTION_DISABLED,
                error_message="SQL execution is currently unavailable.",
            )
            await self.repo.save_submission(submission)
            await self.db.commit()
            raise AppException("SQL execution is currently unavailable.", status_code=503)

        problem = await self.repo.get_by_id(problem_id, load_dataset=True)
        if not problem or not problem.is_active:
            raise AppException("SQL problem not found", status_code=404)

        safety = validate_sql_query(query, max_length=settings.sql_max_query_length)
        if safety:
            submission = SqlSubmission(
                user_id=user.id,
                problem_id=problem.id,
                query_text=query,
                status=SqlSubmissionStatus.SQL_ERROR,
                error_message=safety,
            )
            await self.repo.save_submission(submission)
            await self.repo.upsert_progress(user.id, problem.id, solved=False)
            await self.db.commit()
            return SqlSubmitResponse(
                submission_id=submission.id,
                status=SqlSubmissionStatus.SQL_ERROR,
                message=safety,
                error=safety,
            )

        # Submit: evaluate full result up to submit_max_rows (no display truncation)
        result = await self.executor.execute(
            query, self._dataset_payload(problem), for_submit=True
        )

        if result.timed_out:
            status = SqlSubmissionStatus.TIMEOUT
            message = "Query timed out."
            feedback = None
        elif result.error:
            status = SqlSubmissionStatus.SQL_ERROR
            message = result.error
            feedback = None
        else:
            expected = problem.expected_result
            if expected is None:
                status = SqlSubmissionStatus.INTERNAL_ERROR
                message = "Expected result is not configured."
                feedback = None
            else:
                comparison = compare_results(
                    expected_columns=list(expected.columns),
                    expected_rows=list(expected.rows),
                    actual_columns=result.columns,
                    actual_rows=result.rows,
                    order_sensitive=problem.order_sensitive,
                )
                if comparison["matched"]:
                    status = SqlSubmissionStatus.ACCEPTED
                    message = "Accepted"
                    feedback = None
                else:
                    status = SqlSubmissionStatus.WRONG_ANSWER
                    message = comparison.get("message", "Wrong Answer")
                    feedback = {
                        k: v
                        for k, v in comparison.items()
                        if k not in ("matched",)
                    }

        submission = SqlSubmission(
            user_id=user.id,
            problem_id=problem.id,
            query_text=query,
            status=status,
            result_row_count=result.row_count if not result.error else None,
            execution_time_ms=result.execution_time_ms,
            error_message=result.error if status == SqlSubmissionStatus.SQL_ERROR else None,
            feedback=feedback,
        )
        await self.repo.save_submission(submission)
        await self.repo.upsert_progress(
            user.id,
            problem.id,
            solved=status == SqlSubmissionStatus.ACCEPTED,
            execution_time_ms=result.execution_time_ms
            if status == SqlSubmissionStatus.ACCEPTED
            else None,
        )
        await self.db.commit()

        return SqlSubmitResponse(
            submission_id=submission.id,
            status=status,
            message=message,
            execution_time_ms=result.execution_time_ms,
            result_row_count=result.row_count if not result.error else None,
            feedback=feedback,
            columns=result.columns if status != SqlSubmissionStatus.SQL_ERROR else [],
            rows=result.rows[: settings.sql_max_rows]
            if status != SqlSubmissionStatus.SQL_ERROR
            else [],
            truncated=result.truncated,
            error=result.error if status == SqlSubmissionStatus.SQL_ERROR else None,
            solution_unlocked=status == SqlSubmissionStatus.ACCEPTED,
        )

    async def list_submissions(
        self,
        user: User,
        *,
        problem_id: UUID | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> dict[str, Any]:
        st = SqlSubmissionStatus(status) if status else None
        rows, total = await self.repo.list_submissions(
            user.id, problem_id=problem_id, status=st, skip=skip, limit=limit
        )
        items = []
        for sub in rows:
            problem = await self.repo.get_by_id(sub.problem_id)
            topic = await self.repo.get_topic(problem.topic_id) if problem else None
            items.append(
                SqlSubmissionListItem(
                    id=sub.id,
                    problem_id=sub.problem_id,
                    problem_slug=problem.slug if problem else "",
                    problem_title=problem.title if problem else "Unknown",
                    difficulty=problem.difficulty if problem else None,
                    topic_name=topic.name if topic else None,
                    status=sub.status,
                    result_row_count=sub.result_row_count,
                    execution_time_ms=sub.execution_time_ms,
                    submitted_at=sub.submitted_at,
                )
            )
        return {"items": items, "total": total}

    async def get_submission(self, user: User, submission_id: UUID) -> SqlSubmissionDetail:
        sub = await self.repo.get_submission(submission_id)
        if sub is None or sub.user_id != user.id:
            raise AppException("Submission not found", status_code=404)
        problem = await self.repo.get_by_id(sub.problem_id)
        return SqlSubmissionDetail(
            id=sub.id,
            problem_id=sub.problem_id,
            problem_slug=problem.slug if problem else "",
            problem_title=problem.title if problem else "Unknown",
            difficulty=problem.difficulty if problem else None,
            query_text=sub.query_text,
            status=sub.status,
            result_row_count=sub.result_row_count,
            execution_time_ms=sub.execution_time_ms,
            error_message=sub.error_message,
            feedback=sub.feedback,
            submitted_at=sub.submitted_at,
        )

    async def get_progress(self, user: User) -> SqlProgressSummary:
        problems, _ = await self.repo.list_problems(limit=500)
        progress_map = {p.problem_id: p for p in await self.repo.list_progress_for_user(user.id)}

        def breakdown(diff: Difficulty) -> DifficultyBreakdown:
            subset = [p for p in problems if p.difficulty == diff]
            solved = sum(
                1
                for p in subset
                if progress_map.get(p.id) and progress_map[p.id].status == SqlProgressStatus.SOLVED
            )
            attempted = sum(1 for p in subset if p.id in progress_map)
            return DifficultyBreakdown(solved=solved, total=len(subset), attempted=attempted)

        topic_stats: dict[UUID, TopicBreakdown] = {}
        for problem in problems:
            topic = await self.repo.get_topic(problem.topic_id)
            if topic is None:
                continue
            entry = topic_stats.setdefault(
                topic.id,
                TopicBreakdown(topic_slug=topic.slug, topic_name=topic.name),
            )
            entry.total += 1
            prog = progress_map.get(problem.id)
            if prog and prog.status == SqlProgressStatus.SOLVED:
                entry.solved += 1

        solved_count = sum(
            1 for p in progress_map.values() if p.status == SqlProgressStatus.SOLVED
        )
        return SqlProgressSummary(
            total_problems=len(problems),
            solved_count=solved_count,
            attempted_count=len(progress_map),
            easy=breakdown(Difficulty.EASY),
            medium=breakdown(Difficulty.MEDIUM),
            hard=breakdown(Difficulty.HARD),
            topics=list(topic_stats.values()),
        )

    async def toggle_bookmark(self, user: User, problem_id: UUID) -> dict[str, bool]:
        problem = await self.repo.get_by_id(problem_id)
        if not problem:
            raise AppException("SQL problem not found", status_code=404)
        bookmarked = await self.repo.toggle_bookmark(user.id, problem_id)
        await self.db.commit()
        return {"bookmarked": bookmarked}

    async def list_bookmarks(self, user: User) -> list[SqlProblemListItem]:
        problems = await self.repo.list_bookmarks(user.id)
        items = []
        for problem in problems:
            topic = await self.repo.get_topic(problem.topic_id)
            items.append(
                SqlProblemListItem(
                    id=problem.id,
                    slug=problem.slug,
                    title=problem.title,
                    difficulty=problem.difficulty,
                    topic_id=problem.topic_id,
                    topic_name=topic.name if topic else None,
                    topic_slug=topic.slug if topic else None,
                    tags=list(problem.tags or []),
                    role_tags=list(problem.role_tags or []),
                    estimated_time_seconds=problem.estimated_time_seconds,
                    progress_status=SqlProgressStatus.UNSOLVED,
                )
            )
        return items

    async def get_solution(self, user: User, problem_id: UUID) -> SqlSolutionResponse:
        problem = await self.repo.get_by_id(problem_id)
        if not problem or not problem.is_active:
            raise AppException("SQL problem not found", status_code=404)
        progress = await self.repo.get_progress(user.id, problem_id)
        if not progress or progress.status != SqlProgressStatus.SOLVED:
            raise AppException("Solve this problem to unlock the solution.", status_code=403)
        return SqlSolutionResponse(
            solution_query=problem.solution_query,
            solution_explanation=problem.solution_explanation,
            alternate_solution=problem.alternate_solution,
            key_concepts=list(problem.key_concepts or []),
        )

    async def _resolve_problem(self, slug_or_id: str, *, load_dataset: bool) -> SqlProblem | None:
        try:
            pid = UUID(slug_or_id)
            return await self.repo.get_by_id(pid, load_dataset=load_dataset)
        except ValueError:
            return await self.repo.get_by_slug(slug_or_id, load_dataset=load_dataset)

    async def _to_public_detail(self, user: User, problem: SqlProblem) -> SqlProblemDetail:
        topic = await self.repo.get_topic(problem.topic_id)
        progress = await self.repo.get_progress(user.id, problem.id)
        bookmarked = await self.repo.is_bookmarked(user.id, problem.id)
        unlocked = bool(progress and progress.status == SqlProgressStatus.SOLVED)
        return SqlProblemDetail(
            id=problem.id,
            slug=problem.slug,
            title=problem.title,
            description=problem.description,
            difficulty=problem.difficulty,
            database_dialect=problem.database_dialect or SqlDialect.POSTGRESQL,
            topic_id=problem.topic_id,
            topic_name=topic.name if topic else None,
            topic_slug=topic.slug if topic else None,
            tags=list(problem.tags or []),
            role_tags=list(problem.role_tags or []),
            scenario=problem.scenario,
            task_description=problem.task_description,
            expected_columns=list(problem.expected_columns or []),
            sample_expected_rows=list(problem.sample_expected_rows or []),
            hints=list(problem.hints or []),
            estimated_time_seconds=problem.estimated_time_seconds,
            order_sensitive=problem.order_sensitive,
            schema_tables=self._schema_tables(problem),
            progress_status=progress.status if progress else SqlProgressStatus.UNSOLVED,
            bookmarked=bookmarked,
            solution_unlocked=unlocked,
            execution_available=self.executor.is_available(),
        )

    def _schema_tables(self, problem: SqlProblem) -> list[SqlTableSchemaPublic]:
        out = []
        for table in sorted(problem.tables, key=lambda t: t.sort_order):
            out.append(
                SqlTableSchemaPublic(
                    table_name=table.table_name,
                    display_name=table.display_name,
                    description=table.description,
                    columns=[
                        SqlColumnSchema(
                            column_name=c.column_name,
                            data_type=c.data_type,
                            is_nullable=c.is_nullable,
                            sort_order=c.sort_order,
                        )
                        for c in sorted(table.columns, key=lambda c: c.sort_order)
                    ],
                )
            )
        return out

    def _dataset_payload(self, problem: SqlProblem) -> list[dict[str, Any]]:
        tables = []
        for table in sorted(problem.tables, key=lambda t: t.sort_order):
            tables.append(
                {
                    "table_name": table.table_name,
                    "columns": [
                        {
                            "column_name": c.column_name,
                            "data_type": c.data_type,
                            "is_nullable": c.is_nullable,
                        }
                        for c in sorted(table.columns, key=lambda c: c.sort_order)
                    ],
                    "rows": [
                        r.row_data
                        for r in sorted(table.seed_rows, key=lambda r: r.sort_order)
                    ],
                }
            )
        return tables


class AdminSqlPracticeService:
    def __init__(self, db: AsyncSession, executor: SqlSandboxExecutor | None = None):
        self.db = db
        self.repo = SqlPracticeRepository(db)
        self.executor = executor or get_sql_executor()

    async def list_problems(
        self, *, search: str | None = None, skip: int = 0, limit: int = 50
    ) -> AdminSqlProblemListResponse:
        problems, total = await self.repo.list_problems(
            search=search, skip=skip, limit=limit, active_only=False
        )
        items = [
            SqlProblemListItem(
                id=p.id,
                slug=p.slug,
                title=p.title,
                difficulty=p.difficulty,
                topic_id=p.topic_id,
                tags=list(p.tags or []),
                role_tags=list(p.role_tags or []),
                estimated_time_seconds=p.estimated_time_seconds,
            )
            for p in problems
        ]
        return AdminSqlProblemListResponse(items=items, total=total)

    async def get_problem(self, problem_id: UUID) -> AdminSqlProblemDetail:
        problem = await self.repo.get_by_id(problem_id, load_dataset=True)
        if problem is None:
            raise AppException("SQL problem not found", status_code=404)
        return self._to_admin_detail(problem)

    async def create_problem(
        self, admin: User, payload: AdminSqlProblemCreate
    ) -> AdminSqlProblemDetail:
        existing = await self.repo.get_by_slug(payload.slug)
        if existing:
            raise AppException("Slug already exists", status_code=400)
        problem = SqlProblem(
            slug=payload.slug,
            title=payload.title,
            description=payload.description,
            difficulty=payload.difficulty,
            domain_id=payload.domain_id,
            category_id=payload.category_id,
            topic_id=payload.topic_id,
            subtopic_id=payload.subtopic_id,
            tags=payload.tags,
            role_tags=payload.role_tags,
            scenario=payload.scenario,
            task_description=payload.task_description,
            expected_columns=payload.expected_columns,
            order_sensitive=payload.order_sensitive,
            solution_query=payload.solution_query,
            solution_explanation=payload.solution_explanation,
            alternate_solution=payload.alternate_solution,
            key_concepts=payload.key_concepts,
            hints=payload.hints,
            sample_expected_rows=payload.sample_expected_rows,
            estimated_time_seconds=payload.estimated_time_seconds,
            is_active=payload.is_active,
            is_sample=payload.is_sample,
            created_by=admin.id,
        )
        await self.repo.save_problem(problem)
        await self.repo.replace_dataset(
            problem,
            [t.model_dump() for t in payload.tables],
            payload.expected_columns,
            payload.expected_rows,
        )
        await self.db.commit()
        problem = await self.repo.get_by_id(problem.id, load_dataset=True)
        return self._to_admin_detail(problem)  # type: ignore[arg-type]

    async def update_problem(
        self, problem_id: UUID, payload: AdminSqlProblemUpdate
    ) -> AdminSqlProblemDetail:
        problem = await self.repo.get_by_id(problem_id, load_dataset=True)
        if problem is None:
            raise AppException("SQL problem not found", status_code=404)
        data = payload.model_dump(exclude_unset=True, exclude={"tables", "expected_rows"})
        if "slug" in data and data["slug"] != problem.slug:
            existing = await self.repo.get_by_slug(data["slug"])
            if existing:
                raise AppException("Slug already exists", status_code=400)
        for key, value in data.items():
            setattr(problem, key, value)
        if payload.tables is not None:
            cols = payload.expected_columns if payload.expected_columns is not None else problem.expected_columns
            rows = (
                payload.expected_rows
                if payload.expected_rows is not None
                else (problem.expected_result.rows if problem.expected_result else [])
            )
            await self.repo.replace_dataset(
                problem, [t.model_dump() for t in payload.tables], list(cols), list(rows)
            )
        elif payload.expected_rows is not None or payload.expected_columns is not None:
            cols = payload.expected_columns if payload.expected_columns is not None else problem.expected_columns
            rows = (
                payload.expected_rows
                if payload.expected_rows is not None
                else (problem.expected_result.rows if problem.expected_result else [])
            )
            if problem.expected_result:
                problem.expected_result.columns = list(cols)
                problem.expected_result.rows = list(rows)
        await self.db.commit()
        problem = await self.repo.get_by_id(problem_id, load_dataset=True)
        return self._to_admin_detail(problem)  # type: ignore[arg-type]

    async def delete_problem(self, problem_id: UUID) -> None:
        problem = await self.repo.get_by_id(problem_id)
        if problem is None:
            raise AppException("SQL problem not found", status_code=404)
        problem.is_active = False
        await self.db.commit()

    async def validate_problem(self, problem_id: UUID) -> AdminSqlValidateResponse:
        problem = await self.repo.get_by_id(problem_id, load_dataset=True)
        if problem is None:
            raise AppException("SQL problem not found", status_code=404)

        errors: list[str] = []
        warnings: list[str] = []

        if not problem.tables:
            errors.append("Problem has no tables defined.")
        if not problem.solution_query:
            errors.append("Solution query is required.")
        else:
            safety = validate_sql_query(problem.solution_query)
            if safety:
                errors.append(f"Solution query unsafe: {safety}")

        if not self.executor.is_available():
            warnings.append("Sandbox unavailable — skipped live validation.")
            return AdminSqlValidateResponse(valid=len(errors) == 0, errors=errors, warnings=warnings)

        if errors:
            return AdminSqlValidateResponse(valid=False, errors=errors, warnings=warnings)

        service = SqlPracticeService(self.db, self.executor)
        result = await self.executor.execute(
            problem.solution_query, service._dataset_payload(problem), for_submit=True
        )
        if result.error:
            errors.append(f"Solution failed to execute: {result.error}")
            return AdminSqlValidateResponse(valid=False, errors=errors, warnings=warnings)

        expected = problem.expected_result
        if expected is None:
            errors.append("Expected result is missing.")
        else:
            comparison = compare_results(
                expected_columns=list(expected.columns),
                expected_rows=list(expected.rows),
                actual_columns=result.columns,
                actual_rows=result.rows,
                order_sensitive=problem.order_sensitive,
            )
            if not comparison["matched"]:
                errors.append(
                    f"Solution result does not match expected result ({comparison.get('reason')})."
                )

        if list(problem.expected_columns) != result.columns:
            warnings.append("expected_columns metadata differs from solution output columns.")

        return AdminSqlValidateResponse(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            solution_columns=result.columns,
            solution_row_count=result.row_count,
        )

    def _to_admin_detail(self, problem: SqlProblem) -> AdminSqlProblemDetail:
        tables = []
        for table in sorted(problem.tables, key=lambda t: t.sort_order):
            tables.append(
                AdminSqlTableInput(
                    table_name=table.table_name,
                    display_name=table.display_name,
                    description=table.description,
                    sort_order=table.sort_order,
                    columns=[
                        {
                            "column_name": c.column_name,
                            "data_type": c.data_type,
                            "is_nullable": c.is_nullable,
                            "sort_order": c.sort_order,
                        }
                        for c in sorted(table.columns, key=lambda c: c.sort_order)
                    ],
                    rows=[r.row_data for r in sorted(table.seed_rows, key=lambda r: r.sort_order)],
                )
            )
        expected_rows = list(problem.expected_result.rows) if problem.expected_result else []
        return AdminSqlProblemDetail(
            id=problem.id,
            slug=problem.slug,
            title=problem.title,
            description=problem.description,
            difficulty=problem.difficulty,
            database_dialect=problem.database_dialect or SqlDialect.POSTGRESQL,
            domain_id=problem.domain_id,
            category_id=problem.category_id,
            topic_id=problem.topic_id,
            subtopic_id=problem.subtopic_id,
            tags=list(problem.tags or []),
            role_tags=list(problem.role_tags or []),
            scenario=problem.scenario,
            task_description=problem.task_description,
            expected_columns=list(problem.expected_columns or []),
            order_sensitive=problem.order_sensitive,
            solution_query=problem.solution_query,
            solution_explanation=problem.solution_explanation,
            alternate_solution=problem.alternate_solution,
            key_concepts=list(problem.key_concepts or []),
            hints=list(problem.hints or []),
            sample_expected_rows=list(problem.sample_expected_rows or []),
            estimated_time_seconds=problem.estimated_time_seconds,
            is_active=problem.is_active,
            is_sample=problem.is_sample,
            tables=tables,
            expected_rows=expected_rows,
        )
