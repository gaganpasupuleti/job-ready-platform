import json
from pathlib import Path

from app.core.exceptions import AppException
from app.services.official_roadmap_service import (
    _load_catalog_file,
    _validate_graph_payload,
    list_official_roadmaps,
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


def test_validate_graph_payload_requires_edges():
    try:
        _validate_graph_payload({"nodes": [{"id": "a", "position": {"x": 0, "y": 0}}]})
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
