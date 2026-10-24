"""Provision AUTH-01 pair users when public registration is closed (test DB only)."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.models.enums import UserRole  # noqa: E402
from app.seed.e2e import _ensure_user, _env_allows_seed  # noqa: E402


async def main() -> None:
    if not _env_allows_seed():
        raise SystemExit("Refusing to provision AUTH-01 users outside dev/test (set E2E_ALLOW_SEED=1).")

    parser = argparse.ArgumentParser()
    parser.add_argument("--suffix", required=True, help="Unique suffix for emails/usernames")
    args = parser.parse_args()
    suffix = args.suffix.strip()
    password = "E2eStudent123!"

    await _ensure_user(
        email=f"e2e.cache.a.{suffix}@jobready.dev",
        username=f"e2ecachea{suffix}",
        password=password,
        role=UserRole.STUDENT,
        full_name=f"Cache User A {suffix}",
    )
    await _ensure_user(
        email=f"e2e.cache.b.{suffix}@jobready.dev",
        username=f"e2ecacheb{suffix}",
        password=password,
        role=UserRole.STUDENT,
        full_name="Cache User B",
    )
    print(
        {
            "a": f"e2e.cache.a.{suffix}@jobready.dev",
            "b": f"e2e.cache.b.{suffix}@jobready.dev",
        }
    )


if __name__ == "__main__":
    asyncio.run(main())
