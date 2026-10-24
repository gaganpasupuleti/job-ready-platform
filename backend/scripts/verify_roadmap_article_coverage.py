"""Report topic-node vs markdown file coverage for official roadmaps."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "app" / "data" / "official-roadmap-catalog.json"
CACHE = ROOT / "app" / "data" / "roadmap-cache"

sys.path.insert(0, str(ROOT))
from app.services.official_roadmap_service import _content_root, get_topic_content  # noqa: E402
from app.services.roadmap_graph_normalization import normalize_upstream_graph  # noqa: E402

READABLE = {"topic", "subtopic"}


def main() -> None:
    root = _content_root()
    rows = json.loads(CATALOG.read_text(encoding="utf-8")).get("roadmaps", [])
    report: list[dict] = []
    total_readable = 0
    total_with_file = 0
    for row in rows:
        slug = str(row["family_slug"])
        cache = CACHE / f"{slug}.json"
        if not cache.is_file():
            report.append({"slug": slug, "error": "no graph cache"})
            continue
        envelope = json.loads(cache.read_text(encoding="utf-8"))
        raw = envelope.get("source_payload") or envelope
        served, _ = normalize_upstream_graph(raw, source=f"https://roadmap.sh/{slug}.json")
        nodes = served.get("nodes") or []
        readable = [n for n in nodes if (n.get("type") in READABLE) and n.get("id")]
        hits = 0
        misses: list[str] = []
        for n in readable[:5]:
            nid = n["id"]
            old = (n.get("data") or {}).get("oldId")
            try:
                get_topic_content(slug, nid, old_id=old if isinstance(old, str) else None)
                hits += 1
            except Exception:
                misses.append(nid)
        for n in readable[5:]:
            nid = n["id"]
            old = (n.get("data") or {}).get("oldId")
            content_dir = (root / slug / "content") if root else None
            found = False
            if content_dir and content_dir.is_dir():
                if list(content_dir.glob(f"*@{nid}.md")):
                    found = True
                elif old and list(content_dir.glob(f"*@{old}.md")):
                    found = True
            if found:
                hits += 1
            else:
                misses.append(nid)
        total_readable += len(readable)
        total_with_file += hits
        report.append(
            {
                "slug": slug,
                "readable_nodes": len(readable),
                "resolved_files": hits,
                "missing_files": len(misses),
                "sample_missing": misses[:5],
            }
        )
    out = ROOT.parent / "docs" / "ci-evidence" / "roadmap-article-file-coverage.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "content_root": "backend/app/data/roadmap-syllabus/roadmaps" if root else None,
                "manifest": "backend/app/data/roadmap-syllabus/ROADMAP_SYLLABUS_MANIFEST.json",
                "readable_nodes_total": total_readable,
                "resolved_files_total": total_with_file,
                "slugs": report,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(json.dumps({"out": str(out), "readable": total_readable, "resolved": total_with_file}))


if __name__ == "__main__":
    main()
