"""Create E2E users + manifest without re-running the full catalog seed.

Use when content is already present:

  python -m app.seed.e2e_users [manifest_path]
"""

from __future__ import annotations

import asyncio
import json
import os
import sys

from app.db.session import engine
from app.models.enums import UserRole
from app.seed.e2e import (
    E2E_STUDENT_EMAIL,
    E2E_STUDENT_PASSWORD,
    E2E_STUDENT_USERNAME,
    _ensure_user,
    _env_allows_seed,
    build_manifest,
)


async def _run(path: str | None) -> dict:
    await _ensure_user(
        email=E2E_STUDENT_EMAIL,
        username=E2E_STUDENT_USERNAME,
        password=E2E_STUDENT_PASSWORD,
        role=UserRole.STUDENT,
        full_name="E2E Student",
    )
    manifest = await build_manifest()
    if path:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=2)
        print(f"Wrote {path}")
    await engine.dispose()
    return manifest


def main() -> None:
    if not _env_allows_seed():
        raise SystemExit("Refusing E2E user seed outside development/test.")
    path = sys.argv[1] if len(sys.argv) > 1 else os.getenv("E2E_MANIFEST_PATH")
    manifest = asyncio.run(_run(path))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
