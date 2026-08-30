"""python -m app.content.validate <file>"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from app.content.validator import validate_file_payload
from app.db.session import AsyncSessionLocal, engine


async def _run(path: Path) -> int:
    data = json.loads(path.read_text(encoding="utf-8"))
    async with AsyncSessionLocal() as session:
        results, _questions = await validate_file_payload(session, data)
    ok = 0
    fail = 0
    for idx, result in enumerate(results, start=1):
        if result.ok:
            ok += 1
            if result.warnings:
                print(f"[{idx}] OK with warnings: {'; '.join(result.warnings)}")
            else:
                print(f"[{idx}] OK hash={result.content_hash[:12] if result.content_hash else ''}")
        else:
            fail += 1
            print(f"[{idx}] INVALID: {'; '.join(result.errors)}")
    print(f"\n{ok} valid, {fail} invalid, {len(results)} total")
    return 1 if fail else 0


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Validate generated interview JSON")
    parser.add_argument("file", type=Path)
    args = parser.parse_args(argv)
    if not args.file.exists():
        print(f"File not found: {args.file}", file=sys.stderr)
        raise SystemExit(2)
    code = asyncio.run(_run(args.file))
    asyncio.run(engine.dispose())
    raise SystemExit(code)


if __name__ == "__main__":
    main()
