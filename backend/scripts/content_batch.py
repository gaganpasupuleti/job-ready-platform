"""Validate or apply a local learning-studio content batch.

Dry-run (no database writes):
  python scripts/content_batch.py --batch content/batches/2026-09-19-saturday-001

Local apply:
  python scripts/content_batch.py --batch content/batches/2026-09-19-saturday-001 --apply --target local
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.content.studio_batch import apply_batch, load_batch, plan
from app.db.session import AsyncSessionLocal
from app.models.studio import ContentBatchItem


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--target", default="local")
    args = parser.parse_args()
    batch = load_batch(Path(args.batch))

    async def _stored() -> dict:
        async with AsyncSessionLocal() as db:
            rows = (await db.execute(select(ContentBatchItem))).scalars().all()
            return {row.item_key: row for row in rows}

    if not args.apply:
        stored = {}
        try:
            stored = asyncio.run(_stored())
        except Exception:
            stored = {}
        print(json.dumps(plan(batch, stored), indent=2, default=str))
        return
    if args.target != "local":
        raise SystemExit("Only --target local is accepted. This command does not publish production.")

    async def _run() -> dict:
        async with AsyncSessionLocal() as db:
            return await apply_batch(db, Path(args.batch), allow_remote=False)

    result = asyncio.run(_run())
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
