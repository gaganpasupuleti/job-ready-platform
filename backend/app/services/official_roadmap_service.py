"""Official career roadmap graphs (cached) and optional local syllabus markdown."""

from __future__ import annotations

import json
import logging
import re
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx

from app.core.config import settings
from app.core.exceptions import AppException

logger = logging.getLogger(__name__)

_SLUG_RE = re.compile(r"^[a-z0-9-]+$")
_NODE_KEY_RE = re.compile(r"^[A-Za-z0-9_-]+$")
_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_CATALOG_PATH = _DATA_DIR / "official-roadmap-catalog.json"
_ATTRIBUTION = (
    "Topic articles are adapted from the community Developer Roadmap project "
    "(https://github.com/kamranahmedse/developer-roadmap) under its repository license."
)

_LEGACY_DRAFT = {
    "family_slug": "data-engineer",
    "title": "Data Engineer",
    "config_version": "2-linked-draft",
    "description": "Linked draft curriculum: SQL, Python, pipelines, and platform practice.",
    "preview_only": True,
    "student_eligible": False,
    "source": "legacy-draft",
    "graph_available": False,
    "articles_available": False,
}


def _graph_cache_dir() -> Path:
    raw = (settings.roadmap_graph_cache_dir or "").strip()
    path = Path(raw) if raw else _DATA_DIR / "roadmap-cache"
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        logger.warning("Roadmap graph cache directory unavailable: %s", exc)
    return path


def _content_root() -> Path | None:
    raw = (settings.roadmap_content_root or "").strip()
    if raw:
        root = Path(raw).expanduser().resolve()
        return root if root.is_dir() else None
    default = _DATA_DIR / "roadmap-syllabus" / "roadmaps"
    if default.is_dir():
        return default.resolve()
    legacy = (
        Path(__file__).resolve().parents[2].parent
        / "design-reference"
        / "developer-roadmap-master"
        / "roadmaps"
    )
    return legacy.resolve() if legacy.is_dir() else None


def _load_catalog_file() -> list[dict]:
    if not _CATALOG_PATH.is_file():
        return []
    with _CATALOG_PATH.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    rows = payload.get("roadmaps") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict) and row.get("family_slug")]


def _slug_has_articles(slug: str, root: Path | None) -> bool:
    if root is None:
        return False
    content = (root / slug / "content").resolve()
    try:
        content.relative_to(root.resolve())
    except ValueError:
        return False
    return content.is_dir() and any(content.glob("*.md"))


def _graph_cache_path(slug: str) -> Path:
    return _graph_cache_dir() / f"{slug}.json"


def _cache_is_fresh(path: Path) -> bool:
    if not path.is_file():
        return False
    ttl = max(int(settings.roadmap_graph_cache_ttl_hours), 1)
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
    return datetime.now(tz=UTC) - mtime < timedelta(hours=ttl)


def list_official_roadmaps() -> list[dict]:
    root = _content_root()
    rows: list[dict] = []
    for raw in _load_catalog_file():
        slug = str(raw.get("family_slug", "")).strip()
        if not _SLUG_RE.fullmatch(slug):
            continue
        rows.append(
            {
                "family_slug": slug,
                "title": raw.get("title") or slug.replace("-", " ").title(),
                "description": raw.get("description")
                or f"Interactive career learning path ({slug.replace('-', ' ')}).",
                "preview_only": bool(raw.get("preview_only", False)),
                "student_eligible": bool(raw.get("student_eligible", True)),
                "source": raw.get("source") or "official",
                "graph_available": _graph_cache_path(slug).is_file(),
                "graph_fetchable": True,
                "articles_available": _slug_has_articles(slug, root),
            }
        )
    if rows:
        slugs = {row["family_slug"] for row in rows}
        if _LEGACY_DRAFT["family_slug"] not in slugs:
            rows.append(dict(_LEGACY_DRAFT))
        return rows

    if root is None:
        return []

    for path in sorted(root.iterdir()):
        if not path.is_dir():
            continue
        slug = path.name
        if not _SLUG_RE.fullmatch(slug):
            continue
        rows.append(
            {
                "family_slug": slug,
                "title": slug.replace("-", " ").title(),
                "description": f"Interactive career learning path ({slug.replace('-', ' ')}).",
                "preview_only": False,
                "student_eligible": True,
                "source": "official",
                "graph_available": _graph_cache_path(slug).is_file(),
                "graph_fetchable": True,
                "articles_available": _slug_has_articles(slug, root),
            }
        )
    return rows


