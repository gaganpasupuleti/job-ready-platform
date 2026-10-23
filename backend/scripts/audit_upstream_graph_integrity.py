"""Audit roadmap.sh graphs for dangling edges and duplicate edge IDs.

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
from app.services.official_roadmap_service import (  # noqa: E402
    _GRAPH_FETCH_SLUG_ALIASES,
    _validate_graph_payload,
)


def _analyze_raw(payload: dict) -> dict:
    nodes = payload.get("nodes") or []
    edges = payload.get("edges") or []
    node_ids = {n.get("id") for n in nodes if isinstance(n, dict)}
    node_by_id = {n["id"]: n for n in nodes if isinstance(n, dict) and isinstance(n.get("id"), str)}
    removed: list[dict] = []
    dup_ids: list[str] = []
    seen: set[str] = set()
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        eid = edge.get("id")
        if isinstance(eid, str):
            if eid in seen:
                dup_ids.append(eid)
            seen.add(eid)
        source, target = edge.get("source"), edge.get("target")
        missing = [
            endpoint
            for endpoint in (source, target)
            if isinstance(endpoint, str) and endpoint not in node_ids
        ]
        if missing and isinstance(eid, str):
            removed.append(
                {
                    "id": eid,
                    "source": source,
                    "target": target,
                    "missing_endpoints": missing,
                    "source_node_type": node_by_id.get(source, {}).get("type") if source in node_ids else None,
                    "target_node_type": None,
                }
            )
    return {
        "node_count": len(nodes),
        "edge_count_original": len(edges),
        "dangling_edge_count": len(removed),
        "duplicate_edge_ids": sorted(set(dup_ids)),
        "removed_edges": removed,
    }


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
                raw = _analyze_raw(payload)
                row.update(raw)
                try:
                    validated = _validate_graph_payload(payload, source=url)
                    integrity = validated.get("integrity", {})
                    row["outcome"] = integrity.get("classification", "unknown")
                    row["edge_count_retained"] = integrity.get("edge_count_retained")
                    row["integrity"] = integrity
                    row["upstream_defect"] = (
                        raw["dangling_edge_count"] > 0 or len(raw["duplicate_edge_ids"]) > 0
                    )
                    row["normalization_bug"] = False
                except AppException as exc:
                    row["outcome"] = "failed"
                    row["error"] = str(exc)
                    row["upstream_defect"] = len(raw["duplicate_edge_ids"]) > 0 or raw["dangling_edge_count"] > 0
            except httpx.HTTPError as exc:
                row["error"] = str(exc)
            report_rows.append(row)
            await asyncio.sleep(0.35)

    sanitized = [r for r in report_rows if r.get("outcome") == "sanitized"]
    clean = [r for r in report_rows if r.get("outcome") == "clean"]
    failed = [r for r in report_rows if r.get("outcome") == "failed"]
    unavailable = [r for r in report_rows if r.get("outcome") == "unavailable"]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "generated_at": __import__("datetime").datetime.now(__import__("datetime").UTC).isoformat(),
                "source_version": settings.roadmap_graph_fetch_url,
                "totals": {
                    "slug_total": len(slugs),
                    "clean": len(clean),
                    "sanitized": len(sanitized),
                    "failed": len(failed),
                    "unavailable": len(unavailable),
                },
                "sanitized_slugs": [r["slug"] for r in sanitized],
                "rows": report_rows,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"wrote {OUT}")
    print(json.dumps({"clean": len(clean), "sanitized": len(sanitized), "failed": len(failed), "unavailable": len(unavailable)}))


if __name__ == "__main__":
    asyncio.run(main())
