"""Normalize upstream roadmap.sh graph JSON with provenance-preserving integrity."""

from __future__ import annotations

import copy
import hashlib
import json
import math
from typing import Any

from app.core.exceptions import AppException

_GRAPH_META_KEYS = frozenset({"integrity", "cache_version", "source_payload"})


def _finite_coord(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AppException("Roadmap graph response was invalid", status_code=502)
    number = float(value)
    if not math.isfinite(number):
        raise AppException("Roadmap graph response was invalid", status_code=502)
    return number


def _require_non_empty_id(value: Any, label: str) -> str:
    if not isinstance(value, str):
        raise AppException("Roadmap graph response was invalid", status_code=502)
    stripped = value.strip()
    if not stripped:
        raise AppException("Roadmap graph response was invalid", status_code=502)
    return stripped


def _edge_signature(edge: dict) -> str:
    payload = {
        "source": edge.get("source"),
        "target": edge.get("target"),
        "sourceHandle": edge.get("sourceHandle"),
        "targetHandle": edge.get("targetHandle"),
        "type": edge.get("type"),
        "style": edge.get("style"),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _validate_nodes(nodes: list) -> set[str]:
    if not isinstance(nodes, list) or not nodes:
        raise AppException("Roadmap graph response was invalid", status_code=502)
    node_ids: set[str] = set()
    for node in nodes:
        if not isinstance(node, dict):
            raise AppException("Roadmap graph response was invalid", status_code=502)
        node_id = _require_non_empty_id(node.get("id"), "node")
        if node_id in node_ids:
            raise AppException("Roadmap graph response was invalid", status_code=502)
        node_ids.add(node_id)
        position = node.get("position")
        if not isinstance(position, dict):
            raise AppException("Roadmap graph response was invalid", status_code=502)
        _finite_coord(position.get("x"))
        _finite_coord(position.get("y"))
    return node_ids


def _validate_edge_records(edges: list) -> None:
    if not isinstance(edges, list):
        raise AppException("Roadmap graph response was invalid", status_code=502)
    for edge in edges:
        if not isinstance(edge, dict):
            raise AppException("Roadmap graph response was invalid", status_code=502)
        _require_non_empty_id(edge.get("id"), "edge")
        _require_non_empty_id(edge.get("source"), "edge.source")
        _require_non_empty_id(edge.get("target"), "edge.target")


def detect_duplicate_edge_ids(edges: list) -> list[str]:
    """Return edge IDs that appear more than once in the original edge list."""
    counts: dict[str, int] = {}
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        edge_id = edge.get("id")
        if not isinstance(edge_id, str):
            continue
        counts[edge_id] = counts.get(edge_id, 0) + 1
    return sorted(edge_id for edge_id, count in counts.items() if count > 1)


def normalize_duplicate_edge_ids(edges: list[dict]) -> tuple[list[dict], list[dict]]:
    """Deduplicate identical records; remap conflicting duplicates with deterministic IDs."""
    edge_normalizations: list[dict] = []
    seen_exact: set[str] = set()
    id_use_count: dict[str, int] = {}

    normalized: list[dict] = []
    for edge in edges:
        edge_id = _require_non_empty_id(edge.get("id"), "edge")
        signature = _edge_signature(edge)
        exact_key = f"{edge_id}\0{signature}"
        if exact_key in seen_exact:
            edge_normalizations.append(
                {
                    "kind": "exact_duplicate_dropped",
                    "id": edge_id,
                    "source": edge.get("source"),
                    "target": edge.get("target"),
                }
            )
            continue
        seen_exact.add(exact_key)

        use_index = id_use_count.get(edge_id, 0)
        id_use_count[edge_id] = use_index + 1
        new_id = edge_id
        if use_index > 0:
            new_id = f"{edge_id}__jobready-dup{use_index}"
            edge_normalizations.append(
                {
                    "kind": "duplicate_id_remapped",
                    "from_id": edge_id,
                    "to_id": new_id,
                    "source": edge.get("source"),
                    "target": edge.get("target"),
                }
            )
        normalized.append({**edge, "id": new_id})

    return normalized, edge_normalizations


def drop_dangling_edges(edges: list[dict], node_ids: set[str]) -> tuple[list[dict], list[dict]]:
    kept: list[dict] = []
    removed: list[dict] = []
    for edge in edges:
        source_id = _require_non_empty_id(edge.get("source"), "edge.source")
        target_id = _require_non_empty_id(edge.get("target"), "edge.target")
        missing = [endpoint for endpoint in (source_id, target_id) if endpoint not in node_ids]
        if missing:
            removed.append(
                {
                    "id": edge.get("id"),
                    "source": source_id,
                    "target": target_id,
                    "reason": "endpoint_missing",
                    "missing_endpoints": missing,
                }
            )
            continue
        kept.append(edge)
    return kept, removed


def source_payload_hash(payload: dict) -> str:
    body = {key: value for key, value in payload.items() if key not in _GRAPH_META_KEYS}
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def normalize_upstream_graph(raw_payload: dict, *, source: str) -> tuple[dict, dict]:
    """Return served graph body (nodes/edges/...) and integrity from upstream source JSON."""
    if not isinstance(raw_payload, dict):
        raise AppException("Roadmap graph response was invalid", status_code=502)

    upstream = copy.deepcopy(raw_payload)
    upstream.pop("integrity", None)

    nodes = upstream.get("nodes")
    edges = upstream.get("edges")
    node_ids = _validate_nodes(nodes)
    _validate_edge_records(edges if isinstance(edges, list) else [])

    if not isinstance(edges, list):
        raise AppException("Roadmap graph response was invalid", status_code=502)

    duplicate_ids = detect_duplicate_edge_ids(edges)
    normalized_edges, edge_normalizations = normalize_duplicate_edge_ids(edges)
    served_edges, removed_edges = drop_dangling_edges(normalized_edges, node_ids)

    edge_count_original = len(edges)
    edge_count_retained = len(served_edges)

    if edge_count_retained == 0 and edge_count_original == 0:
        classification = "edgeless"
    elif edge_normalizations or removed_edges:
        classification = "sanitized"
    else:
        classification = "clean"

    integrity = {
        "classification": classification,
        "source": source,
        "source_payload_sha256": source_payload_hash(upstream),
        "node_count": len(nodes),
        "edge_count_original": edge_count_original,
        "edge_count_retained": edge_count_retained,
        "duplicate_edge_ids_original": duplicate_ids,
        "edge_normalizations": edge_normalizations,
        "removed_edges": removed_edges,
        "provenance_verified": True,
    }

    served = {**upstream, "nodes": nodes, "edges": served_edges, "integrity": integrity}
    return served, integrity


def graph_response_from_cache_envelope(envelope: dict) -> dict | None:
    """Validate cache envelope and return API graph response without losing integrity."""
    if envelope.get("cache_version") != 2:
        return None
    source_payload = envelope.get("source_payload")
    integrity = envelope.get("integrity")
    served = envelope.get("served")
    source = envelope.get("source")
    if not isinstance(source_payload, dict) or not isinstance(integrity, dict) or not isinstance(served, dict):
        return None
    if not isinstance(source, str):
        return None

    recomputed, recomputed_integrity = normalize_upstream_graph(source_payload, source=source)
    if recomputed_integrity != integrity:
        return None
    if recomputed.get("nodes") != served.get("nodes") or recomputed.get("edges") != served.get("edges"):
        return None

    return {**served, "integrity": integrity}
