"""Backfill skill evidence snapshots and mistake book from historical activity."""

from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.services.mistake_service import MistakeService
from app.services.readiness_service import ReadinessService


async def backfill_user(user_id) -> dict:
    async with AsyncSessionLocal() as session:
        mistakes = MistakeService(session)
        readiness = ReadinessService(session)
        user = await session.get(User, user_id)
        if user is None:
            return {"mistakes": 0, "snapshot": False}
        m_count = await mistakes.backfill_user(user.id)
        overview = await readiness.refresh_snapshot(user)
        return {
            "mistakes": m_count,
            "snapshot": overview.get("has_minimum_evidence", False),
        }


async def backfill_all() -> None:
    async with AsyncSessionLocal() as session:
        users = (await session.execute(select(User.id))).scalars().all()
    for uid in users:
        result = await backfill_user(uid)
        print(f"user {uid}: {result}")


def main() -> None:
    asyncio.run(backfill_all())


if __name__ == "__main__":
    main()
