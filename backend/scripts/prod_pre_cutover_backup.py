"""Pre-cutover production metadata backup. Run via: railway run --service backend -- python scripts/prod_pre_cutover_backup.py"""
from __future__ import annotations

import asyncio
import json
import os
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

TABLES = [
    "alembic_version",
    "users",
    "domains",
    "categories",
    "topics",
    "questions",
    "skills",
    "jobs",
    "job_applications",
    "saved_jobs",
    "coding_problems",
    "sql_problems",
    "interview_questions",
    "interview_sessions",
    "role_skill_requirements",
    "mistake_items",
    "user_role_readiness_snapshots",
]


async def main() -> None:
    url = os.environ["DATABASE_URL"]
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    engine = create_async_engine(url, pool_pre_ping=True)
    data: dict = {
        "taken_at": datetime.now(UTC).isoformat(),
        "app_env": os.getenv("APP_ENV"),
        "judge0_enabled": os.getenv("JUDGE0_ENABLED"),
        "sql_execution_enabled": os.getenv("SQL_EXECUTION_ENABLED"),
        "counts": {},
        "alembic_version": None,
    }
    async with engine.connect() as conn:
        try:
            data["alembic_version"] = (
                await conn.execute(text("SELECT version_num FROM alembic_version"))
            ).scalar()
        except Exception as exc:  # noqa: BLE001
            data["alembic_version_error"] = type(exc).__name__
        for table in TABLES:
            try:
                data["counts"][table] = (
                    await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                ).scalar_one()
            except Exception:  # noqa: BLE001
                data["counts"][table] = None
    await engine.dispose()

    out_dir = Path(__file__).resolve().parents[2] / "backups"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"pre_cutover_{stamp}.json"
    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(json.dumps(data, indent=2))
    print(f"WROTE {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
