"""One-off semantic inspection for PR24 special-case official roadmap graphs."""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.roadmap_graph_normalization import normalize_upstream_graph

SPECIAL = [
    "code-review",
    "data-analyst",
    "ux-design",
    "design-system",
    "django",
    "javascript",
    "golang",
    "mongodb",
]


def node_label(nodes: list, node_id: str) -> str | None:
    for n in nodes:
        if n.get("id") == node_id:
            data = n.get("data") or {}
            return data.get("label") or n.get("type")
    return None


def node_type(nodes: list, node_id: str) -> str | None:
    for n in nodes:
        if n.get("id") == node_id:
            return n.get("type")
    return None


def incoming_topic_edges(edges: list, target: str, nodes: list) -> list[dict]:
    topic_types = {"topic", "subtopic"}
    out = []
    for e in edges:
        if e.get("target") != target:
            continue
        src = e.get("source")
        t = node_type(nodes, src)
        if t in topic_types:
            out.append(
                {
                    "id": e.get("id"),
                    "source": src,
                    "source_label": node_label(nodes, src),
                    "source_type": t,
                }
            )
    return out


def analyze_dangling(slug: str, raw: dict, integrity: dict) -> dict:
    served_edges = [e for e in raw.get("edges", []) if isinstance(e, dict)]
    _, norm_integrity = normalize_upstream_graph(raw, source=f"https://roadmap.sh/{slug}.json")
    removed = norm_integrity.get("removed_edges") or []
    findings = []
    for rem in removed:
        tgt = rem.get("target")
        nodes = raw.get("nodes") or []
        served_after, _ = normalize_upstream_graph(raw, source=f"https://roadmap.sh/{slug}.json")
        retained = served_after.get("edges") or []
        alt = incoming_topic_edges(retained, tgt, served_after.get("nodes") or nodes)
        findings.append(
            {
                "removed_edge_id": rem.get("id"),
                "missing_source": rem.get("missing_endpoints"),
                "target_id": tgt,
                "target_label": node_label(nodes, tgt),
                "target_type": node_type(nodes, tgt),
                "incoming_topic_edges_after_sanitize": alt,
                "semantic_verdict": (
                    "uncertain"
                    if len(alt) == 0
                    else "alternate_topic_incoming_exists_but_removed_link_semantics_unknown"
                ),
            }
        )
    return {"slug": slug, "classification": integrity.get("classification"), "dangling": findings}


def main() -> None:
    report = []
    for slug in SPECIAL:
        url = f"https://roadmap.sh/{slug}.json"
        with urllib.request.urlopen(url, timeout=60) as resp:
            raw = json.load(resp)
        served, integrity = normalize_upstream_graph(raw, source=url)
        entry = {
            "slug": slug,
            "classification": integrity.get("classification"),
            "node_count": integrity.get("node_count"),
            "edge_count_original": integrity.get("edge_count_original"),
            "edge_count_retained": integrity.get("edge_count_retained"),
            "duplicate_edge_ids_original": integrity.get("duplicate_edge_ids_original"),
            "edge_normalizations": integrity.get("edge_normalizations"),
            "removed_edges": integrity.get("removed_edges"),
        }
        if integrity.get("classification") == "edgeless":
            entry["note"] = "Zero-edge layout; topics are independent nodes (no graph path to verify)."
        if integrity.get("removed_edges"):
            entry["semantic_review"] = analyze_dangling(slug, raw, integrity)
        report.append(entry)
    out = Path(__file__).resolve().parents[2] / "docs" / "ci-evidence" / "special-roadmap-maps-1ebbd48.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"candidate_sha": "1ebbd48", "maps": report}, indent=2), encoding="utf-8")
    print(json.dumps({"written": str(out), "slugs": len(report)}))


if __name__ == "__main__":
    main()
