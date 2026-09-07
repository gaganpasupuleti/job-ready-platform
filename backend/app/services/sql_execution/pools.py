"""Separate connection pools for SQL sandbox admin and runner."""

from __future__ import annotations

import asyncio
import logging
from urllib.parse import quote, urlparse, urlunparse

import asyncpg

from app.core.config import settings

logger = logging.getLogger(__name__)

_admin_pool: asyncpg.Pool | None = None
_runner_pool: asyncpg.Pool | None = None
_pool_loop_id: int | None = None


def to_asyncpg_dsn(url: str) -> str:
    parsed = urlparse(url)
    scheme = parsed.scheme
    if scheme.startswith("postgresql+"):
        scheme = "postgresql"
    elif scheme == "postgres":
        scheme = "postgresql"
    return urlunparse((scheme, parsed.netloc, parsed.path, "", parsed.query, ""))


def with_role_password(url: str, user: str, password: str) -> str:
    """Rewrite a DSN to use a different login while keeping host/db."""
    parsed = urlparse(to_asyncpg_dsn(url))
    host = parsed.hostname or "localhost"
    port = f":{parsed.port}" if parsed.port else ""
    auth = f"{quote(user, safe='')}:{quote(password, safe='')}"
    netloc = f"{auth}@{host}{port}"
    return urlunparse(("postgresql", netloc, parsed.path, "", parsed.query, ""))


def _dsn_username(url: str) -> str | None:
    return urlparse(to_asyncpg_dsn(url)).username


def admin_dsn() -> str:
    url = settings.sql_sandbox_admin_database_url or settings.sql_sandbox_database_url
    return to_asyncpg_dsn(url)


def runner_dsn() -> str:
    """Return runner DSN; derive restricted credentials when admin==runner (Railway)."""
    admin = admin_dsn()
    explicit = (
        settings.sql_sandbox_runner_database_url
        or settings.sql_sandbox_database_url
        or ""
    ).strip()

    if explicit:
        explicit_n = to_asyncpg_dsn(explicit)
        # Distinct runner URL (local Docker) — use as-is
        if explicit_n != admin and _dsn_username(explicit_n) != _dsn_username(admin):
            return explicit_n
        # Same DB user as admin → must derive restricted role
        if _dsn_username(explicit_n) == settings.sql_sandbox_runner_role:
            return explicit_n

    return with_role_password(
        admin,
        settings.sql_sandbox_runner_role,
        settings.sql_sandbox_runner_password,
    )


def _drop_pools_for_new_loop() -> None:
    """Drop in-memory pool refs when pytest (or reload) starts a new event loop."""
    global _admin_pool, _runner_pool, _pool_loop_id
    loop_id = id(asyncio.get_running_loop())
    if _pool_loop_id is not None and _pool_loop_id != loop_id:
        _admin_pool = None
        _runner_pool = None
    _pool_loop_id = loop_id


async def get_admin_pool() -> asyncpg.Pool:
    global _admin_pool
    _drop_pools_for_new_loop()
    if _admin_pool is None:
        _admin_pool = await asyncpg.create_pool(
            dsn=admin_dsn(),
            min_size=1,
            max_size=5,
            command_timeout=max(10, settings.sql_query_timeout_ms / 1000 + 5),
        )
        logger.info("SQL sandbox admin pool created")
    return _admin_pool


async def get_runner_pool() -> asyncpg.Pool:
    global _runner_pool
    _drop_pools_for_new_loop()
    if _runner_pool is None:
        _runner_pool = await asyncpg.create_pool(
            dsn=runner_dsn(),
            min_size=1,
            max_size=10,
            command_timeout=max(10, settings.sql_query_timeout_ms / 1000 + 5),
        )
        logger.info("SQL sandbox runner pool created (user=%s)", _dsn_username(runner_dsn()))
    return _runner_pool


async def close_sandbox_pools() -> None:
    global _admin_pool, _runner_pool, _pool_loop_id
    for pool in (_admin_pool, _runner_pool):
        if pool is None:
            continue
        try:
            await pool.close()
        except Exception:
            # Pool may already be bound to a closed event loop (pytest) — drop it.
            logger.debug("SQL sandbox pool close ignored", exc_info=True)
    _admin_pool = None
    _runner_pool = None
    _pool_loop_id = None
