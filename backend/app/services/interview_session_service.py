# ruff: noqa: E501
"""Student interview session engine — no LLM, self-review only."""

from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppException
from app.models.interview import (
    InterviewAnswerPoint,
    InterviewPack,
    InterviewPackQuestion,
    InterviewQuestion,
    InterviewQuestionCompany,
    InterviewQuestionRole,
    InterviewQuestionSkill,
)
from app.models.interview_enums import (
    ContentReviewStatus,
    InterviewConfidence,
    InterviewSelfRating,
    InterviewSessionMode,
    InterviewSessionQuestionStatus,
    InterviewSessionSource,
    InterviewSessionStatus,
)
from app.models.interview_session import (
    InterviewQuestionNote,
    InterviewQuestionReview,
    InterviewSession,
    InterviewSessionQuestion,
)
from app.models.tagging import Company, JobRole, Skill
from app.models.user import User
from app.schemas.interview import InterviewAnswerPointPublic, InterviewPackPublic
from app.schemas.interview_session import (
    InterviewHubResponse,
    InterviewNavigatorItem,
    InterviewNeedsReviewItem,
    InterviewNotesPayload,
    InterviewProgressResponse,
    InterviewReviewPayload,
    InterviewSessionCreate,
    InterviewSessionDetail,
    InterviewSessionQuestionPublic,
    InterviewSessionResults,
    InterviewSessionSummary,
    InterviewSkillBreakdown,
    InterviewTypeBreakdown,
    InterviewPackDetail,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:160]


class InterviewSessionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _live_q(self):
        return (
            InterviewQuestion.review_status == ContentReviewStatus.APPROVED,
            InterviewQuestion.is_active.is_(True),
        )

    async def _question_tags(self, question_ids: list[UUID]) -> dict[UUID, dict[str, list[str]]]:
        if not question_ids:
            return {}
        out: dict[UUID, dict[str, list[str]]] = {
            qid: {"skills": [], "roles": [], "companies": []} for qid in question_ids
        }
        skill_rows = await self.db.execute(
            select(InterviewQuestionSkill.question_id, Skill.name)
            .join(Skill, Skill.id == InterviewQuestionSkill.skill_id)
            .where(InterviewQuestionSkill.question_id.in_(question_ids))
        )
        for qid, name in skill_rows.all():
            out[qid]["skills"].append(name)
        role_rows = await self.db.execute(
            select(InterviewQuestionRole.question_id, JobRole.name)
            .join(JobRole, JobRole.id == InterviewQuestionRole.role_id)
            .where(InterviewQuestionRole.question_id.in_(question_ids))
        )
        for qid, name in role_rows.all():
            out[qid]["roles"].append(name)
        company_rows = await self.db.execute(
            select(InterviewQuestionCompany.question_id, Company.name)
            .join(Company, Company.id == InterviewQuestionCompany.company_id)
            .where(InterviewQuestionCompany.question_id.in_(question_ids))
        )
        for qid, name in company_rows.all():
            out[qid]["companies"].append(name)
        return out

    async def _pack_slug(self, pack_id: UUID | None) -> str | None:
        if not pack_id:
            return None
        pack = await self.db.get(InterviewPack, pack_id)
        return pack.slug if pack else None

    async def _summary(self, session: InterviewSession) -> InterviewSessionSummary:
        rows = (
            await self.db.execute(
                select(InterviewSessionQuestion).where(InterviewSessionQuestion.session_id == session.id)
            )
        ).scalars().all()
        reviewed = [
            r
            for r in rows
            if r.status
            in {
                InterviewSessionQuestionStatus.REVIEWED,
                InterviewSessionQuestionStatus.COMPLETED,
            }
            or r.self_rating is not None
        ]
        coverages: list[float] = []
        for r in reviewed:
            checked = r.key_points_checked_json or []
            points = (
                await self.db.execute(
                    select(func.count()).select_from(InterviewAnswerPoint).where(
                        InterviewAnswerPoint.question_id == r.question_id
                    )
                )
            ).scalar_one()
            if points:
                coverages.append(len(checked) / points)
        return InterviewSessionSummary(
            id=session.id,
            title=session.title,
            mode=session.mode,
            source_type=session.source_type,
            pack_id=session.pack_id,
            pack_slug=await self._pack_slug(session.pack_id),
            question_count=session.question_count,
            current_question_index=session.current_question_index,
            status=session.status,
            started_at=session.started_at,
            completed_at=session.completed_at,
            reviewed_count=len(reviewed),
            needs_review_count=sum(1 for r in rows if r.needs_review),
            key_point_coverage_avg=(sum(coverages) / len(coverages) * 100) if coverages else None,
        )

    async def _get_owned_session(self, user: User, session_id: UUID) -> InterviewSession:
        session = await self.db.get(InterviewSession, session_id)
        if session is None or session.user_id != user.id:
            raise AppException("Session not found", status_code=404)
        return session

    async def _session_row(
        self, session_id: UUID, number: int
    ) -> tuple[InterviewSessionQuestion, InterviewQuestion]:
        row = (
            await self.db.execute(
                select(InterviewSessionQuestion)
                .where(
                    InterviewSessionQuestion.session_id == session_id,
                    InterviewSessionQuestion.sort_order == number - 1,
                )
            )
        ).scalar_one_or_none()
        if row is None:
            raise AppException("Question not found in session", status_code=404)
        question = await self.db.get(InterviewQuestion, row.question_id)
        if question is None:
            raise AppException("Question not found", status_code=404)
        return row, question

    async def _note(
        self, user_id: UUID, question_id: UUID, session_id: UUID
    ) -> InterviewQuestionNote | None:
        return (
            await self.db.execute(
                select(InterviewQuestionNote).where(
                    InterviewQuestionNote.user_id == user_id,
                    InterviewQuestionNote.question_id == question_id,
                    InterviewQuestionNote.session_id == session_id,
                )
            )
        ).scalar_one_or_none()

    async def _public_question(
        self,
        *,
        user: User,
        session: InterviewSession,
        row: InterviewSessionQuestion,
        question: InterviewQuestion,
        number: int,
        include_answer: bool,
    ) -> InterviewSessionQuestionPublic:
        tags = await self._question_tags([question.id])
        t = tags.get(question.id, {"skills": [], "roles": [], "companies": []})
        note = await self._note(user.id, question.id, session.id)
        revealed = row.answer_revealed_at is not None or include_answer
        # Mock/rapid: never leak until reveal (except study mode always can)
        if session.mode == InterviewSessionMode.STUDY:
            revealed = True
        key_points: list[InterviewAnswerPointPublic] = []
        expected = None
        explanation = None
        if revealed:
            points = (
                await self.db.execute(
                    select(InterviewAnswerPoint)
                    .where(InterviewAnswerPoint.question_id == question.id)
                    .order_by(InterviewAnswerPoint.sort_order)
                )
            ).scalars().all()
            key_points = [
                InterviewAnswerPointPublic(id=p.id, point_text=p.point_text, sort_order=p.sort_order)
                for p in points
            ]
            expected = question.expected_answer
            explanation = question.explanation
        checked = [UUID(str(x)) for x in (row.key_points_checked_json or [])]
        coverage = None
        if revealed and key_points:
            coverage = len(checked) / len(key_points) * 100
        return InterviewSessionQuestionPublic(
            number=number,
            question_id=question.id,
            slug=question.slug,
            question_text=question.question_text,
            question_type=question.question_type,
            difficulty=question.difficulty,
            experience_level=question.experience_level,
            skills=t["skills"],
            roles=t["roles"],
            companies=t["companies"],
            status=row.status,
            answer_revealed=revealed and row.answer_revealed_at is not None
            if session.mode != InterviewSessionMode.STUDY
            else True,
            expected_answer=expected,
            explanation=explanation,
            key_points=key_points,
            answer_text=note.answer_text if note else None,
            private_notes=note.private_notes if note else None,
            self_rating=row.self_rating,
            confidence_level=row.confidence_level,
            key_points_checked=checked,
            needs_review=row.needs_review,
            time_spent_seconds=row.time_spent_seconds,
            key_point_coverage=coverage,
        )

    async def _select_questions(self, payload: InterviewSessionCreate) -> list[InterviewQuestion]:
        if payload.source_type == InterviewSessionSource.PACK or payload.pack_id or payload.pack_slug:
            pack = None
            if payload.pack_id:
                pack = await self.db.get(InterviewPack, payload.pack_id)
            elif payload.pack_slug:
                pack = (
                    await self.db.execute(
                        select(InterviewPack).where(InterviewPack.slug == payload.pack_slug)
                    )
                ).scalar_one_or_none()
            if pack is None or not pack.is_active:
                raise AppException("Interview pack not found", status_code=404)
            items = (
                await self.db.execute(
                    select(InterviewPackQuestion, InterviewQuestion)
                    .join(InterviewQuestion, InterviewQuestion.id == InterviewPackQuestion.question_id)
                    .where(
                        InterviewPackQuestion.pack_id == pack.id,
                        *self._live_q(),
                    )
                    .order_by(InterviewPackQuestion.sort_order)
                )
            ).all()
            questions = [q for _, q in items]
            if len(questions) < 1:
                raise AppException("Pack has no approved active questions", status_code=400)
            return questions

        if payload.source_type == InterviewSessionSource.RETRY_REVIEW or (
            payload.question_ids is not None and payload.source_type != InterviewSessionSource.PACK
        ):
            ids = list(payload.question_ids or [])
            if not ids:
                raise AppException("No review questions available", status_code=400)
            rows = (
                await self.db.execute(
                    select(InterviewQuestion).where(InterviewQuestion.id.in_(ids), *self._live_q())
                )
            ).scalars().all()
            by_id = {r.id: r for r in rows}
            ordered = [by_id[i] for i in ids if i in by_id]
            seen: set[UUID] = set()
            unique: list[InterviewQuestion] = []
            for q in ordered:
                if q.id not in seen:
                    seen.add(q.id)
                    unique.append(q)
            return unique[: payload.question_count]

        stmt: Select = select(InterviewQuestion).where(*self._live_q())
        if payload.difficulty:
            stmt = stmt.where(InterviewQuestion.difficulty == payload.difficulty)
        if payload.question_type:
            stmt = stmt.where(InterviewQuestion.question_type == payload.question_type)
        if payload.experience_level:
            stmt = stmt.where(InterviewQuestion.experience_level == payload.experience_level)
        if payload.skill:
            stmt = (
                stmt.join(InterviewQuestionSkill)
                .join(Skill)
                .where(or_(Skill.slug == payload.skill, Skill.name.ilike(payload.skill)))
            )
        if payload.role:
            stmt = (
                stmt.join(InterviewQuestionRole)
                .join(JobRole)
                .where(or_(JobRole.slug == payload.role, JobRole.name.ilike(payload.role)))
            )
        if payload.company:
            stmt = (
                stmt.join(InterviewQuestionCompany)
                .join(Company)
                .where(or_(Company.slug == payload.company, Company.name.ilike(payload.company)))
            )
        stmt = stmt.distinct().order_by(InterviewQuestion.created_at.asc())
        rows = (await self.db.execute(stmt.limit(200))).scalars().all()
        if not rows:
            raise AppException("No approved questions match the selected filters", status_code=400)
        if payload.deterministic:
            rows = sorted(rows, key=lambda q: q.slug)
        else:
            # Stable shuffle by content hash salt — avoids needing random seed tables
            rows = sorted(rows, key=lambda q: hashlib.sha256(f"{q.id}".encode()).hexdigest())
        return rows[: payload.question_count]

    async def create_session(self, user: User, payload: InterviewSessionCreate) -> InterviewSessionDetail:
        if payload.source_type == InterviewSessionSource.RETRY_REVIEW and not payload.question_ids:
            review_ids = (
                await self.db.execute(
                    select(InterviewQuestionReview.question_id).where(
                        InterviewQuestionReview.user_id == user.id,
                        or_(
                            InterviewQuestionReview.needs_review.is_(True),
                            InterviewQuestionReview.self_rating.in_(
                                [InterviewSelfRating.NEEDS_REVIEW, InterviewSelfRating.PARTIAL]
                            ),
                            InterviewQuestionReview.confidence_level == InterviewConfidence.LOW,
                        ),
                    )
                )
            ).scalars().all()
            payload = payload.model_copy(update={"question_ids": list(review_ids)})

        pack = None
        if payload.pack_id or payload.pack_slug or payload.source_type == InterviewSessionSource.PACK:
            payload = payload.model_copy(update={"source_type": InterviewSessionSource.PACK})
            if payload.pack_id:
                pack = await self.db.get(InterviewPack, payload.pack_id)
            elif payload.pack_slug:
                pack = (
                    await self.db.execute(
                        select(InterviewPack).where(InterviewPack.slug == payload.pack_slug)
                    )
                ).scalar_one_or_none()
            if pack is None:
                raise AppException("Interview pack not found", status_code=404)

        questions = await self._select_questions(payload)
        if not questions:
            raise AppException("No questions available for session", status_code=400)

        title = payload.title
        if not title:
            if pack:
                title = f"{pack.title} ({payload.mode.value})"
            elif payload.source_type == InterviewSessionSource.RETRY_REVIEW:
                title = "Review Session"
            else:
                title = f"Custom Interview ({payload.mode.value})"

        now = _utcnow()
        session = InterviewSession(
            id=uuid4(),
            user_id=user.id,
            mode=payload.mode,
            source_type=payload.source_type,
            pack_id=pack.id if pack else None,
            title=title,
            question_count=len(questions),
            current_question_index=0,
            status=InterviewSessionStatus.ACTIVE,
            started_at=now,
            filters_json=payload.model_dump(mode="json"),
        )
        self.db.add(session)
        await self.db.flush()
        for idx, q in enumerate(questions):
            self.db.add(
                InterviewSessionQuestion(
                    id=uuid4(),
                    session_id=session.id,
                    question_id=q.id,
                    sort_order=idx,
                    status=InterviewSessionQuestionStatus.UNSEEN,
                )
            )
        await self.db.commit()
        return await self.get_session(user, session.id)

    async def get_session(self, user: User, session_id: UUID) -> InterviewSessionDetail:
        session = await self._get_owned_session(user, session_id)
        rows = (
            await self.db.execute(
                select(InterviewSessionQuestion)
                .where(InterviewSessionQuestion.session_id == session.id)
                .order_by(InterviewSessionQuestion.sort_order)
            )
        ).scalars().all()
        navigator = [
            InterviewNavigatorItem(
                number=i + 1,
                status=r.status,
                needs_review=r.needs_review,
                current=i == session.current_question_index,
            )
            for i, r in enumerate(rows)
        ]
        current = None
        if rows:
            idx = min(max(session.current_question_index, 0), len(rows) - 1)
            row = rows[idx]
            question = await self.db.get(InterviewQuestion, row.question_id)
            if question:
                if row.status == InterviewSessionQuestionStatus.UNSEEN:
                    row.status = InterviewSessionQuestionStatus.VIEWED
                    await self.db.commit()
                current = await self._public_question(
                    user=user,
                    session=session,
                    row=row,
                    question=question,
                    number=idx + 1,
                    include_answer=session.mode == InterviewSessionMode.STUDY,
                )
        return InterviewSessionDetail(
            session=await self._summary(session),
            navigator=navigator,
            current=current,
        )

    async def get_question(
        self, user: User, session_id: UUID, number: int
    ) -> InterviewSessionQuestionPublic:
        session = await self._get_owned_session(user, session_id)
        row, question = await self._session_row(session_id, number)
        session.current_question_index = number - 1
        if row.status == InterviewSessionQuestionStatus.UNSEEN:
            row.status = InterviewSessionQuestionStatus.VIEWED
        await self.db.commit()
        return await self._public_question(
            user=user,
            session=session,
            row=row,
            question=question,
            number=number,
            include_answer=session.mode == InterviewSessionMode.STUDY,
        )

    async def save_notes(
        self, user: User, session_id: UUID, number: int, payload: InterviewNotesPayload
    ) -> InterviewSessionQuestionPublic:
        session = await self._get_owned_session(user, session_id)
        row, question = await self._session_row(session_id, number)
        note = await self._note(user.id, question.id, session.id)
        if note is None:
            note = InterviewQuestionNote(
                id=uuid4(),
                user_id=user.id,
                question_id=question.id,
                session_id=session.id,
            )
            self.db.add(note)
        if payload.answer_text is not None:
            note.answer_text = payload.answer_text[:20000]
        if payload.private_notes is not None:
            note.private_notes = payload.private_notes[:20000]
        await self.db.commit()
        return await self._public_question(
            user=user,
            session=session,
            row=row,
            question=question,
            number=number,
            include_answer=session.mode == InterviewSessionMode.STUDY
            or row.answer_revealed_at is not None,
        )

    async def reveal(
        self, user: User, session_id: UUID, number: int
    ) -> InterviewSessionQuestionPublic:
        session = await self._get_owned_session(user, session_id)
        row, question = await self._session_row(session_id, number)
        if row.answer_revealed_at is None:
            row.answer_revealed_at = _utcnow()
            if row.status == InterviewSessionQuestionStatus.UNSEEN:
                row.status = InterviewSessionQuestionStatus.VIEWED
            await self.db.commit()
        return await self._public_question(
            user=user,
            session=session,
            row=row,
            question=question,
            number=number,
            include_answer=True,
        )

    async def submit_review(
        self, user: User, session_id: UUID, number: int, payload: InterviewReviewPayload
    ) -> InterviewSessionQuestionPublic:
        session = await self._get_owned_session(user, session_id)
        row, question = await self._session_row(session_id, number)
        if session.mode != InterviewSessionMode.STUDY and row.answer_revealed_at is None:
            raise AppException("Reveal the expected answer before reviewing", status_code=400)

        points = (
            await self.db.execute(
                select(InterviewAnswerPoint).where(InterviewAnswerPoint.question_id == question.id)
            )
        ).scalars().all()
        valid_ids = {p.id for p in points}
        checked = [pid for pid in payload.key_point_ids if pid in valid_ids]
        row.key_points_checked_json = [str(x) for x in checked]
        row.confidence_level = payload.confidence
        row.self_rating = payload.self_rating
        if payload.time_spent_seconds is not None:
            row.time_spent_seconds = payload.time_spent_seconds
        needs = payload.needs_review
        if needs is None:
            needs = payload.self_rating in {
                InterviewSelfRating.NEEDS_REVIEW,
                InterviewSelfRating.PARTIAL,
            } or payload.confidence == InterviewConfidence.LOW
        row.needs_review = bool(needs)
        row.status = InterviewSessionQuestionStatus.REVIEWED
        coverage = (len(checked) / len(points) * 100) if points else None

        existing = (
            await self.db.execute(
                select(InterviewQuestionReview).where(
                    InterviewQuestionReview.user_id == user.id,
                    InterviewQuestionReview.question_id == question.id,
                )
            )
        ).scalar_one_or_none()
        if existing is None:
            existing = InterviewQuestionReview(
                id=uuid4(),
                user_id=user.id,
                question_id=question.id,
                reviewed_at=_utcnow(),
            )
            self.db.add(existing)
        existing.last_session_id = session.id
        existing.self_rating = payload.self_rating
        existing.confidence_level = payload.confidence
        existing.key_point_coverage = coverage
        existing.needs_review = row.needs_review
        existing.reviewed_at = _utcnow()
        await self.db.commit()
        return await self._public_question(
            user=user,
            session=session,
            row=row,
            question=question,
            number=number,
            include_answer=True,
        )

    async def complete(self, user: User, session_id: UUID) -> InterviewSessionResults:
        session = await self._get_owned_session(user, session_id)
        if session.status == InterviewSessionStatus.ACTIVE:
            session.status = InterviewSessionStatus.COMPLETED
            session.completed_at = _utcnow()
            await self.db.commit()
        return await self.results(user, session_id)

    async def abandon(self, user: User, session_id: UUID) -> InterviewSessionSummary:
        session = await self._get_owned_session(user, session_id)
        if session.status == InterviewSessionStatus.ACTIVE:
            session.status = InterviewSessionStatus.ABANDONED
            session.completed_at = _utcnow()
            await self.db.commit()
        return await self._summary(session)

    async def results(self, user: User, session_id: UUID) -> InterviewSessionResults:
        session = await self._get_owned_session(user, session_id)
        rows = (
            await self.db.execute(
                select(InterviewSessionQuestion)
                .where(InterviewSessionQuestion.session_id == session.id)
                .order_by(InterviewSessionQuestion.sort_order)
            )
        ).scalars().all()
        rating_counts = defaultdict(int)
        confidence = defaultdict(int)
        coverages: list[float] = []
        weak: list[UUID] = []
        skill_map: dict[str, list[float]] = defaultdict(list)
        type_map: dict[str, list[InterviewSessionQuestion]] = defaultdict(list)

        tags = await self._question_tags([r.question_id for r in rows])
        for r in rows:
            q = await self.db.get(InterviewQuestion, r.question_id)
            if q:
                type_map[q.question_type.value].append(r)
            if r.self_rating:
                rating_counts[r.self_rating.value] += 1
            if r.confidence_level:
                confidence[r.confidence_level.value] += 1
            points = (
                await self.db.execute(
                    select(func.count()).select_from(InterviewAnswerPoint).where(
                        InterviewAnswerPoint.question_id == r.question_id
                    )
                )
            ).scalar_one()
            checked = r.key_points_checked_json or []
            if points and r.self_rating is not None:
                cov = len(checked) / points * 100
                coverages.append(cov)
                for skill in tags.get(r.question_id, {}).get("skills", []):
                    skill_map[skill].append(cov)
            if r.needs_review or r.self_rating in {
                InterviewSelfRating.NEEDS_REVIEW,
                InterviewSelfRating.PARTIAL,
            }:
                weak.append(r.question_id)

        summary = await self._summary(session)
        reviewed = sum(1 for r in rows if r.self_rating is not None)
        return InterviewSessionResults(
            session=summary,
            questions_total=len(rows),
            reviewed_count=reviewed,
            needs_review_count=sum(1 for r in rows if r.needs_review),
            strong=rating_counts.get("strong", 0),
            good=rating_counts.get("good", 0),
            partial=rating_counts.get("partial", 0),
            needs_review_rating=rating_counts.get("needs_review", 0),
            key_point_coverage_avg=(sum(coverages) / len(coverages)) if coverages else None,
            confidence_breakdown=dict(confidence),
            skill_breakdown=[
                InterviewSkillBreakdown(
                    skill=k,
                    question_count=len(v),
                    key_point_coverage_avg=(sum(v) / len(v)) if v else None,
                )
                for k, v in sorted(skill_map.items())
            ],
            type_breakdown=[
                InterviewTypeBreakdown(
                    question_type=k,
                    question_count=len(v),
                    needs_review_count=sum(1 for r in v if r.needs_review),
                )
                for k, v in sorted(type_map.items())
            ],
            weak_question_ids=weak,
        )

    async def history(self, user: User, *, skip: int = 0, limit: int = 50) -> list[InterviewSessionSummary]:
        sessions = (
            await self.db.execute(
                select(InterviewSession)
                .where(InterviewSession.user_id == user.id)
                .order_by(InterviewSession.started_at.desc())
                .offset(skip)
                .limit(limit)
            )
        ).scalars().all()
        return [await self._summary(s) for s in sessions]

    async def progress(self, user: User) -> InterviewProgressResponse:
        reviews = (
            await self.db.execute(
                select(InterviewQuestionReview).where(InterviewQuestionReview.user_id == user.id)
            )
        ).scalars().all()
        completed = (
            await self.db.execute(
                select(func.count())
                .select_from(InterviewSession)
                .where(
                    InterviewSession.user_id == user.id,
                    InterviewSession.status == InterviewSessionStatus.COMPLETED,
                )
            )
        ).scalar_one()
        high = sum(1 for r in reviews if r.confidence_level == InterviewConfidence.HIGH)
        coverages = [r.key_point_coverage for r in reviews if r.key_point_coverage is not None]
        qids = [r.question_id for r in reviews]
        tags = await self._question_tags(qids)
        by_role: dict[str, int] = defaultdict(int)
        by_skill: dict[str, int] = defaultdict(int)
        by_type: dict[str, int] = defaultdict(int)
        by_exp: dict[str, int] = defaultdict(int)
        for r in reviews:
            q = await self.db.get(InterviewQuestion, r.question_id)
            if q:
                by_type[q.question_type.value] += 1
                by_exp[q.experience_level.value] += 1
            for role in tags.get(r.question_id, {}).get("roles", []):
                by_role[role] += 1
            for skill in tags.get(r.question_id, {}).get("skills", []):
                by_skill[skill] += 1
        return InterviewProgressResponse(
            questions_reviewed=len(reviews),
            sessions_completed=int(completed or 0),
            needs_review=sum(1 for r in reviews if r.needs_review),
            high_confidence_percent=(high / len(reviews) * 100) if reviews else None,
            average_key_point_coverage=(sum(coverages) / len(coverages)) if coverages else None,
            by_role=dict(by_role),
            by_skill=dict(by_skill),
            by_type=dict(by_type),
            by_experience=dict(by_exp),
        )

    async def needs_review(self, user: User) -> list[InterviewNeedsReviewItem]:
        reviews = (
            await self.db.execute(
                select(InterviewQuestionReview)
                .where(
                    InterviewQuestionReview.user_id == user.id,
                    or_(
                        InterviewQuestionReview.needs_review.is_(True),
                        InterviewQuestionReview.self_rating.in_(
                            [InterviewSelfRating.NEEDS_REVIEW, InterviewSelfRating.PARTIAL]
                        ),
                        InterviewQuestionReview.confidence_level == InterviewConfidence.LOW,
                    ),
                )
                .order_by(InterviewQuestionReview.reviewed_at.desc())
            )
        ).scalars().all()
        items: list[InterviewNeedsReviewItem] = []
        tags = await self._question_tags([r.question_id for r in reviews])
        for r in reviews:
            q = await self.db.get(InterviewQuestion, r.question_id)
            if not q or not q.is_active:
                continue
            items.append(
                InterviewNeedsReviewItem(
                    question_id=q.id,
                    slug=q.slug,
                    question_text=q.question_text,
                    self_rating=r.self_rating,
                    confidence_level=r.confidence_level,
                    key_point_coverage=r.key_point_coverage,
                    needs_review=r.needs_review,
                    skills=tags.get(q.id, {}).get("skills", []),
                )
            )
        return items

    async def mark_reviewed(self, user: User, question_id: UUID) -> InterviewNeedsReviewItem:
        review = (
            await self.db.execute(
                select(InterviewQuestionReview).where(
                    InterviewQuestionReview.user_id == user.id,
                    InterviewQuestionReview.question_id == question_id,
                )
            )
        ).scalar_one_or_none()
        if review is None:
            raise AppException("Review not found", status_code=404)
        review.needs_review = False
        if review.self_rating in {InterviewSelfRating.NEEDS_REVIEW, InterviewSelfRating.PARTIAL}:
            review.self_rating = InterviewSelfRating.GOOD
        review.reviewed_at = _utcnow()
        await self.db.commit()
        q = await self.db.get(InterviewQuestion, question_id)
        tags = await self._question_tags([question_id])
        return InterviewNeedsReviewItem(
            question_id=question_id,
            slug=q.slug if q else "",
            question_text=q.question_text if q else "",
            self_rating=review.self_rating,
            confidence_level=review.confidence_level,
            key_point_coverage=review.key_point_coverage,
            needs_review=False,
            skills=tags.get(question_id, {}).get("skills", []),
        )

    async def hub(self, user: User) -> InterviewHubResponse:
        active = (
            await self.db.execute(
                select(InterviewSession)
                .where(
                    InterviewSession.user_id == user.id,
                    InterviewSession.status == InterviewSessionStatus.ACTIVE,
                )
                .order_by(InterviewSession.started_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        packs = (
            await self.db.execute(
                select(InterviewPack).where(InterviewPack.is_active.is_(True)).order_by(InterviewPack.title)
            )
        ).scalars().all()
        pack_public: list[InterviewPackPublic] = []
        for p in packs:
            count = (
                await self.db.execute(
                    select(func.count())
                    .select_from(InterviewPackQuestion)
                    .join(InterviewQuestion, InterviewQuestion.id == InterviewPackQuestion.question_id)
                    .where(InterviewPackQuestion.pack_id == p.id, *self._live_q())
                )
            ).scalar_one()
            pack_public.append(
                InterviewPackPublic(
                    id=p.id,
                    slug=p.slug,
                    title=p.title,
                    description=p.description,
                    experience_level=p.experience_level,
                    question_count=int(count or 0),
                )
            )
        progress = await self.progress(user)
        recent = await self.history(user, limit=5)
        return InterviewHubResponse(
            continue_session=await self._summary(active) if active else None,
            packs=pack_public,
            progress=progress,
            needs_review_count=progress.needs_review,
            recent_sessions=recent,
        )

    async def pack_detail(self, user: User, slug: str) -> InterviewPackDetail:
        pack = (
            await self.db.execute(select(InterviewPack).where(InterviewPack.slug == slug))
        ).scalar_one_or_none()
        if pack is None or not pack.is_active:
            raise AppException("Pack not found", status_code=404)
        items = (
            await self.db.execute(
                select(InterviewPackQuestion, InterviewQuestion)
                .join(InterviewQuestion, InterviewQuestion.id == InterviewPackQuestion.question_id)
                .where(InterviewPackQuestion.pack_id == pack.id, *self._live_q())
                .order_by(InterviewPackQuestion.sort_order)
            )
        ).all()
        questions = [q for _, q in items]
        tags = await self._question_tags([q.id for q in questions])
        skills: set[str] = set()
        mix: dict[str, int] = defaultdict(int)
        for q in questions:
            mix[q.difficulty.value] += 1
            skills.update(tags.get(q.id, {}).get("skills", []))
        role = await self.db.get(JobRole, pack.target_role_id) if pack.target_role_id else None
        company = await self.db.get(Company, pack.target_company_id) if pack.target_company_id else None
        active = (
            await self.db.execute(
                select(InterviewSession)
                .where(
                    InterviewSession.user_id == user.id,
                    InterviewSession.pack_id == pack.id,
                    InterviewSession.status == InterviewSessionStatus.ACTIVE,
                )
                .order_by(InterviewSession.started_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        return InterviewPackDetail(
            id=pack.id,
            slug=pack.slug,
            title=pack.title,
            description=pack.description,
            experience_level=pack.experience_level,
            question_count=len(questions),
            target_role=role.name if role else None,
            target_company=company.name if company else None,
            skills_covered=sorted(skills),
            difficulty_mix=dict(mix),
            estimated_minutes=max(5, len(questions) * 3),
            active_session_id=active.id if active else None,
        )
