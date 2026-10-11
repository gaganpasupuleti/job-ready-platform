"""Generate or check the content inventory evidence files.

Usage (from backend/):
    python -m app.content.inventory --out ../docs/audits/2026-10-11-content-inventory
    python -m app.content.inventory --out ../docs/audits/2026-10-11-content-inventory --check
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.content.inventory.report import check, render, write
from app.content.inventory.sources import SourceUnavailable, repo_root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", required=True, type=Path, help="evidence directory")
    parser.add_argument(
        "--check", action="store_true", help="fail if committed files differ; write nothing"
    )
    args = parser.parse_args(argv)
    try:
        files = render(repo_root())
    except SourceUnavailable as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    if args.check:
        stale = check(files, args.out)
        for name in stale:
            print(f"stale: {name}", file=sys.stderr)
        return 1 if stale else 0
    write(files, args.out)
    for name in sorted(files):
        print(args.out / name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
