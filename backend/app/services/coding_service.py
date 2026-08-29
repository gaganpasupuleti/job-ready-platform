from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppException
from app.models.coding import (
    CodingProblem,
    CodingProblemProgress,
    CodingSubmission,
    CodingSubmissionResult,
    CodingTestCase,
)
from app.models.coding_enums import ProblemProgressStatus, SubmissionStatus, SubmissionType
from app.models.user import User
from app.repositories.coding_repository import CodingRepository
from app.schemas.coding import (
    AdminCodingProblemCreate,
    AdminCodingProblemDetail,
    AdminCodingProblemListResponse,
    AdminCodingProblemUpdate,
    AdminTestCaseCreate,
    AdminTestCaseDetail,
    AdminTestCaseUpdate,
    BookmarkedProblemItem,
    CodingProblemDetail,
    CodingProblemListItem,
    CodingProblemListResponse,
    CodingProgressSummary,
    DifficultyBreakdown,
    ExecutionResponse,
    ExecutionStatusResponse,
    LanguageInfo,
    RunSubmitRequest,
    SampleTestCasePublic,
    SubmissionDetail,
    SubmissionListItem,
    SubmissionListResponse,
    TestResultPublic,
    TopicBreakdown,
)
from app.services.code_execution.interface import CodeExecutionService, ExecutionRequest
from app.services.code_execution.languages import (
    SUPPORTED_LANGUAGES,
    get_language_name,
    list_languages,
)
from app.services.code_execution.disabled import DisabledCodeExecutionService

STATUS_PRIORITY = [
    SubmissionStatus.COMPILATION_ERROR,
    SubmissionStatus.RUNTIME_ERROR,
    SubmissionStatus.TIME_LIMIT_EXCEEDED,
    SubmissionStatus.MEMORY_LIMIT_EXCEEDED,
    SubmissionStatus.INTERNAL_ERROR,
    SubmissionStatus.WRONG_ANSWER,
    SubmissionStatus.ACCEPTED,
]


def _map_execution_status(raw: str) -> SubmissionStatus:
    mapping = {
        "accepted": SubmissionStatus.ACCEPTED,
        "wrong_answer": SubmissionStatus.WRONG_ANSWER,
        "time_limit_exceeded": SubmissionStatus.TIME_LIMIT_EXCEEDED,
        "memory_limit_exceeded": SubmissionStatus.MEMORY_LIMIT_EXCEEDED,
        "runtime_error": SubmissionStatus.RUNTIME_ERROR,
        "compilation_error": SubmissionStatus.COMPILATION_ERROR,
        "internal_error": SubmissionStatus.INTERNAL_ERROR,
        "service_unavailable": SubmissionStatus.INTERNAL_ERROR,
    }
    return mapping.get(raw, SubmissionStatus.INTERNAL_ERROR)


def _aggregate_status(statuses: list[SubmissionStatus]) -> SubmissionStatus:
    if not statuses:
        return SubmissionStatus.INTERNAL_ERROR
    if all(s == SubmissionStatus.ACCEPTED for s in statuses):
        return SubmissionStatus.ACCEPTED
    for priority in STATUS_PRIORITY:
        if priority in statuses and priority != SubmissionStatus.ACCEPTED:
            return priority
    return SubmissionStatus.WRONG_ANSWER


