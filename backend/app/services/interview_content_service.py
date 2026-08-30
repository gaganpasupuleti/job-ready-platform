# ruff: noqa: E501
from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.content.publisher import publish_validated_question
from app.content.validator import validate_question_payload
from app.core.exceptions import AppException
from app.models.interview import (
    ContentGenerationBatch,
    ContentGenerationCandidate,
    InterviewPack,
    InterviewPackQuestion,
    InterviewQuestion,
    InterviewQuestionCompany,
    InterviewQuestionRole,
    InterviewQuestionSkill,
)
from app.models.interview_enums import ContentReviewStatus, ContentValidationStatus
from app.models.tagging import Company, JobRole, Skill
from app.schemas.interview import (
    ContentBatchAdmin,
    ContentBatchListResponse,
    ContentCandidateAdmin,
    ContentCandidateListResponse,
    ContentCandidateUpdate,
    InterviewAnswerPointPublic,
    InterviewPackPublic,
    InterviewQuestionListItem,
    InterviewQuestionListResponse,
    InterviewQuestionPublic,
)


def _candidate_schema(c: ContentGenerationCandidate) -> ContentCandidateAdmin:
    return ContentCandidateAdmin(
        id=c.id,
        batch_id=c.batch_id,
        content_hash=c.content_hash,
        validation_status=c.validation_status,
        review_status=c.review_status,
        validation_errors=c.validation_errors,
        payload_json=c.payload_json,
        published_question_id=c.published_question_id,
        created_at=c.created_at,
    )


def _batch_schema(b: ContentGenerationBatch, include_candidates: bool = False) -> ContentBatchAdmin:
    return ContentBatchAdmin(
        id=b.id,
        batch_date=b.batch_date,
        content_type=b.content_type.value if hasattr(b.content_type, "value") else str(b.content_type),
        target_domain=b.target_domain,
        target_role=b.target_role,
        target_skill=b.target_skill,
        target_company=b.target_company,
        requested_count=b.requested_count,
        generated_count=b.generated_count,
        accepted_count=b.accepted_count,
        rejected_count=b.rejected_count,
        status=b.status,
        generator=b.generator,
        source_filename=b.source_filename,
        created_at=b.created_at,
        candidates=[_candidate_schema(c) for c in b.candidates] if include_candidates else [],
    )


class InterviewContentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _live_filter(self):
        return (
            InterviewQuestion.review_status == ContentReviewStatus.APPROVED,
            InterviewQuestion.is_active.is_(True),
        )

    async def list_public(
        self,
        *,
        role: str | None = None,
        skill: str | None = None,
        difficulty: str | None = None,
        question_type: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> InterviewQuestionListResponse:
        stmt: Select = select(InterviewQuestion).where(*self._live_filter())
        if difficulty:
            stmt = stmt.where(InterviewQuestion.difficulty == difficulty)
        if question_type:
            stmt = stmt.where(InterviewQuestion.question_type == question_type)
        if skill:
            stmt = (
                stmt.join(InterviewQuestionSkill)
                .join(Skill)
                .where(or_(func.lower(Skill.name) == skill.lower(), func.lower(Skill.slug) == skill.lower()))
            )
        if role:
            stmt = (
                stmt.join(InterviewQuestionRole)
                .join(JobRole)
                .where(
                    or_(func.lower(JobRole.name) == role.lower(), func.lower(JobRole.slug) == role.lower())
                )
            )
        stmt = stmt.order_by(InterviewQuestion.created_at.desc()).offset(skip).limit(limit)
        rows = (await self.db.execute(stmt.options(selectinload(InterviewQuestion.key_points)))).unique().scalars().all()
        count_stmt = select(func.count()).select_from(InterviewQuestion).where(*self._live_filter())
        total = int(await self.db.scalar(count_stmt) or 0)

        items = []
        for q in rows:
            skill_names = await self._skill_names(q.id)
            role_names = await self._role_names(q.id)
            items.append(
                InterviewQuestionListItem(
                    id=q.id,
                    slug=q.slug,
                    question_text=q.question_text,
                    question_type=q.question_type,
                    difficulty=q.difficulty,
                    experience_level=q.experience_level,
                    skills=skill_names,
                    roles=role_names,
                )
            )
        return InterviewQuestionListResponse(items=items, total=total)

    async def get_public(self, slug_or_id: str) -> InterviewQuestionPublic:
        q = await self._get_question(slug_or_id, live_only=True)
        return InterviewQuestionPublic(
            id=q.id,
            slug=q.slug,
            question_text=q.question_text,
            question_type=q.question_type,
            difficulty=q.difficulty,
            experience_level=q.experience_level,
            expected_answer=q.expected_answer,
            explanation=q.explanation,
            key_points=[
                InterviewAnswerPointPublic(id=p.id, point_text=p.point_text, sort_order=p.sort_order)
                for p in q.key_points
            ],
            skills=await self._skill_names(q.id),
            roles=await self._role_names(q.id),
            companies=await self._company_names(q.id),
        )

    async def list_packs(self) -> list[InterviewPackPublic]:
        packs = (
            await self.db.execute(
                select(InterviewPack).where(InterviewPack.is_active.is_(True)).order_by(InterviewPack.title)
            )
        ).scalars().all()
        out = []
        for pack in packs:
            count = await self.db.scalar(
                select(func.count()).select_from(InterviewPackQuestion).where(
                    InterviewPackQuestion.pack_id == pack.id
                )
            )
            out.append(
                InterviewPackPublic(
                    id=pack.id,
                    slug=pack.slug,
                    title=pack.title,
                    description=pack.description,
                    experience_level=pack.experience_level,
                    question_count=int(count or 0),
                )
            )
        return out

    async def _get_question(self, slug_or_id: str, *, live_only: bool) -> InterviewQuestion:
        stmt = select(InterviewQuestion).options(selectinload(InterviewQuestion.key_points))
        try:
            uid = UUID(slug_or_id)
            stmt = stmt.where(InterviewQuestion.id == uid)
        except ValueError:
            stmt = stmt.where(InterviewQuestion.slug == slug_or_id)
        if live_only:
            stmt = stmt.where(*self._live_filter())
        q = (await self.db.execute(stmt)).scalar_one_or_none()
        if q is None:
            raise AppException("Interview question not found", status_code=404)
        return q

    async def _skill_names(self, question_id: UUID) -> list[str]:
        rows = (
            await self.db.execute(
                select(Skill.name)
                .join(InterviewQuestionSkill, InterviewQuestionSkill.skill_id == Skill.id)
                .where(InterviewQuestionSkill.question_id == question_id)
            )
        ).scalars().all()
        return list(rows)

    async def _role_names(self, question_id: UUID) -> list[str]:
        rows = (
            await self.db.execute(
                select(JobRole.name)
                .join(InterviewQuestionRole, InterviewQuestionRole.role_id == JobRole.id)
                .where(InterviewQuestionRole.question_id == question_id)
            )
        ).scalars().all()
        return list(rows)

    async def _company_names(self, question_id: UUID) -> list[str]:
        rows = (
            await self.db.execute(
                select(Company.name)
                .join(InterviewQuestionCompany, InterviewQuestionCompany.company_id == Company.id)
                .where(InterviewQuestionCompany.question_id == question_id)
            )
        ).scalars().all()
        return list(rows)

    async def list_batches(self, skip: int = 0, limit: int = 50) -> ContentBatchListResponse:
        total = int(await self.db.scalar(select(func.count()).select_from(ContentGenerationBatch)) or 0)
        rows = (
            await self.db.execute(
                select(ContentGenerationBatch)
                .order_by(ContentGenerationBatch.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
        ).scalars().all()
        return ContentBatchListResponse(items=[_batch_schema(b) for b in rows], total=total)

    async def get_batch(self, batch_id: UUID) -> ContentBatchAdmin:
        batch = (
            await self.db.execute(
                select(ContentGenerationBatch)
                .options(selectinload(ContentGenerationBatch.candidates))
                .where(ContentGenerationBatch.id == batch_id)
            )
        ).scalar_one_or_none()
        if batch is None:
            raise AppException("Batch not found", status_code=404)
        return _batch_schema(batch, include_candidates=True)

    async def list_candidates(
        self,
        *,
        batch_id: UUID | None = None,
        review_status: str | None = None,
        skill: str | None = None,
        role: str | None = None,
        company: str | None = None,
        difficulty: str | None = None,
        content_type: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> ContentCandidateListResponse:
        stmt = select(ContentGenerationCandidate)
        count_stmt = select(func.count()).select_from(ContentGenerationCandidate)
        if batch_id:
            stmt = stmt.where(ContentGenerationCandidate.batch_id == batch_id)
            count_stmt = count_stmt.where(ContentGenerationCandidate.batch_id == batch_id)
        if review_status:
            stmt = stmt.where(ContentGenerationCandidate.review_status == review_status)
            count_stmt = count_stmt.where(ContentGenerationCandidate.review_status == review_status)
        if content_type:
            stmt = stmt.where(ContentGenerationCandidate.content_type == content_type)
            count_stmt = count_stmt.where(ContentGenerationCandidate.content_type == content_type)
        rows = (
            await self.db.execute(
                stmt.order_by(ContentGenerationCandidate.created_at.desc()).offset(skip).limit(limit)
            )
        ).scalars().all()
        filtered = []
        for c in rows:
            payload = c.payload_json or {}
            if skill and skill.lower() not in [s.lower() for s in payload.get("skills") or []]:
                continue
            if role and role.lower() not in [r.lower() for r in payload.get("roles") or []]:
                continue
            if company and company.lower() not in [x.lower() for x in payload.get("companies") or []]:
                continue
            if difficulty and str(payload.get("difficulty", "")).lower() != difficulty.lower():
                continue
            filtered.append(c)
        total = int(await self.db.scalar(count_stmt) or 0)
        return ContentCandidateListResponse(items=[_candidate_schema(c) for c in filtered], total=total)

    async def update_candidate(self, candidate_id: UUID, payload: ContentCandidateUpdate) -> ContentCandidateAdmin:
        candidate = await self._get_candidate(candidate_id)
        if candidate.review_status != ContentReviewStatus.PENDING:
            raise AppException("Only pending candidates can be edited", status_code=400)
        data = dict(candidate.payload_json or {})
        updates = payload.model_dump(exclude_unset=True)
        data.update({k: v for k, v in updates.items() if v is not None})
        validation = await validate_question_payload(self.db, data)
        candidate.payload_json = data
        candidate.content_hash = validation.content_hash or candidate.content_hash
        candidate.validation_status = (
            ContentValidationStatus.VALID if validation.ok else ContentValidationStatus.INVALID
        )
        candidate.validation_errors = validation.as_json()
        await self.db.commit()
        await self.db.refresh(candidate)
        return _candidate_schema(candidate)

    async def approve_candidate(self, candidate_id: UUID, reviewer_id: UUID | None) -> ContentCandidateAdmin:
        candidate = await self._get_candidate(candidate_id)
        return await self._approve(candidate, reviewer_id)

    async def reject_candidate(self, candidate_id: UUID) -> ContentCandidateAdmin:
        candidate = await self._get_candidate(candidate_id)
        if candidate.review_status != ContentReviewStatus.PENDING:
            raise AppException("Candidate is not pending", status_code=400)
        candidate.review_status = ContentReviewStatus.REJECTED
        batch = await self.db.get(ContentGenerationBatch, candidate.batch_id)
        if batch:
            batch.rejected_count = (batch.rejected_count or 0) + 1
        await self.db.commit()
        await self.db.refresh(candidate)
        return _candidate_schema(candidate)

    async def bulk_approve(self, ids: list[UUID], reviewer_id: UUID | None) -> dict:
        approved = 0
        errors: list[str] = []
        for cid in ids:
            try:
                candidate = await self._get_candidate(cid)
                await self._approve(candidate, reviewer_id, commit=False)
                approved += 1
            except AppException as exc:
                errors.append(f"{cid}: {exc.message}")
        await self.db.commit()
        return {"approved": approved, "errors": errors}

    async def _approve(
        self,
        candidate: ContentGenerationCandidate,
        reviewer_id: UUID | None,
        *,
        commit: bool = True,
    ) -> ContentCandidateAdmin:
        if candidate.review_status != ContentReviewStatus.PENDING:
            raise AppException("Candidate is not pending", status_code=400)
        validation = await validate_question_payload(self.db, candidate.payload_json)
        if not validation.ok:
            candidate.validation_status = ContentValidationStatus.INVALID
            candidate.validation_errors = validation.as_json()
            if commit:
                await self.db.commit()
            raise AppException("; ".join(validation.errors), status_code=400)
        question = await publish_validated_question(
            self.db,
            candidate.payload_json,
            validation=validation,
            reviewer_id=reviewer_id,
        )
        candidate.review_status = ContentReviewStatus.APPROVED
        candidate.validation_status = ContentValidationStatus.VALID
        candidate.published_question_id = question.id
        batch = await self.db.get(ContentGenerationBatch, candidate.batch_id)
        if batch:
            batch.accepted_count = (batch.accepted_count or 0) + 1
        if commit:
            await self.db.commit()
            await self.db.refresh(candidate)
        return _candidate_schema(candidate)

    async def _get_candidate(self, candidate_id: UUID) -> ContentGenerationCandidate:
        candidate = await self.db.get(ContentGenerationCandidate, candidate_id)
        if candidate is None:
            raise AppException("Candidate not found", status_code=404)
        return candidate
