"""Student career roadmap assembly (static exports until DB-backed definitions ship)."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user
from app.core.exceptions import AppException
from app.models.user import User
from app.services.official_roadmap_service import (
    fetch_official_graph,
    get_topic_content,
    list_official_roadmaps,
)

router = APIRouter(prefix="/roadmap")

_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "roadmaps"

_CATALOG = [
    {
        "family_slug": "data-engineer",
        "title": "Data Engineer",
        "config_version": "2-linked-draft",
        "description": "Linked draft curriculum: SQL, Python, pipelines, and platform practice.",
        "preview_only": True,
        "student_eligible": False,
    },
]


def _load_payload(family_slug: str, config_version: str) -> dict:
    filename = f"{family_slug}.{config_version}.json"
    path = _DATA_DIR / filename
    if not path.is_file():
        raise AppException("Roadmap not found", status_code=404)
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


@router.get("/catalog")
async def list_roadmaps(
    _user: User = Depends(get_current_user),
) -> dict:
    official = list_official_roadmaps()
    if official:
        with_articles = sum(1 for row in official if row.get("articles_available"))
        with_graph_cache = sum(1 for row in official if row.get("graph_available"))
        return {
            "roadmaps": official,
            "source": "official",
            "meta": {
                "total": len(official),
                "with_articles": with_articles,
                "with_graph_cache": with_graph_cache,
                "has_bundled_catalog": True,
            },
        }
    return {"roadmaps": _CATALOG, "source": "legacy", "meta": {"total": len(_CATALOG)}}


@router.get("/official/{slug}/graph")
async def get_official_graph(
    slug: str,
    _user: User = Depends(get_current_user),
) -> dict:
    return await fetch_official_graph(slug)


@router.get("/official/{slug}/topics/{node_id}")
async def get_official_topic(
    slug: str,
    node_id: str,
    old_id: str | None = Query(default=None),
    _user: User = Depends(get_current_user),
) -> dict:
    return get_topic_content(slug, node_id, old_id=old_id)


@router.get("/assembly")
async def get_roadmap_assembly(
    family_slug: str = Query(..., min_length=1, max_length=80),
    config_version: str | None = Query(default=None, max_length=80),
    _user: User = Depends(get_current_user),
) -> dict:
    version = config_version
    if not version:
        match = next((row for row in _CATALOG if row["family_slug"] == family_slug), None)
        if match is None:
            raise AppException("Roadmap not found", status_code=404)
        version = match["config_version"]
    return _load_payload(family_slug, version)
