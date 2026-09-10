"""Bounded login failure throttling.

Prefer Redis for atomic counters across instances. If Redis is unavailable,
falls back to a process-local counter (per-instance only) and logs a warning.
"""

from __future__ import annotations

import logging
import time
from threading import Lock

from app.core.config import settings
from app.core.exceptions import AppException
from app.utils.redis import get_redis

logger = logging.getLogger(__name__)

_memory_lock = Lock()
_memory_failures: dict[str, tuple[int, float]] = {}


def _key(email: str) -> str:
    return f"auth:login_fail:{email.strip().lower()}"


async def assert_login_allowed(email: str) -> None:
    """Raise 429 when the email has exceeded the failure budget in the window."""
    limit = settings.login_max_failures
    window = settings.login_failure_window_seconds
    if limit <= 0:
        return
    key = _key(email)
    try:
        redis = await get_redis()
        count = await redis.get(key)
        if count is not None and int(count) >= limit:
            raise AppException(
                "Too many failed login attempts. Please try again later.",
                status_code=429,
            )
        return
    except AppException:
        raise
    except Exception:
        logger.warning(
            "Login throttle Redis check failed — using process-local fallback",
            exc_info=True,
        )

    now = time.monotonic()
    with _memory_lock:
        count, expires = _memory_failures.get(key, (0, 0.0))
        if expires <= now:
            return
        if count >= limit:
            raise AppException(
                "Too many failed login attempts. Please try again later.",
                status_code=429,
            )


async def record_failed_login(email: str) -> None:
    limit = settings.login_max_failures
    window = settings.login_failure_window_seconds
    if limit <= 0:
        return
    key = _key(email)
    try:
        redis = await get_redis()
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, window)
        return
    except Exception:
        logger.warning(
            "Login throttle Redis record failed — using process-local fallback",
            exc_info=True,
        )

    now = time.monotonic()
    with _memory_lock:
        count, expires = _memory_failures.get(key, (0, 0.0))
        if expires <= now:
            _memory_failures[key] = (1, now + window)
        else:
            _memory_failures[key] = (count + 1, expires)


async def clear_login_failures(email: str) -> None:
    key = _key(email)
    try:
        redis = await get_redis()
        await redis.delete(key)
    except Exception:
        logger.warning(
            "Login throttle Redis clear failed — clearing process-local fallback",
            exc_info=True,
        )
    with _memory_lock:
        _memory_failures.pop(key, None)


def reset_memory_throttle_for_tests() -> None:
    """Test helper — clear process-local buckets."""
    with _memory_lock:
        _memory_failures.clear()
