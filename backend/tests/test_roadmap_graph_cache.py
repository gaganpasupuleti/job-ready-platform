import json
from pathlib import Path

from app.services.official_roadmap_service import (
    _cache_envelope_from_fetch,
    _read_graph_cache,
    _write_graph_cache,
)
from app.services.roadmap_graph_normalization import (
    graph_response_from_cache_envelope,
    normalize_upstream_graph,
)


def _sample_upstream():
    return {
        "nodes": [
            {"id": "a", "position": {"x": 0, "y": 0}},
            {"id": "b", "position": {"x": 1, "y": 1}},
        ],
        "edges": [
            {"id": "e1", "source": "a", "target": "b"},
            {"id": "e2", "source": "a", "target": "missing"},
        ],
    }


def test_cache_roundtrip_preserves_sanitized_integrity(tmp_path, monkeypatch):
    slug = "cache-test-slug"
    cache_file = tmp_path / f"{slug}.json"
    monkeypatch.setattr(
        "app.services.official_roadmap_service._graph_cache_path",
        lambda _slug: cache_file,
    )
    monkeypatch.setattr("app.services.official_roadmap_service._cache_is_fresh", lambda _path: True)

    source = "https://roadmap.sh/cache-test-slug.json"
    raw = _sample_upstream()
    served, integrity = normalize_upstream_graph(raw, source=source)
    envelope = _cache_envelope_from_fetch(source, raw, served, integrity)
    _write_graph_cache(slug, envelope)

    loaded = _read_graph_cache(slug)
    assert loaded is not None
    assert loaded["integrity"]["classification"] == "sanitized"
    assert loaded["integrity"]["edge_count_original"] == 2
    assert loaded["integrity"]["edge_count_retained"] == 1
    assert len(loaded["integrity"]["removed_edges"]) == 1

    loaded_again = _read_graph_cache(slug)
    assert loaded_again["integrity"] == loaded["integrity"]


def test_legacy_cache_is_invalidated(tmp_path, monkeypatch):
    slug = "legacy-slug"
    cache_file = tmp_path / f"{slug}.json"
    monkeypatch.setattr(
        "app.services.official_roadmap_service._graph_cache_path",
        lambda _slug: cache_file,
    )
    monkeypatch.setattr("app.services.official_roadmap_service._cache_is_fresh", lambda _path: True)

    legacy = {
        "nodes": [{"id": "a", "position": {"x": 0, "y": 0}}],
        "edges": [],
        "integrity": {"classification": "clean", "removed_edges": []},
    }
    cache_file.write_text(json.dumps(legacy), encoding="utf-8")
    assert _read_graph_cache(slug) is None
    assert not cache_file.is_file()


def test_malformed_cache_envelope_rejected():
    assert graph_response_from_cache_envelope({"cache_version": 1}) is None
    assert graph_response_from_cache_envelope({"cache_version": 2, "source_payload": {}}) is None
    raw = _sample_upstream()
    served, integrity = normalize_upstream_graph(raw, source="https://roadmap.sh/x.json")
    envelope = {
        "cache_version": 2,
        "source": "https://roadmap.sh/x.json",
        "source_payload": raw,
        "served": served,
        "integrity": {**integrity, "classification": "clean"},
    }
    assert graph_response_from_cache_envelope(envelope) is None
