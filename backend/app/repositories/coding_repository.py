from uuid import UUID

from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.coding import (
    CodingProblem,
    CodingProblemProgress,
    CodingSubmission,
    CodingTestCase,
)
from app.models.coding_enums import ProblemProgressStatus, SubmissionStatus
from app.models.practice import Bookmark
from app.models.taxonomy import Topic


class CodingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_problems(
        self,
        *,
        domain_id: UUID | None = None,
        topic_id: UUID | None = None,
        topic_slug: str | None = None,
        difficulty: str | None = None,
        search: str | None = None,
        tag: str | None = None,
        language_id: int | None = None,
        progress_status: str | None = None,
        user_id: UUID | None = None,
        skip: int = 0,
        limit: int = 50,
        active_only: bool = True,
    ) -> tuple[list[CodingProblem], int]:
        query = select(CodingProblem)
        count_query = select(func.count()).select_from(CodingProblem)

        if active_only:
            query = query.where(CodingProblem.is_active.is_(True))
            count_query = count_query.where(CodingProblem.is_active.is_(True))
        if domain_id:
            query = query.where(CodingProblem.domain_id == domain_id)
            count_query = count_query.where(CodingProblem.domain_id == domain_id)
        if topic_id:
            query = query.where(CodingProblem.topic_id == topic_id)
            count_query = count_query.where(CodingProblem.topic_id == topic_id)
        if topic_slug:
            query = query.join(Topic, CodingProblem.topic_id == Topic.id).where(
                Topic.slug == topic_slug
            )
            count_query = count_query.join(Topic, CodingProblem.topic_id == Topic.id).where(
                Topic.slug == topic_slug
            )
        if difficulty:
            query = query.where(CodingProblem.difficulty == difficulty)
            count_query = count_query.where(CodingProblem.difficulty == difficulty)
        if search:
            pattern = f"%{search}%"
            query = query.where(
                or_(CodingProblem.title.ilike(pattern), CodingProblem.slug.ilike(pattern))
            )
            count_query = count_query.where(
                or_(CodingProblem.title.ilike(pattern), CodingProblem.slug.ilike(pattern))
            )
        if tag:
            query = query.where(CodingProblem.tags.contains([tag]))
            count_query = count_query.where(CodingProblem.tags.contains([tag]))
        if language_id is not None:
            query = query.where(CodingProblem.supported_language_ids.contains([language_id]))
            count_query = count_query.where(
                CodingProblem.supported_language_ids.contains([language_id])
            )
        if progress_status and user_id:
            query = query.join(
                CodingProblemProgress,
                (CodingProblemProgress.problem_id == CodingProblem.id)
                & (CodingProblemProgress.user_id == user_id),
            ).where(CodingProblemProgress.status == progress_status)
            count_query = count_query.join(
                CodingProblemProgress,
                (CodingProblemProgress.problem_id == CodingProblem.id)
                & (CodingProblemProgress.user_id == user_id),
            ).where(CodingProblemProgress.status == progress_status)
        elif progress_status == "unsolved" and user_id:
            solved_or_attempted = select(CodingProblemProgress.problem_id).where(
                CodingProblemProgress.user_id == user_id
            )
            query = query.where(CodingProblem.id.not_in(solved_or_attempted))
            count_query = count_query.where(CodingProblem.id.not_in(solved_or_attempted))

        total = (await self.db.execute(count_query)).scalar_one()
        result = await self.db.execute(
            query.order_by(CodingProblem.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_topic_map(self) -> dict[UUID, Topic]:
        result = await self.db.execute(select(Topic))
        return {t.id: t for t in result.scalars().all()}

    async def get_acceptance_rates(self) -> dict[UUID, float]:
        stmt = (
            select(
                CodingSubmission.problem_id,
                func.count().label("total"),
                func.sum(
                    case((CodingSubmission.status == SubmissionStatus.ACCEPTED, 1), else_=0)
                ).label("accepted"),
            )
            .where(CodingSubmission.submission_type == "submit")
            .group_by(CodingSubmission.problem_id)
        )
        result = await self.db.execute(stmt)
        rates: dict[UUID, float] = {}
        for row in result.all():
            if row.total:
                rates[row.problem_id] = row.accepted / row.total
        return rates

    async def get_problem_by_id(
        self, problem_id: UUID, *, load_tests: bool = False
    ) -> CodingProblem | None:
        query = select(CodingProblem).where(CodingProblem.id == problem_id)
        if load_tests:
            query = query.options(selectinload(CodingProblem.test_cases))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_problem_by_slug(
        self, slug: str, *, load_tests: bool = False
    ) -> CodingProblem | None:
        query = select(CodingProblem).where(CodingProblem.slug == slug)
        if load_tests:
            query = query.options(selectinload(CodingProblem.test_cases))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_progress(
        self, user_id: UUID, problem_id: UUID
    ) -> CodingProblemProgress | None:
        result = await self.db.execute(
            select(CodingProblemProgress).where(
                CodingProblemProgress.user_id == user_id,
                CodingProblemProgress.problem_id == problem_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_user_progress(self, user_id: UUID) -> list[CodingProblemProgress]:
        result = await self.db.execute(
            select(CodingProblemProgress).where(CodingProblemProgress.user_id == user_id)
        )
        return list(result.scalars().all())

    async def save_progress(self, progress: CodingProblemProgress) -> CodingProblemProgress:
        self.db.add(progress)
        await self.db.flush()
        return progress

    async def save_submission(self, submission: CodingSubmission) -> CodingSubmission:
        self.db.add(submission)
        await self.db.flush()
        return submission

    async def get_submission(
        self, submission_id: UUID, *, load_results: bool = False
    ) -> CodingSubmission | None:
        query = select(CodingSubmission).where(CodingSubmission.id == submission_id)
        if load_results:
            query = query.options(selectinload(CodingSubmission.results))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_submissions(
        self,
        *,
        user_id: UUID,
        problem_id: UUID | None = None,
        status: str | None = None,
        language_id: int | None = None,
        difficulty: str | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[CodingSubmission], int]:
        query = select(CodingSubmission).where(CodingSubmission.user_id == user_id)
        count_query = select(func.count()).select_from(CodingSubmission).where(
            CodingSubmission.user_id == user_id
        )
        if problem_id:
            query = query.where(CodingSubmission.problem_id == problem_id)
            count_query = count_query.where(CodingSubmission.problem_id == problem_id)
        if status:
            query = query.where(CodingSubmission.status == status)
            count_query = count_query.where(CodingSubmission.status == status)
        if language_id is not None:
            query = query.where(CodingSubmission.language_id == language_id)
            count_query = count_query.where(CodingSubmission.language_id == language_id)
        if difficulty or search:
            query = query.join(CodingProblem, CodingSubmission.problem_id == CodingProblem.id)
            count_query = count_query.join(
                CodingProblem, CodingSubmission.problem_id == CodingProblem.id
            )
            if difficulty:
                query = query.where(CodingProblem.difficulty == difficulty)
                count_query = count_query.where(CodingProblem.difficulty == difficulty)
            if search:
                pattern = f"%{search}%"
                query = query.where(CodingProblem.title.ilike(pattern))
                count_query = count_query.where(CodingProblem.title.ilike(pattern))

        total = (await self.db.execute(count_query)).scalar_one()
        result = await self.db.execute(
            query.order_by(CodingSubmission.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total

    async def is_problem_bookmarked(self, user_id: UUID, problem_id: UUID) -> bool:
        result = await self.db.execute(
            select(Bookmark.id).where(
                Bookmark.user_id == user_id, Bookmark.problem_id == problem_id
            )
        )
        return result.scalar_one_or_none() is not None

    async def toggle_problem_bookmark(self, user_id: UUID, problem_id: UUID) -> bool:
        result = await self.db.execute(
            select(Bookmark).where(
                Bookmark.user_id == user_id, Bookmark.problem_id == problem_id
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            await self.db.delete(existing)
            await self.db.flush()
            return False
        self.db.add(Bookmark(user_id=user_id, problem_id=problem_id))
        await self.db.flush()
        return True

    async def list_problem_bookmarks(self, user_id: UUID) -> list[CodingProblem]:
        stmt = (
            select(CodingProblem)
            .join(Bookmark, Bookmark.problem_id == CodingProblem.id)
            .where(Bookmark.user_id == user_id, CodingProblem.is_active.is_(True))
            .order_by(Bookmark.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def save_problem(self, problem: CodingProblem) -> CodingProblem:
        self.db.add(problem)
        await self.db.flush()
        return problem

    async def delete_problem(self, problem: CodingProblem) -> None:
        await self.db.delete(problem)

    async def get_test_case(self, test_case_id: UUID) -> CodingTestCase | None:
        result = await self.db.execute(
            select(CodingTestCase).where(CodingTestCase.id == test_case_id)
        )
        return result.scalar_one_or_none()

    async def save_test_case(self, test_case: CodingTestCase) -> CodingTestCase:
        self.db.add(test_case)
        await self.db.flush()
        return test_case

    async def delete_test_case(self, test_case: CodingTestCase) -> None:
        await self.db.delete(test_case)

    async def count_solved(self, user_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(CodingProblemProgress)
            .where(
                CodingProblemProgress.user_id == user_id,
                CodingProblemProgress.status == ProblemProgressStatus.SOLVED,
            )
        )
        return result.scalar_one()
