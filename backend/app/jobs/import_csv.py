"""CLI: python -m app.jobs.import_csv path/to/jobs.csv"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from app.db.session import AsyncSessionLocal
from app.services.admin_job_service import AdminJobService


async def main(path: str) -> None:
    content = Path(path).read_text(encoding="utf-8-sig")
    async with AsyncSessionLocal() as session:
        svc = AdminJobService(session)
        preview = await svc.validate_csv(content, Path(path).name)
        print(f"Preview: create={preview.create_count} update={preview.update_count} errors={preview.error_count}")
        if preview.run_id:
            result = await svc.confirm_import(preview.run_id, Path(path).name)
            print(f"Import {result.status}: created={result.records_created} failed={result.records_failed}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m app.jobs.import_csv <csv-file>")
        sys.exit(1)
    asyncio.run(main(sys.argv[1]))
