"""CLI: python -m app.jobs.import_csv path/to/jobs.csv [--confirm]

Always validates and prints NEW / UPDATE / DUPLICATE / INVALID counts.
Import only runs when --confirm is passed.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from collections import Counter
from pathlib import Path

from app.db.session import AsyncSessionLocal, engine
from app.services.admin_job_service import AdminJobService


async def main(path: str, *, confirm: bool) -> int:
    content = Path(path).read_text(encoding="utf-8-sig")
    async with AsyncSessionLocal() as session:
        svc = AdminJobService(session)
        preview = await svc.validate_csv(content, Path(path).name)
        actions = Counter(row.action for row in preview.rows)
        print("=== IMPORT PREVIEW ===")
        print(f"File: {path}")
        print(f"NEW:        {actions.get('new', 0)}")
        print(f"UPDATE:     {actions.get('update', 0)}")
        print(f"DUPLICATE:  {actions.get('duplicate', 0)}")
        print(f"INVALID:    {actions.get('invalid', 0)}")
        print(
            f"Totals: create={preview.create_count} update={preview.update_count} "
            f"duplicate={preview.duplicate_count} errors={preview.error_count}"
        )
        for row in preview.rows:
            if row.action in {"invalid", "duplicate"} or row.errors:
                err = "; ".join(row.errors) if row.errors else ""
                print(f"  row {row.row_number}: {row.action} | {row.title} @ {row.company} {err}")
        if not confirm:
            print("Dry run only. Re-run with --confirm to import.")
            return 0 if preview.error_count == 0 else 1
        if not preview.run_id:
            print("No run_id — nothing to import.")
            return 1
        result = await svc.confirm_import(preview.run_id, Path(path).name)
        print(
            f"Import {result.status}: created={result.records_created} "
            f"updated={getattr(result, 'records_updated', '?')} failed={result.records_failed}"
        )
        return 0 if result.records_failed == 0 else 1


def cli() -> None:
    parser = argparse.ArgumentParser(description="Validate/import jobs CSV")
    parser.add_argument("csv_file", help="Path to jobs CSV")
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Apply import after preview (default is dry-run)",
    )
    args = parser.parse_args()

    async def _wrapped() -> int:
        try:
            return await main(args.csv_file, confirm=args.confirm)
        finally:
            await engine.dispose()

    raise SystemExit(asyncio.run(_wrapped()))


if __name__ == "__main__":
    cli()
