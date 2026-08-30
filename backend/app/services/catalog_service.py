from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.taxonomy import Category, Topic
from app.repositories.question_repository import TaxonomyRepository
from app.schemas.admin import TaxonomyTopicCreate, TaxonomyTopicUpdate
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

    async def create_topic(self, payload: TaxonomyTopicCreate) -> dict:
        category = await self.taxonomy.get_category(payload.category_id)
        if category is None:
            raise AppException("Category not found", status_code=404)
        existing = await self.taxonomy.get_topic_by_slug(payload.category_id, payload.slug)
        if existing is not None:
            raise AppException("Topic slug already exists in this category", status_code=400)
        topic = Topic(
            category_id=payload.category_id,
            name=payload.name,
            slug=payload.slug,
            description=payload.description,
            is_active=payload.is_active,
        )
        self.taxonomy.db.add(topic)
        await self.taxonomy.db.commit()
        await self.taxonomy.db.refresh(topic)
        await self.invalidate_cache()
        return {"id": str(topic.id), "name": topic.name, "slug": topic.slug, "is_active": topic.is_active}

    async def update_topic(self, topic_id, payload: TaxonomyTopicUpdate) -> dict:
        topic = await self.taxonomy.get_topic(topic_id)
        if topic is None:
            raise AppException("Topic not found", status_code=404)
        if payload.name is not None:
            topic.name = payload.name
        if payload.slug is not None:
            topic.slug = payload.slug
        if payload.description is not None:
            topic.description = payload.description
        if payload.is_active is not None:
            topic.is_active = payload.is_active
        await self.taxonomy.db.commit()
        await self.invalidate_cache()
        return {"id": str(topic.id), "name": topic.name, "slug": topic.slug, "is_active": topic.is_active}
