import json
from pathlib import Path

from app.core.exceptions import AppException
from app.services.official_roadmap_service import (
    _load_catalog_file,
    _validate_graph_payload,
    list_official_roadmaps,
)
from app.services.roadmap_graph_normalization import (
    detect_duplicate_edge_ids,
    normalize_duplicate_edge_ids,
    normalize_upstream_graph,
)


def test_bundled_catalog_has_many_entries():
    rows = _load_catalog_file()
    assert len(rows) >= 90


def test_catalog_slugs_are_valid():
    for row in _load_catalog_file():
        slug = row["family_slug"]
        assert slug
        assert " " not in slug
        assert slug.islower() or slug.replace("-", "").isalnum()


def test_official_data_engineer_not_legacy_draft_row():
    """Bundled catalog includes official data-engineer; linked draft stays on /assembly only."""
    rows = list_official_roadmaps()
    official_de = next((r for r in rows if r["family_slug"] == "data-engineer"), None)
    assert official_de is not None
    assert official_de.get("source") == "official"
    assert official_de.get("preview_only") is False
    assert official_de.get("student_eligible") is True
    assert not any(r.get("source") == "legacy-draft" for r in rows)


def _two_node_graph():
    return [
        {"id": "a", "position": {"x": 0, "y": 0}},
        {"id": "b", "position": {"x": 1, "y": 1}},
    ]


def test_edgeless_graph_supported():
    served, integrity = normalize_upstream_graph(
        {"nodes": _two_node_graph(), "edges": []},
        source="https://roadmap.sh/code-review.json",
    )
    assert integrity["classification"] == "edgeless"
    assert served["edges"] == []


def test_validate_graph_payload_drops_dangling_edges():
    payload = _validate_graph_payload(
        {
            "nodes": _two_node_graph(),
            "edges": [
                {"id": "e1", "source": "a", "target": "b"},
                {"id": "e2", "source": "a", "target": "missing"},
            ],
        },
        source="https://roadmap.sh/example.json",
    )
    assert len(payload["edges"]) == 1
    assert payload["integrity"]["classification"] == "sanitized"
    assert payload["integrity"]["edge_count_original"] == 2
    assert payload["integrity"]["edge_count_retained"] == 1


def test_duplicate_id_distinct_endpoints_are_remapped():
    edges = [
        {"id": "e1", "source": "a", "target": "b"},
        {"id": "e1", "source": "a", "target": "missing"},
    ]
    assert detect_duplicate_edge_ids(edges) == ["e1"]
    normalized, changes = normalize_duplicate_edge_ids(edges)
    ids = [edge["id"] for edge in normalized]
    assert "e1" in ids
    assert "e1__jobready-dup1" in ids
    assert any(change["kind"] == "duplicate_id_remapped" for change in changes)


def test_duplicate_id_order_permutations_produce_same_ids():
    base = [
        {"id": "e1", "source": "a", "target": "b", "sourceHandle": "z2", "targetHandle": "y1"},
        {"id": "e1", "source": "a", "target": "c", "sourceHandle": "z2", "targetHandle": "y1"},
    ]
    reversed_edges = list(reversed(base))
    a_ids = [e["id"] for e in normalize_duplicate_edge_ids(base)[0]]
    b_ids = [e["id"] for e in normalize_duplicate_edge_ids(reversed_edges)[0]]
    assert sorted(a_ids) == sorted(b_ids)


def test_rejects_whitespace_node_id():
    try:
        normalize_upstream_graph(
            {"nodes": [{"id": "   ", "position": {"x": 0, "y": 0}}], "edges": []},
            source="https://roadmap.sh/x.json",
        )
        assert False, "expected AppException"
    except AppException:
        pass


def test_rejects_boolean_coordinates():
    try:
        normalize_upstream_graph(
            {"nodes": [{"id": "a", "position": {"x": True, "y": 0}}], "edges": []},
            source="https://roadmap.sh/x.json",
        )
        assert False, "expected AppException"
    except AppException:
        pass


def test_catalog_file_matches_frontend_bundle():
    backend_path = Path(__file__).resolve().parents[1] / "app" / "data" / "official-roadmap-catalog.json"
    frontend_path = (
        Path(__file__).resolve().parents[2]
        / "frontend"
        / "public"
        / "official-roadmaps-index.json"
    )
    assert backend_path.is_file()
    assert frontend_path.is_file()
    backend_slugs = {r["family_slug"] for r in json.loads(backend_path.read_text(encoding="utf-8"))["roadmaps"]}
    frontend_slugs = {r["family_slug"] for r in json.loads(frontend_path.read_text(encoding="utf-8"))["roadmaps"]}
    assert backend_slugs == frontend_slugs
