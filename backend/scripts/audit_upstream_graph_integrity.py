"""Audit roadmap.sh graphs using the same normalization contract as the API.

Run from backend root:
  python -m scripts.audit_upstream_graph_integrity
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "app" / "data" / "official-roadmap-catalog.json"
OUT = ROOT.parent / "docs" / "roadmap-upstream-graph-integrity.json"

sys.path.insert(0, str(ROOT))

from app.core.config import settings  # noqa: E402
from app.core.exceptions import AppException  # noqa: E402
from app.services.official_roadmap_service import _GRAPH_FETCH_SLUG_ALIASES  # noqa: E402
from app.services.roadmap_graph_normalization import (  # noqa: E402
    detect_duplicate_edge_ids,
    normalize_upstream_graph,
)


async def main() -> None:
    rows = json.loads(CATALOG.read_text(encoding="utf-8")).get("roadmaps", [])
    slugs = [str(r["family_slug"]) for r in rows if r.get("family_slug")]
    report_rows: list[dict] = []
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        for slug in slugs:
            fetch_slug = _GRAPH_FETCH_SLUG_ALIASES.get(slug, slug)
            url = settings.roadmap_graph_fetch_url.format(slug=fetch_slug)
            row: dict = {
                "slug": slug,
                "fetch_slug": fetch_slug,
                "source": url,
                "http_status": None,
                "outcome": "unavailable",
            }
            try:
                response = await client.get(url)
                row["http_status"] = response.status_code
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict):
                    row["outcome"] = "failed"
                    row["error"] = "payload not object"
                    report_rows.append(row)
                    continue
                edges = payload.get("edges") if isinstance(payload.get("edges"), list) else []
                row["duplicate_edge_ids_original"] = detect_duplicate_edge_ids(edges)
                try:
                    _served, integrity = normalize_upstream_graph(payload, source=url)
                    row["outcome"] = integrity.get("classification", "failed")
                    row["integrity"] = integrity
                    row["semantic_path_verified"] = False
                    if integrity.get("classification") == "sanitized":
                        row["upstream_defect"] = True
                        row["requires_manual_review"] = True
                    elif integrity.get("classification") == "edgeless":
                        row["upstream_defect"] = False
                        row["requires_manual_review"] = True
                    else:
                        row["upstream_defect"] = False
                        row["requires_manual_review"] = False
                except AppException as exc:
                    row["outcome"] = "failed"
                    row["error"] = str(exc)
                    row["upstream_defect"] = True
            except httpx.HTTPError as exc:
                row["error"] = str(exc)
            report_rows.append(row)
            await asyncio.sleep(0.35)

    totals = {
        "slug_total": len(slugs),
        "clean": sum(1 for r in report_rows if r.get("outcome") == "clean"),
        "edgeless": sum(1 for r in report_rows if r.get("outcome") == "edgeless"),
        "sanitized": sum(1 for r in report_rows if r.get("outcome") == "sanitized"),
        "failed": sum(1 for r in report_rows if r.get("outcome") == "failed"),
        "unavailable": sum(1 for r in report_rows if r.get("outcome") == "unavailable"),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "generated_at": __import__("datetime").datetime.now(__import__("datetime").UTC).isoformat(),
                "source_version": settings.roadmap_graph_fetch_url,
                "totals": totals,
                "rows": report_rows,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"wrote {OUT}")
    print(json.dumps(totals))


if __name__ == "__main__":
    asyncio.run(main())
