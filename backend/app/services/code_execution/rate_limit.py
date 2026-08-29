"""Redis-backed rate limits and concurrency guards for coding execution."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

from app.core.config import settings
from app.core.exceptions import AppException
from app.utils.redis import get_redis

logger = logging.getLogger(__name__)


async def enforce_rate_limit(user_id: UUID, *, kind: str) -> None:
    """kind: 'run' | 'submit'. Raises 429 when over limit."""
    limit = (
        settings.coding_runs_per_minute
        if kind == "run"
        else settings.coding_submits_per_minute
    )
    if limit <= 0:
        return
    key = f"coding:rate:{kind}:{user_id}"
    try:
        redis = await get_redis()
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, 60)
        if count > limit:
            raise AppException(
                f"Too many {kind} requests. Please wait a minute and try again.",
                status_code=429,
            )
    except AppException:
        raise
    except Exception:
        logger.warning("Rate limit check failed — allowing request", exc_info=True)


@asynccontextmanager
async def concurrency_slot(user_id: UUID) -> AsyncIterator[None]:
    """Bound concurrent executions per user. Always releases the slot."""
    max_c = settings.coding_max_concurrent_executions_per_user
    key = f"coding:concurrent:{user_id}"
    acquired = False
    if max_c <= 0:
        yield
        return
    try:
        redis = await get_redis()
        count = await redis.incr(key)
        acquired = True
        await redis.expire(key, 120)
        if count > max_c:
            raise AppException(
                "Too many concurrent executions. Wait for the current run to finish.",
                status_code=429,
            )
        yield
    except AppException:
        raise
    except Exception:
        logger.warning("Concurrency guard failed — allowing request", exc_info=True)
        yield
    finally:
        if acquired:
            try:
                redis = await get_redis()
                await redis.decr(key)
            except Exception:
                logger.warning("Failed to release concurrency slot", exc_info=True)
