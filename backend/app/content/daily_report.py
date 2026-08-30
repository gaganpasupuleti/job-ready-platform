"""python -m app.content.daily_report"""

from __future__ import annotations

import asyncio
import json

from app.content.reports import daily_report
from app.db.session import AsyncSessionLocal, engine


async def _run() -> None:
    async with AsyncSessionLocal() as session:
        report = await daily_report(session)
    print(json.dumps(report, indent=2, default=str))


def main() -> None:
    asyncio.run(_run())
    asyncio.run(engine.dispose())


if __name__ == "__main__":
    main()
