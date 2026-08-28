from uuid import UUID

from sqlalchemy import select
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
        stmt = select(PracticeAnswer).where(
            PracticeAnswer.session_id == session_id,
            PracticeAnswer.question_id == question_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def save_answer(self, answer: PracticeAnswer) -> PracticeAnswer:
        self.db.add(answer)
        await self.db.commit()
        await self.db.refresh(answer)
        return answer

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