class CodingService:
    def __init__(self, db: AsyncSession, executor: CodeExecutionService):
        self.db = db
        self.repo = CodingRepository(db)
        self.executor = executor

    def is_execution_available(self) -> bool:
        if not settings.judge0_enabled:
            return False
        return not isinstance(self.executor, DisabledCodeExecutionService)

    def get_execution_status(self) -> ExecutionStatusResponse:
        if self.is_execution_available():
            return ExecutionStatusResponse(available=True)
        return ExecutionStatusResponse(
            available=False,
            message="Code execution is currently unavailable.",
        )

    def _validate_language(self, language_id: int) -> str:
        name = get_language_name(language_id)
        if not name:
            raise AppException("Unsupported language", status_code=400)
        return name

    def _validate_source_code(self, source_code: str) -> None:
        if len(source_code) > settings.max_source_code_length:
            raise AppException("Source code exceeds maximum allowed length", status_code=400)

    def _ensure_execution_available(self) -> None:
        if not self.is_execution_available():
            raise AppException(
                "Code execution is currently unavailable.",
                status_code=503,
            )

    def _problem_languages(self, problem: CodingProblem) -> list[LanguageInfo]:
        ids = problem.supported_language_ids or list(SUPPORTED_LANGUAGES.keys())
        return [
            LanguageInfo(id=lid, name=get_language_name(lid) or str(lid))
            for lid in ids
            if get_language_name(lid)
        ]

    async def _build_list_item(
        self,
        problem: CodingProblem,
        *,
        progress_map: dict,
        topic_map: dict,
        acceptance: dict,
        bookmarked: bool | None = None,
    ) -> CodingProblemListItem:
        topic = topic_map.get(problem.topic_id)
        prog = progress_map.get(problem.id)
        return CodingProblemListItem(
            id=problem.id,
            slug=problem.slug,
            title=problem.title,
            difficulty=problem.difficulty,
            domain_id=problem.domain_id,
            category_id=problem.category_id,
            topic_id=problem.topic_id,
            topic_name=topic.name if topic else None,
            topic_slug=topic.slug if topic else None,
            tags=list(problem.tags or []),
            attempts=prog.attempts if prog else 0,
            acceptance_rate=acceptance.get(problem.id),
            progress_status=prog.status if prog else None,
            bookmarked=bookmarked,
        )

    async def list_problems(
        self,
        user: User,
        *,
        domain_id: UUID | None = None,
        topic_id: UUID | None = None,
        topic_slug: str | None = None,
        difficulty: str | None = None,
        search: str | None = None,
        tag: str | None = None,
        language_id: int | None = None,
        progress_status: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> CodingProblemListResponse:
        problems, total = await self.repo.list_problems(
            domain_id=domain_id,
            topic_id=topic_id,
            topic_slug=topic_slug,
            difficulty=difficulty,
            search=search,
            tag=tag,
            language_id=language_id,
            progress_status=progress_status,
            user_id=user.id if progress_status else None,
            skip=skip,
            limit=limit,
        )
        progress_list = await self.repo.list_user_progress(user.id)
        progress_map = {p.problem_id: p for p in progress_list}
        topic_map = await self.repo.get_topic_map()
        acceptance = await self.repo.get_acceptance_rates()
        items = [
            await self._build_list_item(
                p, progress_map=progress_map, topic_map=topic_map, acceptance=acceptance
            )
            for p in problems
        ]
        return CodingProblemListResponse(items=items, total=total)

    async def get_problem(self, user: User, problem_id: UUID) -> CodingProblemDetail:
        problem = await self.repo.get_problem_by_id(problem_id, load_tests=True)
        if problem is None or not problem.is_active:
            raise AppException("Problem not found", status_code=404)

        progress = await self.repo.get_progress(user.id, problem.id)
        bookmarked = await self.repo.is_problem_bookmarked(user.id, problem.id)
        lang_ids = problem.supported_language_ids or list(SUPPORTED_LANGUAGES.keys())
        starter = {k: str(v) for k, v in (problem.starter_code or {}).items()}
        samples = [
            SampleTestCasePublic(
                id=tc.id,
                name=tc.name,
                input=tc.input,
                expected_output=tc.expected_output,
                explanation=tc.explanation,
            )
            for tc in problem.test_cases
            if tc.is_sample and not tc.is_hidden
        ]
        return CodingProblemDetail(
            id=problem.id,
            slug=problem.slug,
            title=problem.title,
            description=problem.description,
            difficulty=problem.difficulty,
            constraints=problem.constraints,
            input_format=problem.input_format,
            output_format=problem.output_format,
            tags=list(problem.tags or []),
            time_limit_ms=problem.time_limit_ms,
            memory_limit_kb=problem.memory_limit_kb,
            starter_code=starter,
            sample_test_cases=samples,
            supported_languages=self._problem_languages(problem),
            progress_status=progress.status if progress else None,
            bookmarked=bookmarked,
            execution_available=self.is_execution_available(),
        )

    async def run_code(
        self, user: User, problem_id: UUID, payload: RunSubmitRequest
    ) -> ExecutionResponse:
        return await self._execute(
            user, problem_id, payload, submission_type=SubmissionType.RUN, hidden=False
        )

    async def submit_code(
        self, user: User, problem_id: UUID, payload: RunSubmitRequest
    ) -> ExecutionResponse:
        response = await self._execute(
            user, problem_id, payload, submission_type=SubmissionType.SUBMIT, hidden=True
        )
        await self.db.commit()
        return response

    async def _execute(
        self,
        user: User,
        problem_id: UUID,
        payload: RunSubmitRequest,
        *,
        submission_type: SubmissionType,
        hidden: bool,
    ) -> ExecutionResponse:
        problem = await self.repo.get_problem_by_id(problem_id, load_tests=True)
        if problem is None or not problem.is_active:
            raise AppException("Problem not found", status_code=404)

        self._ensure_execution_available()
        self._validate_source_code(payload.source_code)
        language_name = self._validate_language(payload.language_id)
        test_cases = sorted(problem.test_cases, key=lambda tc: tc.sort_order)
        if submission_type == SubmissionType.RUN:
            test_cases = [tc for tc in test_cases if not tc.is_hidden]
        if not test_cases:
            raise AppException("No test cases available", status_code=400)

        submission = CodingSubmission(
            user_id=user.id,
            problem_id=problem.id,
            source_code=payload.source_code,
            language_id=payload.language_id,
            language_name=language_name,
            submission_type=submission_type,
            status=SubmissionStatus.RUNNING,
            passed_tests=0,
            total_tests=len(test_cases),
        )

        results: list[CodingSubmissionResult] = []
        statuses: list[SubmissionStatus] = []
        max_time: float | None = None
        max_memory: int | None = None
        passed = 0

        for index, test_case in enumerate(test_cases, start=1):
            exec_result = await self.executor.execute(
                ExecutionRequest(
                    source_code=payload.source_code,
                    language_id=payload.language_id,
                    stdin=test_case.input,
                    expected_output=test_case.expected_output,
                )
            )
            if exec_result.status == "service_unavailable":
                raise AppException(
                    "Code execution is currently unavailable.",
                    status_code=503,
                )
            status = _map_execution_status(exec_result.status)
            statuses.append(status)
            if status == SubmissionStatus.ACCEPTED:
                passed += 1

            if exec_result.time is not None:
                max_time = max(max_time or 0, exec_result.time) * 1000
            if exec_result.memory is not None:
                max_memory = max(max_memory or 0, exec_result.memory)

            results.append(
                CodingSubmissionResult(
                    test_case_id=test_case.id,
                    test_number=index,
                    is_hidden=test_case.is_hidden,
                    status=status,
                    stdout=exec_result.stdout,
                    stderr=exec_result.stderr,
                    execution_time_ms=exec_result.time * 1000 if exec_result.time else None,
                    memory_kb=exec_result.memory,
                )
            )

        submission.status = _aggregate_status(statuses)
        submission.passed_tests = passed
        submission.execution_time_ms = max_time
        submission.memory_kb = max_memory
        submission.results = results
        await self.repo.save_submission(submission)

        if submission_type == SubmissionType.SUBMIT:
            await self._update_progress(user.id, problem, submission)

        public_results = [
            self._public_result(r, test_cases) for r in results
        ]

        await self.db.flush()
        return ExecutionResponse(
            submission_id=submission.id,
            submission_type=submission_type,
            status=submission.status,
            passed_tests=passed,
            total_tests=len(test_cases),
            execution_time_ms=max_time,
            memory_kb=max_memory,
            results=public_results,
        )

    async def _update_progress(
        self, user_id: UUID, problem: CodingProblem, submission: CodingSubmission
    ) -> None:
        progress = await self.repo.get_progress(user_id, problem.id)
        now = datetime.now(UTC)
        if progress is None:
            progress = CodingProblemProgress(
                user_id=user_id,
                problem_id=problem.id,
                status=ProblemProgressStatus.ATTEMPTED,
                attempts=0,
                first_attempted_at=now,
            )
        progress.attempts += 1
        progress.last_attempt_at = now
        if progress.first_attempted_at is None:
            progress.first_attempted_at = now
        if submission.status == SubmissionStatus.ACCEPTED:
            progress.status = ProblemProgressStatus.SOLVED
            progress.best_submission_id = submission.id
            progress.solved_at = progress.solved_at or now
            if submission.execution_time_ms is not None:
                if progress.best_runtime_ms is None or submission.execution_time_ms < progress.best_runtime_ms:
                    progress.best_runtime_ms = submission.execution_time_ms
        elif progress.status != ProblemProgressStatus.SOLVED:
            progress.status = ProblemProgressStatus.ATTEMPTED
        await self.repo.save_progress(progress)

    def _public_result(
        self, result: CodingSubmissionResult, test_cases: list[CodingTestCase]
    ) -> TestResultPublic:
        test_case = next(
            (tc for tc in test_cases if tc.id == result.test_case_id),
            None,
        )
        if result.is_hidden:
            return TestResultPublic(
                test_number=result.test_number,
                name=test_case.name if test_case else f"Hidden test {result.test_number}",
                status=result.status,
                is_hidden=True,
                execution_time_ms=result.execution_time_ms,
                memory_kb=result.memory_kb,
            )
        return TestResultPublic(
            test_number=result.test_number,
            name=test_case.name if test_case else None,
            status=result.status,
            input=test_case.input if test_case else None,
            expected_output=test_case.expected_output if test_case else None,
            stdout=result.stdout,
            stderr=result.stderr,
            execution_time_ms=result.execution_time_ms,
            memory_kb=result.memory_kb,
            is_hidden=False,
        )

    async def list_submissions(
        self,
        user: User,
        *,
        problem_id: UUID | None = None,
        status: str | None = None,
        language_id: int | None = None,
        difficulty: str | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> SubmissionListResponse:
        submissions, total = await self.repo.list_submissions(
            user_id=user.id,
            problem_id=problem_id,
            status=status,
            language_id=language_id,
            difficulty=difficulty,
            search=search,
            skip=skip,
            limit=limit,
        )
        problem_cache: dict[UUID, CodingProblem | None] = {}
        items: list[SubmissionListItem] = []
        for sub in submissions:
            if sub.problem_id not in problem_cache:
                problem_cache[sub.problem_id] = await self.repo.get_problem_by_id(sub.problem_id)
            problem = problem_cache[sub.problem_id]
            items.append(
                SubmissionListItem(
                    id=sub.id,
                    problem_id=sub.problem_id,
                    problem_title=problem.title if problem else "Unknown",
                    problem_difficulty=problem.difficulty if problem else None,
                    language_name=sub.language_name,
                    language_id=sub.language_id,
                    submission_type=sub.submission_type,
                    status=sub.status,
                    passed_tests=sub.passed_tests,
                    total_tests=sub.total_tests,
                    execution_time_ms=sub.execution_time_ms,
                    memory_kb=sub.memory_kb,
                    created_at=sub.created_at,
                )
            )
        return SubmissionListResponse(items=items, total=total)

    async def get_submission(self, user: User, submission_id: UUID) -> SubmissionDetail:
        submission = await self.repo.get_submission(submission_id, load_results=True)
        if submission is None or submission.user_id != user.id:
            raise AppException("Submission not found", status_code=404)

        problem = await self.repo.get_problem_by_id(submission.problem_id, load_tests=True)
        test_cases = problem.test_cases if problem else []
        public_results = [self._public_result(r, test_cases) for r in submission.results]
        hidden = [r for r in public_results if r.is_hidden]
        hidden_passed = sum(1 for r in hidden if r.status == SubmissionStatus.ACCEPTED)
        hidden_summary = None
        if hidden:
            hidden_summary = f"Hidden tests passed: {hidden_passed} / {len(hidden)}"
        return SubmissionDetail(
            id=submission.id,
            problem_id=submission.problem_id,
            problem_title=problem.title if problem else "Unknown",
            problem_difficulty=problem.difficulty if problem else None,
            source_code=submission.source_code,
            language_id=submission.language_id,
            language_name=submission.language_name,
            created_at=submission.created_at,
            submission_id=submission.id,
            submission_type=submission.submission_type,
            status=submission.status,
            passed_tests=submission.passed_tests,
            total_tests=submission.total_tests,
            execution_time_ms=submission.execution_time_ms,
            memory_kb=submission.memory_kb,
            results=public_results,
            hidden_summary=hidden_summary,
        )

    async def get_progress_summary(self, user: User) -> CodingProgressSummary:
        problems, total = await self.repo.list_problems(limit=500)
        progress_list = await self.repo.list_user_progress(user.id)
        progress_map = {p.problem_id: p for p in progress_list}
        topic_map = await self.repo.get_topic_map()
        acceptance = await self.repo.get_acceptance_rates()
        solved = sum(1 for p in progress_list if p.status == ProblemProgressStatus.SOLVED)
        attempted = sum(
            1 for p in progress_list if p.status == ProblemProgressStatus.ATTEMPTED
        )

        def _breakdown(level: str) -> DifficultyBreakdown:
            level_problems = [p for p in problems if p.difficulty.value == level]
            level_ids = {p.id for p in level_problems}
            return DifficultyBreakdown(
                total=len(level_problems),
                solved=sum(
                    1
                    for prog in progress_list
                    if prog.problem_id in level_ids
                    and prog.status == ProblemProgressStatus.SOLVED
                ),
                attempted=sum(
                    1
                    for prog in progress_list
                    if prog.problem_id in level_ids
                    and prog.status == ProblemProgressStatus.ATTEMPTED
                ),
            )

        topic_stats: dict[str, TopicBreakdown] = {}
        for problem in problems:
            topic = topic_map.get(problem.topic_id)
            if not topic:
                continue
            entry = topic_stats.setdefault(
                topic.slug,
                TopicBreakdown(topic_slug=topic.slug, topic_name=topic.name, solved=0, total=0),
            )
            entry.total += 1
            prog = progress_map.get(problem.id)
            if prog and prog.status == ProblemProgressStatus.SOLVED:
                entry.solved += 1

        items = [
            await self._build_list_item(
                problem, progress_map=progress_map, topic_map=topic_map, acceptance=acceptance
            )
            for problem in problems
        ]
        return CodingProgressSummary(
            total_problems=total,
            solved_count=solved,
            attempted_count=attempted,
            easy=_breakdown("easy"),
            medium=_breakdown("medium"),
            hard=_breakdown("hard"),
            topics=list(topic_stats.values()),
            items=items,
        )

    async def toggle_bookmark(self, user: User, problem_id: UUID) -> dict[str, bool]:
        problem = await self.repo.get_problem_by_id(problem_id)
        if problem is None or not problem.is_active:
            raise AppException("Problem not found", status_code=404)
        bookmarked = await self.repo.toggle_problem_bookmark(user.id, problem_id)
        await self.db.commit()
        return {"bookmarked": bookmarked}

    async def list_bookmarks(self, user: User) -> list[CodingProblemListItem]:
        problems = await self.repo.list_problem_bookmarks(user.id)
        progress_list = await self.repo.list_user_progress(user.id)
        progress_map = {p.problem_id: p for p in progress_list}
        topic_map = await self.repo.get_topic_map()
        acceptance = await self.repo.get_acceptance_rates()
        return [
            await self._build_list_item(
                p,
                progress_map=progress_map,
                topic_map=topic_map,
                acceptance=acceptance,
                bookmarked=True,
            )
            for p in problems
        ]


class AdminCodingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CodingRepository(db)

    async def list_problems(
        self,
        *,
        domain_id: UUID | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> AdminCodingProblemListResponse:
        problems, total = await self.repo.list_problems(
            domain_id=domain_id, search=search, skip=skip, limit=limit, active_only=False
        )
        items = [
            CodingProblemListItem(
                id=p.id,
                slug=p.slug,
                title=p.title,
                difficulty=p.difficulty,
                domain_id=p.domain_id,
                category_id=p.category_id,
                topic_id=p.topic_id,
            )
            for p in problems
        ]
        return AdminCodingProblemListResponse(items=items, total=total)

    async def get_problem(self, problem_id: UUID) -> AdminCodingProblemDetail:
        problem = await self.repo.get_problem_by_id(problem_id, load_tests=True)
        if problem is None:
            raise AppException("Problem not found", status_code=404)
        return self._to_admin_detail(problem)

    async def create_problem(
        self, admin: User, payload: AdminCodingProblemCreate
    ) -> AdminCodingProblemDetail:
        existing = await self.repo.get_problem_by_slug(payload.slug)
        if existing:
            raise AppException("Slug already exists", status_code=400)

        problem = CodingProblem(
            slug=payload.slug,
            title=payload.title,
            description=payload.description,
            difficulty=payload.difficulty,
            domain_id=payload.domain_id,
            category_id=payload.category_id,
            topic_id=payload.topic_id,
            constraints=payload.constraints,
            input_format=payload.input_format,
            output_format=payload.output_format,
            tags=payload.tags,
            supported_language_ids=payload.supported_language_ids or list(SUPPORTED_LANGUAGES.keys()),
            time_limit_ms=payload.time_limit_ms,
            memory_limit_kb=payload.memory_limit_kb,
            starter_code=payload.starter_code,
            is_active=payload.is_active,
            is_sample=payload.is_sample,
            created_by=admin.id,
            test_cases=[CodingTestCase(**tc.model_dump()) for tc in payload.test_cases],
        )
        await self.repo.save_problem(problem)
        await self.db.commit()
        return self._to_admin_detail(problem)

    async def update_problem(
        self, problem_id: UUID, payload: AdminCodingProblemUpdate
    ) -> AdminCodingProblemDetail:
        problem = await self.repo.get_problem_by_id(problem_id, load_tests=True)
        if problem is None:
            raise AppException("Problem not found", status_code=404)

        data = payload.model_dump(exclude_unset=True)
        if "slug" in data and data["slug"] != problem.slug:
            existing = await self.repo.get_problem_by_slug(data["slug"])
            if existing:
                raise AppException("Slug already exists", status_code=400)
        for key, value in data.items():
            setattr(problem, key, value)
        await self.db.commit()
        return self._to_admin_detail(problem)

    async def delete_problem(self, problem_id: UUID) -> None:
        problem = await self.repo.get_problem_by_id(problem_id)
        if problem is None:
            raise AppException("Problem not found", status_code=404)
        await self.repo.delete_problem(problem)
        await self.db.commit()

    async def add_test_case(
        self, problem_id: UUID, payload: AdminTestCaseCreate
    ) -> AdminTestCaseDetail:
        problem = await self.repo.get_problem_by_id(problem_id)
        if problem is None:
            raise AppException("Problem not found", status_code=404)
        test_case = CodingTestCase(problem_id=problem.id, **payload.model_dump())
        await self.repo.save_test_case(test_case)
        await self.db.commit()
        return AdminTestCaseDetail(id=test_case.id, problem_id=problem.id, **payload.model_dump())

    async def update_test_case(
        self, test_case_id: UUID, payload: AdminTestCaseUpdate
    ) -> AdminTestCaseDetail:
        test_case = await self.repo.get_test_case(test_case_id)
        if test_case is None:
            raise AppException("Test case not found", status_code=404)
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(test_case, key, value)
        await self.db.commit()
        return AdminTestCaseDetail(
            id=test_case.id,
            problem_id=test_case.problem_id,
            name=test_case.name,
            input=test_case.input,
            expected_output=test_case.expected_output,
            is_hidden=test_case.is_hidden,
            is_sample=test_case.is_sample,
            sort_order=test_case.sort_order,
            explanation=test_case.explanation,
        )

    async def delete_test_case(self, test_case_id: UUID) -> None:
        test_case = await self.repo.get_test_case(test_case_id)
        if test_case is None:
            raise AppException("Test case not found", status_code=404)
        await self.repo.delete_test_case(test_case)
        await self.db.commit()

    def _to_admin_detail(self, problem: CodingProblem) -> AdminCodingProblemDetail:
        return AdminCodingProblemDetail(
            id=problem.id,
            slug=problem.slug,
            title=problem.title,
            description=problem.description,
            difficulty=problem.difficulty,
            domain_id=problem.domain_id,
            category_id=problem.category_id,
            topic_id=problem.topic_id,
            constraints=problem.constraints,
            input_format=problem.input_format,
            output_format=problem.output_format,
            tags=list(problem.tags or []),
            supported_language_ids=list(problem.supported_language_ids or []),
            time_limit_ms=problem.time_limit_ms,
            memory_limit_kb=problem.memory_limit_kb,
            starter_code={k: str(v) for k, v in (problem.starter_code or {}).items()},
            is_active=problem.is_active,
            is_sample=problem.is_sample,
            test_cases=[
                AdminTestCaseDetail(
                    id=tc.id,
                    problem_id=problem.id,
                    name=tc.name,
                    input=tc.input,
                    expected_output=tc.expected_output,
                    is_hidden=tc.is_hidden,
                    is_sample=tc.is_sample,
                    sort_order=tc.sort_order,
                    explanation=tc.explanation,
                )
                for tc in sorted(problem.test_cases, key=lambda t: t.sort_order)
            ],
        )
