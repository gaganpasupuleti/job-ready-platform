"""Plan, publish, or roll back Visual Learning Phase 1.

This command does not replace `scripts/content_batch.py`. That importer still
refuses every non-local target. This command writes only the six reviewed
lesson rows, and only after a separate authorization gate.

Plan (no writes):
  python scripts/visual_phase1_release.py plan

Publish, after the frontend assets are verified:
  VISUAL_PHASE1_AUTHORIZATION=PUBLISH-2026-10-10-VISUAL-LEARNING-001 ^
  python scripts/visual_phase1_release.py apply ^
    --confirm-database HOST:PORT/DATABASE ^
    --confirm-keys crt-di-tables,crt-logical-patterns,crt-quant-percentages,crt-verbal-meaning,dsa-arrays-strings,dsa-complexity ^
    --backup-out PATH-OUTSIDE-GIT.json

Roll back using the backup written by apply:
  VISUAL_PHASE1_AUTHORIZATION=ROLLBACK-2026-10-10-VISUAL-LEARNING-001 ^
  python scripts/visual_phase1_release.py rollback ^
    --confirm-database HOST:PORT/DATABASE ^
    --confirm-keys crt-di-tables,crt-logical-patterns,crt-quant-percentages,crt-verbal-meaning,dsa-arrays-strings,dsa-complexity ^
    --backup-in PATH-OUTSIDE-GIT.json

DATABASE_URL selects the database. Do not put the URL on the command line.
The command never prints the URL or the authorization value.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.content.visual_phase1_release import prepare_visual_phase1, publish_visual_phase1, rollback_visual_phase1
from app.db.session import AsyncSessionLocal

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.engine.Engine").setLevel(logging.WARNING)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("plan", "apply", "rollback"))
    parser.add_argument("--confirm-database", default="")
    parser.add_argument("--confirm-keys", default="")
    parser.add_argument("--backup-out", default="")
    parser.add_argument("--backup-in", default="")
    args = parser.parse_args()
    authorization = os.environ.get("VISUAL_PHASE1_AUTHORIZATION")

    async def _run() -> dict:
        async with AsyncSessionLocal() as db:
            if args.command == "plan":
                prepared = await prepare_visual_phase1(db)
                await db.rollback()
                return {key: value for key, value in prepared.items() if not key.startswith("_")}
            if args.command == "apply":
                return await publish_visual_phase1(
                    db,
                    authorization=authorization,
                    confirm_database=args.confirm_database,
                    confirm_keys=args.confirm_keys,
                    backup_path=Path(args.backup_out) if args.backup_out else None,
                )
            if not args.backup_in:
                return {"applied": False, "refused": True, "rejected": ["--backup-in is required"]}
            return await rollback_visual_phase1(
                db,
                authorization=authorization,
                confirm_database=args.confirm_database,
                confirm_keys=args.confirm_keys,
                backup_path=Path(args.backup_in),
            )

    result = asyncio.run(_run())
    print(json.dumps(result, indent=2, default=str))
    if result.get("refused") or result.get("rejected"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
