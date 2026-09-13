from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.practice import Bookmark, PracticeAnswer, PracticeSession, PracticeSessionQuestion
from app.repositories.base import BaseRepository


class PracticeRepository(BaseRepository):
    async def create_session(self, session: PracticeSession) -> PracticeSession:
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_session_for_user(self, session_id: UUID, user_id: UUID) -> PracticeSession | None:
        stmt = (
            select(PracticeSession)
            .where(PracticeSession.id == session_id, PracticeSession.user_id == user_id)
            .options(
                selectinload(PracticeSession.questions),
                selectinload(PracticeSession.answers),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def lock_session_for_user(self, session_id: UUID, user_id: UUID) -> PracticeSession | None:
        """Lock the session row so autosave and completion cannot interleave writes."""
        stmt = (
            select(PracticeSession)
            .where(PracticeSession.id == session_id, PracticeSession.user_id == user_id)
            .options(
                selectinload(PracticeSession.questions),
                selectinload(PracticeSession.answers),
            )
            .with_for_update()
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def save_session(self, session: PracticeSession) -> PracticeSession:
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def add_session_questions(
        self, items: list[PracticeSessionQuestion]
    ) -> None:
        self.db.add_all(items)
        await self.db.commit()

    async def get_answer(
        self, session_id: UUID, question_id: UUID
    ) -> PracticeAnswer | None:
        stmt = (
            select(PracticeAnswer)
            .where(
                PracticeAnswer.session_id == session_id,
                PracticeAnswer.question_id == question_id,
            )
            .order_by(PracticeAnswer.updated_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def save_answer(self, answer: PracticeAnswer) -> PracticeAnswer:
        if answer.answered_at is None:
            await self.upsert_draft(answer)
        else:
            await self.upsert_final(answer)
        saved = await self.get_answer(answer.session_id, answer.question_id)
        if saved is None:
            raise RuntimeError("practice answer was not persisted")
        return saved

    async def upsert_draft(self, answer: PracticeAnswer) -> None:
        """Insert or update a draft. A finalized sibling is left unchanged."""
        values = {
            "id": answer.id or uuid4(),
            "session_id": answer.session_id,
            "question_id": answer.question_id,
            "selected_option_ids": answer.selected_option_ids or [],
            "is_correct": None,
            "marks_awarded": 0.0,
            "time_spent_seconds": answer.time_spent_seconds or 0,
            "marked_for_review": bool(answer.marked_for_review),
        }
        stmt = insert(PracticeAnswer).values(**values).on_conflict_do_update(
            constraint="uq_practice_answer_session_question",
            set_={
                "selected_option_ids": values["selected_option_ids"],
                "time_spent_seconds": values["time_spent_seconds"],
                "marked_for_review": values["marked_for_review"],
                "updated_at": func.now(),
            },
            where=PracticeAnswer.answered_at.is_(None),
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def upsert_final(self, answer: PracticeAnswer) -> None:
        """Insert or replace with the graded answer so a concurrent draft cannot win."""
        values = {
            "id": answer.id or uuid4(),
            "session_id": answer.session_id,
            "question_id": answer.question_id,
            "selected_option_ids": answer.selected_option_ids or [],
            "is_correct": answer.is_correct,
            "marks_awarded": answer.marks_awarded,
            "time_spent_seconds": answer.time_spent_seconds or 0,
            "marked_for_review": bool(answer.marked_for_review),
            "answered_at": answer.answered_at,
        }
        stmt = insert(PracticeAnswer).values(**values).on_conflict_do_update(
            constraint="uq_practice_answer_session_question",
            set_={
                "selected_option_ids": values["selected_option_ids"],
                "is_correct": values["is_correct"],
                "marks_awarded": values["marks_awarded"],
                "time_spent_seconds": values["time_spent_seconds"],
                "marked_for_review": values["marked_for_review"],
                "answered_at": values["answered_at"],
                "updated_at": func.now(),
            },
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def list_history(self, user_id: UUID, limit: int = 20) -> list[PracticeSession]:
        stmt = (
            select(PracticeSession)
            .where(PracticeSession.user_id == user_id)
            .order_by(PracticeSession.started_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def is_bookmarked(self, user_id: UUID, question_id: UUID) -> bool:
        stmt = select(Bookmark.id).where(
            Bookmark.user_id == user_id, Bookmark.question_id == question_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def list_question_bookmarks(self, user_id: UUID) -> list[dict]:
        from app.models.question import Question

        stmt = (
            select(Question, Bookmark)
            .join(Bookmark, Bookmark.question_id == Question.id)
            .where(Bookmark.user_id == user_id)
            .order_by(Bookmark.created_at.desc())
        )
        result = await self.db.execute(stmt)
        rows = result.all()
        return [
            {
                "id": str(question.id),
                "question_text": question.question_text,
                "difficulty": question.difficulty.value,
            }
            for question, _bookmark in rows
        ]

    async def toggle_bookmark(self, user_id: UUID, question_id: UUID) -> bool:
        stmt = select(Bookmark).where(
            Bookmark.user_id == user_id, Bookmark.question_id == question_id
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            await self.db.delete(existing)
            await self.db.commit()
            return False
        self.db.add(Bookmark(user_id=user_id, question_id=question_id))
        await self.db.commit()
        return True
