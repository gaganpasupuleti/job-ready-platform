"""Limited Company Prep surface using existing companies + interview packs + paths."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.interview import InterviewPack
from app.models.learn import PracticePath
from app.models.tagging import Company
from app.schemas.interview import InterviewPackPublic
from app.schemas.interview_session import CompanyPrepCard, CompanyPrepDetail

DISCLAIMER = (
    "Preparation content is based on commonly relevant skills and hiring patterns. "
    "It is not affiliated with or endorsed by the listed companies."
)

FEATURED = ["tcs", "accenture", "infosys", "cognizant", "capgemini", "deloitte"]


class CompanyPrepService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_companies(self) -> list[CompanyPrepCard]:
        cards: list[CompanyPrepCard] = []
        for slug in FEATURED:
            company = (
                await self.db.execute(select(Company).where(Company.slug == slug))
            ).scalar_one_or_none()
            if not company:
                continue
            pack_count = (
                await self.db.execute(
                    select(func.count())
                    .select_from(InterviewPack)
                    .where(
                        InterviewPack.target_company_id == company.id,
                        InterviewPack.is_active.is_(True),
                    )
                )
            ).scalar_one()
            paths = (
                await self.db.execute(
                    select(PracticePath.slug).where(
                        PracticePath.external_route.ilike(f"%company={slug}%")
                        | PracticePath.external_route.ilike(f"%/company-prep/{slug}%")
                    )
                )
            ).scalars().all()
            cards.append(
                CompanyPrepCard(
                    slug=company.slug,
                    name=company.name,
                    interview_pack_count=int(pack_count or 0),
                    practice_path_slugs=list(paths),
                )
            )
        return cards

    async def detail(self, slug: str) -> CompanyPrepDetail:
        company = (
            await self.db.execute(select(Company).where(Company.slug == slug))
        ).scalar_one_or_none()
        if not company:
            raise AppException("Company not found", status_code=404)
        packs = (
            await self.db.execute(
                select(InterviewPack).where(
                    InterviewPack.target_company_id == company.id,
                    InterviewPack.is_active.is_(True),
                )
            )
        ).scalars().all()
        pack_public: list[InterviewPackPublic] = []
        for p in packs:
            pack_public.append(
                InterviewPackPublic(
                    id=p.id,
                    slug=p.slug,
                    title=p.title,
                    description=p.description,
                    experience_level=p.experience_level,
                    question_count=0,
                )
            )
        paths = (
            await self.db.execute(
                select(PracticePath).where(
                    PracticePath.external_route.ilike(f"%{slug}%")
                    | PracticePath.title.ilike(f"%{company.name}%")
                )
            )
        ).scalars().all()
        return CompanyPrepDetail(
            slug=company.slug,
            name=company.name,
            disclaimer=DISCLAIMER,
            skills=[],
            packs=pack_public,
            practice_paths=[
                {"slug": p.slug, "title": p.title, "href": p.external_route or f"/practice/paths/{p.slug}"}
                for p in paths
            ],
        )
