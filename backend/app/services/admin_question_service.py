from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.question import Question, QuestionOption
from app.models.tagging import QuestionCompany, QuestionRole, QuestionSkill
from app.models.user import User
from app.repositories.question_repository import QuestionRepository, TaxonomyRepository
from app.schemas.admin import (
    AdminOptionInput,
    AdminQuestionCreate,
    AdminQuestionDetail,
    AdminQuestionListItem,
    AdminQuestionListResponse,
    AdminQuestionUpdate,
)
from app.services.catalog_service import CatalogService


class AdminQuestionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.questions = QuestionRepository(db)
        self.taxonomy = TaxonomyRepository(db)
        self.catalog = CatalogService(db)

    async def list_questions(
        self,
        *,
        domain_id: UUID | None = None,
        category_id: UUID | None = None,
        topic_id: UUID | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> AdminQuestionListResponse:
        rows, total = await self.questions.list_admin(
            domain_id=domain_id,
            category_id=category_id,
            topic_id=topic_id,
            search=search,
            skip=skip,
            limit=limit,
        )
        names = await self.questions.get_names_for_questions(rows)
        return AdminQuestionListResponse(
            questions=[
                AdminQuestionListItem(
                    id=row.id,
                    title=row.title,
                    question_text=row.question_text,
                    question_type=row.question_type,
                    difficulty=row.difficulty,
                    domain_name=names[str(row.id)]["domain_name"],
                    category_name=names[str(row.id)]["category_name"],
                    topic_name=names[str(row.id)]["topic_name"],
                    is_active=row.is_active,
                    is_sample=row.is_sample,
                )
                for row in rows
            ],
            total=total,
        )

    async def get_question(self, question_id: UUID) -> AdminQuestionDetail:
        question = await self.questions.get_by_id(question_id)
        if question is None:
            raise AppException("Question not found", status_code=404)
        return await self._to_detail(question)

    async def create_question(self, user: User, payload: AdminQuestionCreate) -> AdminQuestionDetail:
        self._validate_options(payload.options, payload.question_type.value)
        question = Question(
            question_type=payload.question_type,
            title=payload.title,
            question_text=payload.question_text,
            explanation=payload.explanation,
            difficulty=payload.difficulty,
            domain_id=payload.domain_id,
            category_id=payload.category_id,
            topic_id=payload.topic_id,
            subtopic_id=payload.subtopic_id,
            marks=payload.marks,
            negative_marks=payload.negative_marks,
            estimated_time_seconds=payload.estimated_time_seconds,
            is_active=payload.is_active,
            is_premium=payload.is_premium,
            is_sample=False,
            created_by=user.id,
            options=self._build_options(payload.options),
        )
        question = await self.questions.save(question)
        await self._assign_tags(question.id, payload.skill_ids, payload.role_ids, payload.company_ids)
        await self.catalog.invalidate_cache()
        question = await self.questions.get_by_id(question.id)
        return await self._to_detail(question)

    async def update_question(
        self, question_id: UUID, payload: AdminQuestionUpdate
    ) -> AdminQuestionDetail:
        question = await self.questions.get_by_id(question_id)
        if question is None:
            raise AppException("Question not found", status_code=404)

        for field in (
            "question_type",
            "title",
            "question_text",
            "explanation",
            "difficulty",
            "domain_id",
            "category_id",
            "topic_id",
            "subtopic_id",
            "marks",
            "negative_marks",
            "estimated_time_seconds",
            "is_active",
            "is_premium",
        ):
            value = getattr(payload, field)
            if value is not None:
                setattr(question, field, value)

        if payload.options is not None:
            qtype = payload.question_type or question.question_type
            self._validate_options(payload.options, qtype.value)
            await self.questions.replace_options(question, self._build_options(payload.options))

        if payload.skill_ids is not None or payload.role_ids is not None or payload.company_ids is not None:
            await self.questions.delete_tags(question.id)
            await self._assign_tags(
                question.id,
                payload.skill_ids or [],
                payload.role_ids or [],
                payload.company_ids or [],
            )

        question = await self.questions.save(question)
        await self.catalog.invalidate_cache()
        question = await self.questions.get_by_id(question.id)
        return await self._to_detail(question)

    async def _assign_tags(
        self,
        question_id: UUID,
        skill_ids: list[UUID],
        role_ids: list[UUID],
        company_ids: list[UUID],
    ) -> None:
        for skill_id in skill_ids:
            self.db.add(QuestionSkill(question_id=question_id, skill_id=skill_id))
        for role_id in role_ids:
            self.db.add(QuestionRole(question_id=question_id, role_id=role_id))
        for company_id in company_ids:
            self.db.add(QuestionCompany(question_id=question_id, company_id=company_id))
        await self.db.commit()

    async def _to_detail(self, question: Question) -> AdminQuestionDetail:
        from sqlalchemy import select

        skill_ids = list(
            (
                await self.db.execute(
                    select(QuestionSkill.skill_id).where(QuestionSkill.question_id == question.id)
                )
            )
            .scalars()
            .all()
        )
        role_ids = list(
            (
                await self.db.execute(
                    select(QuestionRole.role_id).where(QuestionRole.question_id == question.id)
                )
            )
            .scalars()
            .all()
        )
        company_ids = list(
            (
                await self.db.execute(
                    select(QuestionCompany.company_id).where(
                        QuestionCompany.question_id == question.id
                    )
                )
            )
            .scalars()
            .all()
        )
        return AdminQuestionDetail(
            id=question.id,
            question_type=question.question_type,
            title=question.title,
            question_text=question.question_text,
            explanation=question.explanation,
            difficulty=question.difficulty,
            domain_id=question.domain_id,
            category_id=question.category_id,
            topic_id=question.topic_id,
            subtopic_id=question.subtopic_id,
            marks=question.marks,
            negative_marks=question.negative_marks,
            estimated_time_seconds=question.estimated_time_seconds,
            is_active=question.is_active,
            is_premium=question.is_premium,
            is_sample=question.is_sample,
            skill_ids=skill_ids,
            role_ids=role_ids,
            company_ids=company_ids,
            options=[
                AdminOptionInput(
                    id=opt.id,
                    option_text=opt.option_text,
                    is_correct=opt.is_correct,
                    sort_order=opt.sort_order,
                )
                for opt in question.options
            ],
        )

    def _build_options(self, options: list[AdminOptionInput]) -> list[QuestionOption]:
        return [
            QuestionOption(
                id=option.id or uuid4(),
                option_text=option.option_text,
                is_correct=option.is_correct,
                sort_order=option.sort_order,
            )
            for option in options
        ]

    def _validate_options(self, options: list[AdminOptionInput], question_type: str) -> None:
        if len(options) < 2 and question_type != "true_false":
            raise AppException("At least two options are required", status_code=400)
        correct_count = len([opt for opt in options if opt.is_correct])
        if correct_count == 0:
            raise AppException("At least one correct option is required", status_code=400)
        if question_type == "single_choice" and correct_count != 1:
            raise AppException("Single choice questions must have exactly one correct option", status_code=400)
