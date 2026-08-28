from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.question_repository import TaxonomyRepository
from app.schemas.practice import (
    CatalogResponse,
    CategoryBrief,
    DomainBrief,
    SubtopicBrief,
    TopicBrief,
)
from app.services.catalog_cache_service import CatalogCacheService


class CatalogService:
    def __init__(self, db: AsyncSession):
        self.taxonomy = TaxonomyRepository(db)
        self.cache = CatalogCacheService()

    async def get_catalog(self, *, use_cache: bool = True) -> CatalogResponse:
        if use_cache:
            cached = await self.cache.get_cached_catalog()
            if cached:
                return cached

        domains = await self.taxonomy.get_full_catalog()
        response = CatalogResponse(
            domains=[
                DomainBrief(
                    id=domain.id,
                    name=domain.name,
                    slug=domain.slug,
                    categories=[
                        CategoryBrief(
                            id=category.id,
                            name=category.name,
                            slug=category.slug,
                            topics=[
                                TopicBrief(
                                    id=topic.id,
                                    name=topic.name,
                                    slug=topic.slug,
                                    subtopics=[
                                        SubtopicBrief(
                                            id=subtopic.id,
                                            name=subtopic.name,
                                            slug=subtopic.slug,
                                        )
                                        for subtopic in topic.subtopics
                                        if subtopic.is_active
                                    ],
                                )
                                for topic in category.topics
                                if topic.is_active
                            ],
                        )
                        for category in domain.categories
                        if category.is_active
                    ],
                )
                for domain in domains
            ]
        )
        await self.cache.set_cached_catalog(response)
        return response

    async def invalidate_cache(self) -> None:
        await self.cache.invalidate()
