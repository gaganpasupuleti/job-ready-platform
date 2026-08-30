from __future__ import annotations

import logging

from app.core.config import settings
from app.db.session import engine
from app.schemas.health import DetailedHealthResponse, HealthChecks, HealthResponse
from app.utils.database import check_database_connection
from app.utils.redis import check_redis_connection

logger = logging.getLogger(__name__)


class HealthService:
    SERVICE_NAME = "job-ready-platform-api"

    def get_health(self) -> HealthResponse:
        return HealthResponse(status="ok", service=self.SERVICE_NAME)

    async def get_health_detailed(self) -> DetailedHealthResponse:
        checks = HealthChecks()

        checks.database = "ok" if await check_database_connection(engine) else "error"

        try:
            checks.redis = "ok" if await check_redis_connection() else "unavailable"
        except Exception:
            checks.redis = "unavailable"

        if not settings.sql_execution_enabled:
            checks.sql_sandbox = "disabled"
        else:
            try:
                from app.services.sql_execution.pools import get_runner_pool

                pool = await get_runner_pool()
                async with pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
                checks.sql_sandbox = "ok"
            except Exception:
                logger.debug("SQL sandbox health probe failed", exc_info=True)
                checks.sql_sandbox = "unavailable"

        if not settings.judge0_enabled:
            checks.judge0 = "disabled"
        else:
            try:
                from app.services.code_execution.health import get_execution_health

                health = await get_execution_health()
                available = bool(getattr(health, "available", False))
                checks.judge0 = "ok" if available else "unavailable"
            except Exception:
                checks.judge0 = "unavailable"

        overall = "ok"
        if checks.database == "error":
            overall = "degraded"
        elif checks.sql_sandbox == "unavailable" and settings.sql_execution_enabled:
            overall = "degraded"

        return DetailedHealthResponse(status=overall, service=self.SERVICE_NAME, checks=checks)
