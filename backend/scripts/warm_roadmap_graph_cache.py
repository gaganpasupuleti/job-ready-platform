"""Fetch and cache official roadmap graphs (requires network). Run from backend root:
  python -m scripts.warm_roadmap_graph_cache
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "app" / "data" / "official-roadmap-catalog.json"
sys.path.insert(0, str(ROOT))

from app.core.config import settings  # noqa: E402
from app.services.official_roadmap_service import fetch_official_graph  # noqa: E402


async def main() -> None:
    rows = json.loads(CATALOG.read_text(encoding="utf-8")).get("roadmaps", [])
    slugs = [str(r["family_slug"]) for r in rows if r.get("family_slug")]
    ok = fail = 0
    for slug in slugs:
        try:
            await fetch_official_graph(slug)
            ok += 1
            print(f"ok {slug}")
        except Exception as exc:  # noqa: BLE001
            fail += 1
            print(f"fail {slug}: {exc}")
    print(f"done ok={ok} fail={fail} cache_dir={settings.roadmap_graph_cache_dir or 'default'}")


if __name__ == "__main__":
    asyncio.run(main())
