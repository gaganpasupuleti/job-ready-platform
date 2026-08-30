from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import Difficulty
from app.models.question import Question, QuestionOption
from app.models.tagging import QuestionCompany, QuestionRole, QuestionSkill
from app.models.taxonomy import Category, Domain, Subtopic, Topic
from app.repositories.base import BaseRepository


class TaxonomyRepository(BaseRepository):
    async def get_full_catalog(self) -> list[Domain]:
        stmt = (
            select(Domain)
            .where(Domain.is_active.is_(True))
            .options(
                selectinload(Domain.categories).selectinload(Category.topics).selectinload(Topic.subtopics)
            )
            .order_by(Domain.name)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().unique().all())

    async def get_category(self, category_id: UUID) -> Category | None:
        result = await self.db.execute(select(Category).where(Category.id == category_id))
        return result.scalar_one_or_none()

    async def get_topic(self, topic_id: UUID) -> Topic | None:
        result = await self.db.execute(select(Topic).where(Topic.id == topic_id))
        return result.scalar_one_or_none()

    async def get_topic_by_slug(self, category_id: UUID, slug: str) -> Topic | None:
        result = await self.db.execute(
            select(Topic).where(Topic.category_id == category_id, Topic.slug == slug)
        )
        return result.scalar_one_or_none()


class QuestionRepository(BaseRepository):
    async def get_by_id(self, question_id: UUID) -> Question | None:
        stmt = (
            select(Question)
            .where(Question.id == question_id)
            .options(selectinload(Question.options))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_for_session(
        self,
        *,
        category_id: UUID | None,
        topic_id: UUID | None,
        difficulty: Difficulty | None,
        limit: int,
        exclude_ids: list[UUID] | None = None,
    ) -> list[Question]:
        stmt = (
            select(Question)
            .where(Question.is_active.is_(True))
            .options(selectinload(Question.options))
        )
        if category_id:
            stmt = stmt.where(Question.category_id == category_id)
        if topic_id:
            stmt = stmt.where(Question.topic_id == topic_id)
        if difficulty:
            stmt = stmt.where(Question.difficulty == difficulty)
        if exclude_ids:
            stmt = stmt.where(Question.id.notin_(exclude_ids))
        stmt = stmt.order_by(func.random()).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().unique().all())

    async def list_admin(
        self,
        *,
        domain_id: UUID | None = None,
        category_id: UUID | None = None,
        topic_id: UUID | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Question], int]:
        stmt = select(Question)
        count_stmt = select(func.count()).select_from(Question)
        if domain_id:
            stmt = stmt.where(Question.domain_id == domain_id)
            count_stmt = count_stmt.where(Question.domain_id == domain_id)
        if category_id:
            stmt = stmt.where(Question.category_id == category_id)
            count_stmt = count_stmt.where(Question.category_id == category_id)
        if topic_id:
            stmt = stmt.where(Question.topic_id == topic_id)
            count_stmt = count_stmt.where(Question.topic_id == topic_id)
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(Question.question_text.ilike(pattern))
            count_stmt = count_stmt.where(Question.question_text.ilike(pattern))

        total = (await self.db.execute(count_stmt)).scalar_one()
        result = await self.db.execute(
            stmt.order_by(Question.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total

    async def save(self, question: Question) -> Question:
        self.db.add(question)
        await self.db.commit()
        await self.db.refresh(question)
        return question

    async def delete_tags(self, question_id: UUID) -> None:
        await self.db.execute(
            QuestionSkill.__table__.delete().where(QuestionSkill.question_id == question_id)
        )
        await self.db.execute(
            QuestionRole.__table__.delete().where(QuestionRole.question_id == question_id)
        )
        await self.db.execute(
            QuestionCompany.__table__.delete().where(QuestionCompany.question_id == question_id)
        )

    async def replace_options(self, question: Question, options: list[QuestionOption]) -> None:
        for existing in list(question.options):
            await self.db.delete(existing)
        question.options = options
        await self.db.commit()
        await self.db.refresh(question, attribute_names=["options"])

    async def get_skill_names(self, question_id: UUID) -> list[str]:
        from app.models.tagging import Skill

        stmt = (
            select(Skill.name)
            .join(QuestionSkill, QuestionSkill.skill_id == Skill.id)
            .where(QuestionSkill.question_id == question_id)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_topic_name(self, topic_id: UUID) -> str | None:
        result = await self.db.execute(select(Topic.name).where(Topic.id == topic_id))
        return result.scalar_one_or_none()

    async def get_names_for_questions(self, questions: list[Question]) -> dict[str, dict[str, str]]:
        domain_ids = {q.domain_id for q in questions}
        category_ids = {q.category_id for q in questions}
        topic_ids = {q.topic_id for q in questions}

        domains = {
            row.id: row.name
            for row in (await self.db.execute(select(Domain).where(Domain.id.in_(domain_ids))))
            .scalars()
            .all()
        }
        categories = {
            row.id: row.name
            for row in (await self.db.execute(select(Category).where(Category.id.in_(category_ids))))
            .scalars()
            .all()
        }
        topics = {
            row.id: row.name
            for row in (await self.db.execute(select(Topic).where(Topic.id.in_(topic_ids))))
            .scalars()
            .all()
        }
        return {
            str(q.id): {
                "domain_name": domains.get(q.domain_id, ""),
                "category_name": categories.get(q.category_id, ""),
                "topic_name": topics.get(q.topic_id, ""),
            }
            for q in questions
        }
