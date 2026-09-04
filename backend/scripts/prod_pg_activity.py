"""Inspect pg_stat_activity for production cutover debugging."""
from __future__ import annotations

import asyncio
import os

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


async def main() -> None:
    url = os.environ["DATABASE_URL"]
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    engine = create_async_engine(url)
    async with engine.connect() as conn:
        rows = (
            await conn.execute(
                text(
                    """
                    SELECT pid, state, wait_event_type, wait_event,
                           now() - xact_start AS xact_age,
                           now() - query_start AS query_age,
                           left(query, 160) AS q
                    FROM pg_stat_activity
                    WHERE datname = current_database()
                      AND pid <> pg_backend_pid()
                    ORDER BY xact_start NULLS LAST
                    """
                )
            )
        ).mappings().all()
        for row in rows:
            print(dict(row))
        if not rows:
            print("NO_OTHER_SESSIONS")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
