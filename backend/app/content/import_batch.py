"""python -m app.content.import_batch <file> [--approve]"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from app.content.importer import import_questions_file, summarize_import
from app.db.session import AsyncSessionLocal, engine


async def _run(path: Path, approve: bool) -> int:
    async with AsyncSessionLocal() as session:
        batch = await import_questions_file(session, path, approve=approve)
    print(json.dumps(summarize_import(batch), indent=2))
    if not approve:
        print("Imported to staging only. Use admin review or --approve to publish.")
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Import generated interview JSON into staging")
    parser.add_argument("file", type=Path)
    parser.add_argument(
        "--approve",
        action="store_true",
        help="Publish valid items immediately (local/admin only; not for unattended production)",
    )
    args = parser.parse_args(argv)
    if not args.file.exists():
        print(f"File not found: {args.file}", file=sys.stderr)
        raise SystemExit(2)
    code = asyncio.run(_run(args.file, args.approve))
    asyncio.run(engine.dispose())
    raise SystemExit(code)


if __name__ == "__main__":
    main()
