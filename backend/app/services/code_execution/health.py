"""Cached Judge0 health + language discovery for execution-status."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from app.core.config import settings
from app.services.code_execution.interface import get_code_execution_service
from app.services.code_execution.judge0 import Judge0CodeExecutionService
from app.services.code_execution.languages import list_languages

logger = logging.getLogger(__name__)


@dataclass
class ExecutionHealthSnapshot:
    enabled: bool
    available: bool
    provider: str
    message: str | None = None
    languages: list[dict] = field(default_factory=list)
    checked_at: float = 0.0


_cache: ExecutionHealthSnapshot | None = None


async def get_execution_health(*, force: bool = False) -> ExecutionHealthSnapshot:
    global _cache
    now = time.monotonic()
    ttl = max(5, settings.judge0_health_cache_seconds)
    if (
        not force
        and _cache is not None
        and (now - _cache.checked_at) < ttl
    ):
        return _cache

    enabled = bool(settings.judge0_enabled)
    if not enabled:
        snap = ExecutionHealthSnapshot(
            enabled=False,
            available=False,
            provider="none",
            message="Code execution is currently unavailable.",
            languages=[
                {
                    "id": lang.id,
                    "key": lang.key,
                    "name": lang.name,
                    "available": False,
                }
                for lang in list_languages()
            ],
            checked_at=now,
        )
        _cache = snap
        return snap

    executor = get_code_execution_service()
    available = False
    if isinstance(executor, Judge0CodeExecutionService):
        available = await executor.health_check()
        if available:
            await executor.refresh_languages()
    else:
        available = False

    langs = [
        {
            "id": lang.id,
            "key": lang.key,
            "name": lang.name,
            "available": lang.available and available,
        }
        for lang in list_languages()
    ]
    snap = ExecutionHealthSnapshot(
        enabled=True,
        available=available,
        provider="judge0",
        message=None if available else "Code execution is currently unavailable.",
        languages=langs,
        checked_at=now,
    )
    _cache = snap
    return snap


def clear_execution_health_cache() -> None:
    global _cache
    _cache = None
