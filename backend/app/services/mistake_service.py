"""Global mistake book — aggregate incorrect practice across engines."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.coding import CodingProblem, CodingSubmission
from app.models.coding_enums import SubmissionStatus
from app.models.enums import SessionStatus
from app.models.interview import InterviewQuestion
from app.models.interview_session import InterviewQuestionReview, InterviewSession, InterviewSessionQuestion
from app.models.practice import PracticeAnswer, PracticeSession
from app.models.prompt import PromptChallenge, PromptSubmission
from app.models.question import Question, QuestionOption
from app.models.readiness import MistakeItem
from app.models.readiness_enums import MistakeSourceType, MistakeStatus
from app.models.scenario import ScenarioChallenge, ScenarioSubmission
from app.models.sql_practice import SqlProblem, SqlSubmission
from app.models.sql_enums import SqlSubmissionStatus
from app.models.tagging import QuestionSkill, Skill
from app.models.user import User


class MistakeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upsert(
        self,
        *,
        user_id: UUID,
        source_type: MistakeSourceType,
        source_id: UUID,
        title: str,
        summary: str | None = None,
        skill_id: UUID | None = None,
        topic_id: UUID | None = None,
        mistake_type: str = "incorrect",
        context: dict[str, Any] | None = None,
        retry_href: str | None = None,
    ) -> MistakeItem:
        now = datetime.now(UTC)
        existing = (
            await self.db.execute(
                select(MistakeItem).where(
                    MistakeItem.user_id == user_id,
                    MistakeItem.source_type == source_type,
                    MistakeItem.source_id == source_id,
                )
            )
        ).scalar_one_or_none()
        if existing:
            existing.occurrence_count += 1
            existing.last_seen_at = now
            existing.summary = summary or existing.summary
            existing.latest_context_json = context or existing.latest_context_json
            existing.retry_href = retry_href or existing.retry_href
            if existing.status == MistakeStatus.RESOLVED:
                existing.status = MistakeStatus.OPEN
            await self.db.commit()
            await self.db.refresh(existing)
            return existing

        item = MistakeItem(
            user_id=user_id,
            source_type=source_type,
            source_id=source_id,
            skill_id=skill_id,
            topic_id=topic_id,
            title=title,
            summary=summary,
            mistake_type=mistake_type,
            first_seen_at=now,
            last_seen_at=now,
            occurrence_count=1,
            status=MistakeStatus.OPEN,
            latest_context_json=context,
            retry_href=retry_href,
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def list_mistakes(
        self,
        user: User,
        *,
        source_type: str | None = None,
        status: str | None = None,
        view: str = "recent",
    ) -> list[dict[str, Any]]:
        stmt = select(MistakeItem).where(MistakeItem.user_id == user.id)
        if source_type:
            stmt = stmt.where(MistakeItem.source_type == source_type)
        if status:
            stmt = stmt.where(MistakeItem.status == status)
        if view == "repeated":
            stmt = stmt.where(MistakeItem.occurrence_count >= 2)
        elif view == "resolved":
            stmt = stmt.where(MistakeItem.status == MistakeStatus.RESOLVED)
        elif view == "unresolved":
            stmt = stmt.where(MistakeItem.status != MistakeStatus.RESOLVED)
        stmt = stmt.order_by(MistakeItem.last_seen_at.desc())
        rows = (await self.db.execute(stmt)).scalars().all()
        return [self._to_dict(r) for r in rows]

    async def summary(self, user: User) -> dict[str, Any]:
        rows = (
            await self.db.execute(
                select(
                    MistakeItem.status,
                    func.count(MistakeItem.id),
                    func.sum(MistakeItem.occurrence_count),
                )
                .where(MistakeItem.user_id == user.id)
                .group_by(MistakeItem.status)
            )
        ).all()
        open_count = 0
        resolved = 0
        for st, count, _ in rows:
            if st == MistakeStatus.RESOLVED:
                resolved = int(count)
            else:
                open_count += int(count)
        repeated = (
            await self.db.execute(
                select(func.count(MistakeItem.id)).where(
                    MistakeItem.user_id == user.id,
                    MistakeItem.occurrence_count >= 2,
                    MistakeItem.status != MistakeStatus.RESOLVED,
                )
            )
        ).scalar() or 0
        top_topics = (
            await self.db.execute(
                select(MistakeItem.title, func.sum(MistakeItem.occurrence_count))
                .where(MistakeItem.user_id == user.id, MistakeItem.status != MistakeStatus.RESOLVED)
                .group_by(MistakeItem.title)
                .order_by(func.sum(MistakeItem.occurrence_count).desc())
                .limit(5)
            )
        ).all()
        return {
            "open_count": open_count,
            "repeated_count": int(repeated),
            "resolved_count": resolved,
            "top_weak_topics": [{"title": t, "count": int(c)} for t, c in top_topics],
        }

    async def mark_reviewed(self, user: User, mistake_id: UUID) -> dict:
        item = await self._owned(user.id, mistake_id)
        item.status = MistakeStatus.REVIEWED
        await self.db.commit()
        return self._to_dict(item)

    async def resolve(self, user: User, mistake_id: UUID) -> dict:
        item = await self._owned(user.id, mistake_id)
        item.status = MistakeStatus.RESOLVED
        await self.db.commit()
        return self._to_dict(item)

    async def _owned(self, user_id: UUID, mistake_id: UUID) -> MistakeItem:
        item = await self.db.get(MistakeItem, mistake_id)
        if item is None or item.user_id != user_id:
            from app.core.exceptions import AppException  # noqa: PLC0415

            raise AppException("Mistake not found", status_code=404)
        return item

    def _to_dict(self, item: MistakeItem) -> dict[str, Any]:
        return {
            "id": str(item.id),
            "source_type": item.source_type.value if hasattr(item.source_type, "value") else str(item.source_type),
            "source_id": str(item.source_id),
            "title": item.title,
            "summary": item.summary,
            "mistake_type": item.mistake_type,
            "occurrence_count": item.occurrence_count,
            "status": item.status.value if hasattr(item.status, "value") else str(item.status),
            "first_seen_at": item.first_seen_at.isoformat(),
            "last_seen_at": item.last_seen_at.isoformat(),
            "retry_href": item.retry_href,
            "context": item.latest_context_json,
        }

    async def backfill_user(self, user_id: UUID) -> int:
        count = 0
        count += await self._backfill_mcq(user_id)
        count += await self._backfill_sql(user_id)
        count += await self._backfill_interview(user_id)
        count += await self._backfill_prompt(user_id)
        return count

    async def _backfill_mcq(self, user_id: UUID) -> int:
        rows = (
            await self.db.execute(
                select(PracticeAnswer, Question, PracticeSession)
                .join(Question, Question.id == PracticeAnswer.question_id)
                .join(PracticeSession, PracticeSession.id == PracticeAnswer.session_id)
                .where(
                    PracticeSession.user_id == user_id,
                    PracticeSession.status == SessionStatus.COMPLETED,
                    PracticeAnswer.is_correct.is_(False),
                )
            )
        ).all()
        n = 0
        for answer, question, session in rows:
            skill = (
                await self.db.execute(
                    select(Skill)
                    .join(QuestionSkill, QuestionSkill.skill_id == Skill.id)
                    .where(QuestionSkill.question_id == question.id)
                    .limit(1)
                )
            ).scalar_one_or_none()
            correct_opts = (
                await self.db.execute(
                    select(QuestionOption).where(
                        QuestionOption.question_id == question.id, QuestionOption.is_correct.is_(True)
                    )
                )
            ).scalars().all()
            await self.upsert(
                user_id=user_id,
                source_type=MistakeSourceType.MCQ,
                source_id=question.id,
                title=question.title or question.question_text[:80],
                skill_id=skill.id if skill else None,
                topic_id=question.topic_id,
                context={
                    "session_id": str(session.id),
                    "selected_option_ids": answer.selected_option_ids,
                    "correct_option_ids": [str(o.id) for o in correct_opts],
                    "explanation": question.explanation,
                },
                retry_href=f"/practice/history/{session.id}",
            )
            n += 1
        return n

    async def _backfill_sql(self, user_id: UUID) -> int:
        rows = (
            await self.db.execute(
                select(SqlSubmission, SqlProblem)
                .join(SqlProblem, SqlProblem.id == SqlSubmission.problem_id)
                .where(
                    SqlSubmission.user_id == user_id,
                    SqlSubmission.status == SqlSubmissionStatus.WRONG_ANSWER,
                )
            )
        ).all()
        n = 0
        for sub, problem in rows:
            await self.upsert(
                user_id=user_id,
                source_type=MistakeSourceType.SQL,
                source_id=problem.id,
                title=problem.title,
                topic_id=problem.topic_id,
                context={"attempt_count": 1},
                retry_href=f"/practice/sql/{problem.slug}",
            )
            n += 1
        return n

    async def _backfill_interview(self, user_id: UUID) -> int:
        rows = (
            await self.db.execute(
                select(InterviewQuestionReview, InterviewQuestion)
                .join(InterviewQuestion, InterviewQuestion.id == InterviewQuestionReview.question_id)
                .where(
                    InterviewQuestionReview.user_id == user_id,
                    InterviewQuestionReview.needs_review.is_(True),
                )
            )
        ).all()
        n = 0
        for review, question in rows:
            await self.upsert(
                user_id=user_id,
                source_type=MistakeSourceType.INTERVIEW,
                source_id=question.id,
                title=(question.question_text or "Interview question")[:500],
                mistake_type="needs_review",
                context={"key_point_coverage": review.key_point_coverage},
                retry_href=f"/interviews/review?question={question.id}",
            )
            n += 1
        return n

    async def _backfill_prompt(self, user_id: UUID) -> int:
        rows = (
            await self.db.execute(
                select(PromptSubmission, PromptChallenge)
                .join(PromptChallenge, PromptChallenge.id == PromptSubmission.challenge_id)
                .where(PromptSubmission.user_id == user_id, PromptSubmission.overall_score < 60)
            )
        ).all()
        n = 0
        for sub, challenge in rows:
            await self.upsert(
                user_id=user_id,
                source_type=MistakeSourceType.PROMPT,
                source_id=challenge.id,
                title=challenge.title,
                context={"score": sub.overall_score, "failed_categories": list(sub.rubric_breakdown.keys())},
                retry_href=f"/ai/prompts/{challenge.slug}",
            )
            n += 1
        return n
