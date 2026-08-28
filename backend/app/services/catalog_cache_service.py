import json
import logging

from app.core.config import settings
from app.schemas.practice import CatalogResponse
from app.utils.redis import get_redis

logger = logging.getLogger(__name__)


class CatalogCacheService:
    async def get_cached_catalog(self) -> CatalogResponse | None:
        try:
            redis = await get_redis()
            cached = await redis.get(settings.practice_catalog_cache_key)
            if not cached:
                return None
            return CatalogResponse.model_validate(json.loads(cached))
        except Exception:
            logger.warning("Redis unavailable — skipping catalog cache read")
            return None

    async def set_cached_catalog(self, catalog: CatalogResponse) -> None:
        try:
            redis = await get_redis()
            await redis.set(
                settings.practice_catalog_cache_key,
                catalog.model_dump_json(),
                ex=settings.practice_catalog_cache_ttl_seconds,
            )
        except Exception:
            logger.warning("Redis unavailable — skipping catalog cache write")

    async def invalidate(self) -> None:
        try:
            redis = await get_redis()
            await redis.delete(settings.practice_catalog_cache_key)
        except Exception:
            logger.warning("Redis unavailable — skipping catalog cache invalidation")
