"""python -m app.content.gaps"""

from __future__ import annotations

import asyncio
import json

from app.content.reports import gap_report
from app.db.session import AsyncSessionLocal, engine


async def _run() -> None:
    async with AsyncSessionLocal() as session:
        report = await gap_report(session)
    print(json.dumps(report, indent=2, default=str))


def main() -> None:
    asyncio.run(_run())
    asyncio.run(engine.dispose())


if __name__ == "__main__":
    main()