def _validate_graph_payload(payload: dict) -> dict:
    nodes = payload.get("nodes")
    edges = payload.get("edges")
    if not isinstance(nodes, list) or not nodes:
        raise AppException("Roadmap graph response was invalid", status_code=502)
    if not isinstance(edges, list):
        raise AppException("Roadmap graph response was invalid", status_code=502)
    node_ids: set[str] = set()
    for node in nodes:
        if not isinstance(node, dict) or not isinstance(node.get("id"), str):
            raise AppException("Roadmap graph response was invalid", status_code=502)
        node_id = node["id"]
        if node_id in node_ids:
            raise AppException("Roadmap graph response was invalid", status_code=502)
        node_ids.add(node_id)
        position = node.get("position")
        if not isinstance(position, dict):
            raise AppException("Roadmap graph response was invalid", status_code=502)
        x, y = position.get("x"), position.get("y")
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            raise AppException("Roadmap graph response was invalid", status_code=502)
    edge_ids: set[str] = set()
    for edge in edges:
        if not isinstance(edge, dict) or not isinstance(edge.get("id"), str):
            raise AppException("Roadmap graph response was invalid", status_code=502)
        edge_id = edge["id"]
        if edge_id in edge_ids:
            raise AppException("Roadmap graph response was invalid", status_code=502)
        edge_ids.add(edge_id)
        source, target = edge.get("source"), edge.get("target")
        if not isinstance(source, str) or not isinstance(target, str):
            raise AppException("Roadmap graph response was invalid", status_code=502)
        if source not in node_ids or target not in node_ids:
            raise AppException("Roadmap graph response was invalid", status_code=502)
    return payload


def _read_graph_cache(slug: str) -> dict | None:
    path = _graph_cache_path(slug)
    if not _cache_is_fresh(path):
        return None
    try:
        with path.open(encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, dict):
            return _validate_graph_payload(payload)
    except AppException:
        logger.warning("Ignoring invalid roadmap graph cache for %s", slug)
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Ignoring corrupt roadmap graph cache for %s: %s", slug, exc)
    return None


def _write_graph_cache(slug: str, payload: dict) -> None:
    path = _graph_cache_path(slug)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        delete=False,
        suffix=".tmp",
    ) as handle:
        json.dump(payload, handle)
        temp_name = handle.name
    Path(temp_name).replace(path)


async def fetch_official_graph(slug: str) -> dict:
    if not _SLUG_RE.fullmatch(slug):
        raise AppException("Invalid roadmap slug", status_code=400)

    catalog_slugs = {row["family_slug"] for row in _load_catalog_file()}
    if catalog_slugs and slug not in catalog_slugs:
        raise AppException("Roadmap not in catalog", status_code=404)

    cached = _read_graph_cache(slug)
    if cached is not None:
        return cached

    url = settings.roadmap_graph_fetch_url.format(slug=slug)
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            response = await client.get(url)
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise AppException("Roadmap graph not found", status_code=404) from exc
        raise AppException("Could not download roadmap graph", status_code=502) from exc
    except (httpx.HTTPError, json.JSONDecodeError, ValueError) as exc:
        raise AppException("Could not download roadmap graph", status_code=502) from exc

    if not isinstance(payload, dict):
        raise AppException("Roadmap graph response was invalid", status_code=502)
    payload = _validate_graph_payload(payload)

    try:
        _write_graph_cache(slug, payload)
    except OSError as exc:
        logger.warning("Could not write roadmap graph cache for %s: %s", slug, exc)

    return payload


def _resolve_topic_file(slug: str, node_key: str) -> Path | None:
    if not _NODE_KEY_RE.fullmatch(node_key):
        return None
    root = _content_root()
    if root is None:
        return None
    content_dir = (root / slug / "content").resolve()
    try:
        content_dir.relative_to(root.resolve())
    except ValueError:
        return None
    if not content_dir.is_dir():
        return None
    matches = list(content_dir.glob(f"*@{node_key}.md"))
    if not matches:
        return None
    path = matches[0].resolve()
    try:
        path.relative_to(content_dir)
    except ValueError:
        return None
    return path


def get_topic_content(slug: str, node_id: str, old_id: str | None = None) -> dict:
    if not _SLUG_RE.fullmatch(slug):
        raise AppException("Invalid roadmap slug", status_code=400)

    path = None
    for key in (old_id, node_id):
        if not key:
            continue
        path = _resolve_topic_file(slug, key)
        if path is not None:
            break

    if path is None:
        raise AppException(
            "Topic article is not available for this roadmap yet.",
            status_code=404,
        )

    text = path.read_text(encoding="utf-8")
    title = path.stem.split("@", 1)[0].replace("-", " ").title()
    return {
        "node_id": node_id,
        "title": title,
        "markdown": text,
        "attribution": _ATTRIBUTION,
    }
