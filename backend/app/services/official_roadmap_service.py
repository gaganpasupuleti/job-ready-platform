"""roadmap.sh graph + local topic markdown from developer-roadmap content."""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from app.core.exceptions import AppException

_CONTENT_ROOT = (
    Path(__file__).resolve().parents[2].parent
    / "design-reference"
    / "developer-roadmap-master"
    / "roadmaps"
)
_CACHE_DIR = Path(__file__).resolve().parents[1] / "data" / "roadmap-cache"
_ROADMAP_JSON_URL = "https://roadmap.sh/{slug}.json"


def list_official_roadmaps() -> list[dict[str, str]]:
    if not _CONTENT_ROOT.is_dir():
        return []
    rows: list[dict[str, str]] = []
    for path in sorted(_CONTENT_ROOT.iterdir()):
        if not path.is_dir():
            continue
        slug = path.name
        rows.append(
            {
                "family_slug": slug,
                "title": slug.replace("-", " ").title(),
                "description": f"Interactive career learning path ({slug.replace('-', ' ')}).",
                "preview_only": False,
                "student_eligible": True,
                "source": "official",
            }
        )
    return rows


def _cache_path(slug: str) -> Path:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return _CACHE_DIR / f"{slug}.json"


def fetch_official_graph(slug: str) -> dict:
    if not re.fullmatch(r"[a-z0-9-]+", slug):
        raise AppException("Invalid roadmap slug", status_code=400)
    cached = _cache_path(slug)
    if cached.is_file():
        with cached.open(encoding="utf-8") as handle:
            return json.load(handle)
    url = _ROADMAP_JSON_URL.format(slug=slug)
    try:
        with urlopen(url, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code == 404:
            raise AppException("Roadmap graph not found on roadmap.sh", status_code=404) from exc
        raise AppException("Could not download roadmap graph", status_code=502) from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise AppException("Could not download roadmap graph", status_code=502) from exc
    with cached.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle)
    return payload


def _topic_dir(slug: str) -> Path:
    return _CONTENT_ROOT / slug / "content"


def find_topic_markdown(slug: str, node_id: str) -> Path | None:
    content_dir = _topic_dir(slug)
    if not content_dir.is_dir():
        return None
    direct = list(content_dir.glob(f"*@{node_id}.md"))
    if direct:
        return direct[0]
    return None


def get_topic_content(slug: str, node_id: str, old_id: str | None = None) -> dict:
    path = None
    for key in (old_id, node_id):
        if not key:
            continue
        path = find_topic_markdown(slug, key)
        if path is not None:
            break
    if path is None:
        raise AppException("Topic content not found in local syllabus", status_code=404)
    text = path.read_text(encoding="utf-8")
    title = path.stem.split("@", 1)[0].replace("-", " ").title()
    return {"node_id": node_id, "title": title, "markdown": text, "source_path": str(path.name)}
