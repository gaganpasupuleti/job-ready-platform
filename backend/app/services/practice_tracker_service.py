"""Aggregate existing practice records. This service does not write."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.coding import CodingProblem, CodingSubmission
from app.models.coding_enums import SubmissionType
from app.models.enums import SessionStatus
from app.models.practice import PracticeAnswer, PracticeSession
from app.models.question import Question
from app.models.sql_practice import SqlProblem, SqlSubmission
from app.models.taxonomy import Category, Topic
from app.models.user import User
from app.schemas.practice_tracker import (
    McqAccuracy,
    PracticeTrackerResponse,
    QuizAttempt,
    RecentPracticeItem,
    RecentlyPublished,
    WeakTopic,
    WeeklyActivity,
    WeekWindow,
)

WEEK_BOUNDARY = (
    "Monday 00:00:00 UTC inclusive through the next Monday 00:00:00 UTC exclusive"
)
RECENT_LIMIT = 10
WEAK_TOPIC_LIMIT = 5
NO_PUBLICATION_REASON = (
    "Topics and questions store created_at, which is the row's creation time, "
    "not a publication date. Recently published quizzes are unavailable until "
    "a real published_at exists. Never-attempted content is not treated as new."
)


def utc_week_bounds(now: datetime | None = None) -> tuple[datetime, datetime]:
    """Return the current Monday-start week in UTC."""
    moment = now or datetime.now(UTC)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    else:
        moment = moment.astimezone(UTC)
    start = (moment - timedelta(days=moment.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return start, start + timedelta(days=7)


def _percent(correct: int, graded: int) -> float | None:
    if graded <= 0:
        return None
    return round((correct / graded) * 100, 2)


class PracticeTrackerService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def snapshot(self, user: User, *, now: datetime | None = None) -> PracticeTrackerResponse:
        week_start, week_end = utc_week_bounds(now)
        weekly = await self._weekly_activity(user.id, week_start, week_end)
        attempted_questions, attempt_events = await self._mcq_attempts(user.id)
        accuracy = await self._mcq_accuracy(user.id)
        completed, in_progress = await self._session_counts(user.id)
        return PracticeTrackerResponse(
            week=WeekWindow(
                start=week_start,
                end=week_end,
                boundary=WEEK_BOUNDARY,
            ),
            weekly_activity=weekly,
            mcq_attempted_questions=attempted_questions,
            mcq_attempt_events=attempt_events,
            mcq_accuracy=accuracy,
            completed_sessions=completed,
            in_progress_sessions=in_progress,
            recent_practice=await self._recent_practice(user.id),
            weak_topics=await self._weak_topics(user.id),
            quizzes=await self._quizzes(user.id),
            recently_published=RecentlyPublished(
                available=False,
                reason=NO_PUBLICATION_REASON,
            ),
        )

    async def _weekly_activity(
        self, user_id: UUID, start: datetime, end: datetime
    ) -> WeeklyActivity:
        mcq = (
            await self.db.execute(
                select(func.count(PracticeAnswer.id))
                .join(PracticeSession, PracticeSession.id == PracticeAnswer.session_id)
                .where(
                    PracticeSession.user_id == user_id,
                    PracticeAnswer.answered_at.is_not(None),
                    PracticeAnswer.answered_at >= start,
                    PracticeAnswer.answered_at < end,
                )
            )
        ).scalar_one()
        coding = (
            await self.db.execute(
                select(func.count(CodingSubmission.id)).where(
                    CodingSubmission.user_id == user_id,
                    CodingSubmission.submission_type == SubmissionType.SUBMIT,
                    CodingSubmission.created_at >= start,
                    CodingSubmission.created_at < end,
                )
            )
        ).scalar_one()
        sql = (
            await self.db.execute(
                select(func.count(SqlSubmission.id)).where(
                    SqlSubmission.user_id == user_id,
                    SqlSubmission.submitted_at >= start,
                    SqlSubmission.submitted_at < end,
                )
            )
        ).scalar_one()
        mcq_count = int(mcq or 0)
        coding_count = int(coding or 0)
        sql_count = int(sql or 0)
        return WeeklyActivity(
            mcq_finalized_answers=mcq_count,
            coding_submits=coding_count,
            sql_submits=sql_count,
            total=mcq_count + coding_count + sql_count,
        )

    async def _mcq_attempts(self, user_id: UUID) -> tuple[int, int]:
        """Distinct questions and answer rows that were finalized.

        Autosave without answered_at, and opening a question, are excluded.
        """
        owned = (
            select(PracticeAnswer.question_id, PracticeAnswer.id)
            .join(PracticeSession, PracticeSession.id == PracticeAnswer.session_id)
            .where(
                PracticeSession.user_id == user_id,
                PracticeAnswer.answered_at.is_not(None),
            )
        ).subquery()
        row = (
            await self.db.execute(
                select(
                    func.count(func.distinct(owned.c.question_id)),
                    func.count(owned.c.id),
                )
            )
        ).one()
        return int(row[0] or 0), int(row[1] or 0)

    async def _mcq_accuracy(self, user_id: UUID) -> McqAccuracy:
        """Accuracy uses graded answers on completed sessions only.

        Unanswered questions are excluded. Coding and SQL results are excluded.
        An active session, even with a saved selection, does not count.
        """
        correct_expr = func.coalesce(
            func.sum(case((PracticeAnswer.is_correct.is_(True), 1), else_=0)),
            0,
        )
        incorrect_expr = func.coalesce(
            func.sum(case((PracticeAnswer.is_correct.is_(False), 1), else_=0)),
            0,
        )
        row = (
            await self.db.execute(
                select(correct_expr, incorrect_expr)
                .select_from(PracticeAnswer)
                .join(PracticeSession, PracticeSession.id == PracticeAnswer.session_id)
                .where(
                    PracticeSession.user_id == user_id,
                    PracticeSession.status == SessionStatus.COMPLETED,
                    PracticeAnswer.answered_at.is_not(None),
                    PracticeAnswer.is_correct.is_not(None),
                )
            )
        ).one()
        correct = int(row[0] or 0)
        incorrect = int(row[1] or 0)
        graded = correct + incorrect
        return McqAccuracy(
            graded_answers=graded,
            correct_answers=correct,
            accuracy_percent=_percent(correct, graded),
        )

    async def _session_counts(self, user_id: UUID) -> tuple[int, int]:
        rows = (
            await self.db.execute(
                select(PracticeSession.status, func.count(PracticeSession.id))
                .where(PracticeSession.user_id == user_id)
                .group_by(PracticeSession.status)
            )
        ).all()
        completed = 0
        in_progress = 0
        for status, count in rows:
            if status == SessionStatus.COMPLETED:
                completed = int(count)
            elif status == SessionStatus.ACTIVE:
                in_progress = int(count)
        return completed, in_progress

    async def _recent_practice(self, user_id: UUID) -> list[RecentPracticeItem]:
        items: list[RecentPracticeItem] = []
        sessions = (
            await self.db.execute(
                select(PracticeSession, Topic.name)
                .outerjoin(Topic, Topic.id == PracticeSession.topic_id)
                .where(PracticeSession.user_id == user_id)
                .order_by(
                    func.coalesce(
                        PracticeSession.completed_at, PracticeSession.started_at
                    ).desc()
                )
                .limit(RECENT_LIMIT)
            )
        ).all()
        for session, topic_name in sessions:
            occurred = session.completed_at or session.started_at
            items.append(
                RecentPracticeItem(
                    kind="mcq_session",
                    source_id=session.id,
                    title=topic_name or "Practice session",
                    status=session.status.value,
                    occurred_at=occurred,
                )
            )

        coding_rows = (
            await self.db.execute(
                select(CodingSubmission, CodingProblem.title)
                .join(CodingProblem, CodingProblem.id == CodingSubmission.problem_id)
                .where(
                    CodingSubmission.user_id == user_id,
                    CodingSubmission.submission_type == SubmissionType.SUBMIT,
                )
                .order_by(CodingSubmission.created_at.desc())
                .limit(RECENT_LIMIT)
            )
        ).all()
        for submission, title in coding_rows:
            items.append(
                RecentPracticeItem(
                    kind="coding_submit",
                    source_id=submission.id,
                    title=title,
                    status=submission.status.value,
                    occurred_at=submission.created_at,
                )
            )

        sql_rows = (
            await self.db.execute(
                select(SqlSubmission, SqlProblem.title)
                .join(SqlProblem, SqlProblem.id == SqlSubmission.problem_id)
                .where(SqlSubmission.user_id == user_id)
                .order_by(SqlSubmission.submitted_at.desc())
                .limit(RECENT_LIMIT)
            )
        ).all()
        for submission, title in sql_rows:
            items.append(
                RecentPracticeItem(
                    kind="sql_submit",
                    source_id=submission.id,
                    title=title,
                    status=submission.status.value,
                    occurred_at=submission.submitted_at,
                )
            )

        items.sort(key=lambda item: item.occurred_at, reverse=True)
        return items[:RECENT_LIMIT]

    async def _weak_topics(self, user_id: UUID) -> list[WeakTopic]:
        correct_expr = func.sum(case((PracticeAnswer.is_correct.is_(True), 1), else_=0))
        incorrect_expr = func.sum(case((PracticeAnswer.is_correct.is_(False), 1), else_=0))
        rows = (
            await self.db.execute(
                select(
                    Topic.id,
                    Topic.name,
                    Topic.slug,
                    func.coalesce(correct_expr, 0),
                    func.coalesce(incorrect_expr, 0),
                )
                .select_from(PracticeAnswer)
                .join(PracticeSession, PracticeSession.id == PracticeAnswer.session_id)
                .join(Question, Question.id == PracticeAnswer.question_id)
                .join(Topic, Topic.id == Question.topic_id)
                .where(
                    PracticeSession.user_id == user_id,
                    PracticeSession.status == SessionStatus.COMPLETED,
                    PracticeAnswer.answered_at.is_not(None),
                    PracticeAnswer.is_correct.is_not(None),
                )
                .group_by(Topic.id, Topic.name, Topic.slug)
                .having(func.coalesce(incorrect_expr, 0) > 0)
                .order_by(incorrect_expr.desc(), correct_expr.asc())
                .limit(WEAK_TOPIC_LIMIT)
            )
        ).all()
        topics: list[WeakTopic] = []
        for topic_id, name, slug, correct, incorrect in rows:
            correct_count = int(correct or 0)
            incorrect_count = int(incorrect or 0)
            graded = correct_count + incorrect_count
            topics.append(
                WeakTopic(
                    topic_id=topic_id,
                    topic_name=name,
                    topic_slug=slug,
                    graded_answers=graded,
                    correct_answers=correct_count,
                    incorrect_answers=incorrect_count,
                    accuracy_percent=_percent(correct_count, graded) or 0.0,
                )
            )
        return topics

    async def _quizzes(self, user_id: UUID) -> list[QuizAttempt]:
        topic_rows = (
            await self.db.execute(
                select(
                    Topic.id,
                    Topic.name,
                    Topic.slug,
                    Category.id,
                    Category.name,
                    func.count(Question.id),
                )
                .join(Category, Category.id == Topic.category_id)
                .join(Question, Question.topic_id == Topic.id)
                .where(
                    Topic.is_active.is_(True),
                    Category.is_active.is_(True),
                    Question.is_active.is_(True),
                )
                .group_by(Topic.id, Topic.name, Topic.slug, Category.id, Category.name)
                .order_by(Category.name, Topic.name)
            )
        ).all()
        status_rows = (
            await self.db.execute(
                select(PracticeSession.topic_id, PracticeSession.status, func.count())
                .where(
                    PracticeSession.user_id == user_id,
                    PracticeSession.topic_id.is_not(None),
                )
                .group_by(PracticeSession.topic_id, PracticeSession.status)
            )
        ).all()
        by_topic: dict[UUID, dict[str, int]] = {}
        for topic_id, status, count in status_rows:
            bucket = by_topic.setdefault(topic_id, {"active": 0, "completed": 0})
            if status == SessionStatus.ACTIVE:
                bucket["active"] = int(count)
            elif status == SessionStatus.COMPLETED:
                bucket["completed"] = int(count)
        quizzes: list[QuizAttempt] = []
        for topic_id, topic_name, slug, category_id, category_name, question_count in topic_rows:
            counts = by_topic.get(topic_id, {"active": 0, "completed": 0})
            if counts["active"] > 0:
                attempt_status = "in_progress"
            elif counts["completed"] > 0:
                attempt_status = "completed"
            else:
                attempt_status = "not_started"
            quizzes.append(
                QuizAttempt(
                    topic_id=topic_id,
                    topic_name=topic_name,
                    topic_slug=slug,
                    category_id=category_id,
                    category_name=category_name,
                    active_question_count=int(question_count),
                    attempt_status=attempt_status,
                )
            )
        return quizzes
