"""Sync official roadmap topic markdown from the Developer Roadmap open-source repo.

Source: https://github.com/kamranahmedse/developer-roadmap (MIT-style community license).
Output layout matches official_roadmap_service._resolve_topic_file:
  {dest}/roadmaps/{catalog_slug}/content/{title}@{nodeId}.md

Run from backend root:
  python -m scripts.sync_roadmap_syllabus_content
  python -m scripts.sync_roadmap_syllabus_content --commit <sha> --slugs python,data-analyst
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "app" / "data" / "official-roadmap-catalog.json"
DEFAULT_DEST = ROOT / "app" / "data" / "roadmap-syllabus" / "roadmaps"
MANIFEST_NAME = "ROADMAP_SYLLABUS_MANIFEST.json"
REPO = "kamranahmedse/developer-roadmap"
DEFAULT_COMMIT = "e906c5f60c2e72623a73cce4bea51153b319c0d8"

sys.path.insert(0, str(ROOT))
from app.services.official_roadmap_service import _GRAPH_FETCH_SLUG_ALIASES  # noqa: E402

_ATTRIBUTION_HEADER = (
    "<!--\n"
    "  Synced from https://github.com/kamranahmedse/developer-roadmap for JobReady syllabus display.\n"
    "  Community Developer Roadmap — see repository LICENSE.\n"
    "-->\n\n"
)


def _github_json(url: str) -> list | dict:
    req = urllib.request.Request(
        url,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "jobready-sync"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _download_raw(commit: str, repo_path: str) -> bytes:
    url = f"https://raw.githubusercontent.com/{REPO}/{commit}/{repo_path}"
    with urllib.request.urlopen(url, timeout=120) as resp:
        return resp.read()


def _repo_slug(catalog_slug: str) -> str:
    return _GRAPH_FETCH_SLUG_ALIASES.get(catalog_slug, catalog_slug)


def _list_content_files(commit: str, repo_slug: str) -> list[dict]:
    files: list[dict] = []
    page = 1
    while True:
        url = (
            f"https://api.github.com/repos/{REPO}/contents/roadmaps/{repo_slug}/content"
            f"?ref={commit}&per_page=100&page={page}"
        )
        try:
            batch = _github_json(url)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return files
            raise
        if not isinstance(batch, list) or not batch:
            break
        for item in batch:
            if item.get("type") == "file" and str(item.get("name", "")).endswith(".md"):
                files.append(item)
        if len(batch) < 100:
            break
        page += 1
        time.sleep(0.2)
    return files


def sync_slug(commit: str, catalog_slug: str, dest_root: Path) -> dict:
    repo_slug = _repo_slug(catalog_slug)
    content_dir = dest_root / catalog_slug / "content"
    content_dir.mkdir(parents=True, exist_ok=True)
    entries = _list_content_files(commit, repo_slug)
    written = 0
    skipped = 0
    for item in entries:
        name = str(item["name"])
        if not re.search(r"@[A-Za-z0-9_-]+\.md$", name):
            skipped += 1
            continue
        repo_path = str(item["path"])
        body = _download_raw(commit, repo_path)
        target = content_dir / name
        if not target.exists() or target.read_bytes() != body:
            text = body.decode("utf-8")
            if not text.lstrip().startswith("<!--"):
                text = _ATTRIBUTION_HEADER + text
            target.write_text(text, encoding="utf-8")
        written += 1
        time.sleep(0.02)
    return {
        "catalog_slug": catalog_slug,
        "repo_slug": repo_slug,
        "files_listed": len(entries),
        "files_written": written,
        "files_skipped": skipped,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", default=DEFAULT_COMMIT)
    parser.add_argument("--dest", type=Path, default=DEFAULT_DEST)
    parser.add_argument("--slugs", default="", help="Comma-separated catalog slugs (default: all)")
    args = parser.parse_args()

    rows = json.loads(CATALOG.read_text(encoding="utf-8")).get("roadmaps", [])
    all_slugs = [str(r["family_slug"]) for r in rows if r.get("family_slug")]
    slugs = [s.strip() for s in args.slugs.split(",") if s.strip()] if args.slugs else all_slugs

    results: list[dict] = []
    for i, slug in enumerate(slugs, 1):
        print(f"[{i}/{len(slugs)}] {slug}", flush=True)
        try:
            results.append(sync_slug(args.commit, slug, args.dest))
        except Exception as exc:  # noqa: BLE001
            results.append({"catalog_slug": slug, "error": str(exc)})

    manifest = {
        "source_repo": REPO,
        "source_commit": args.commit,
        "synced_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "dest": str(args.dest.resolve()),
        "catalog_slugs": len(slugs),
        "slugs": results,
    }
    manifest_path = args.dest.parent / MANIFEST_NAME
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    ok = sum(1 for r in results if r.get("files_written", 0) > 0)
    print(json.dumps({"manifest": str(manifest_path), "slugs_with_content": ok, "total": len(slugs)}))


if __name__ == "__main__":
    main()
