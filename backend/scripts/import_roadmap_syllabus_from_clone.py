"""Copy roadmaps/*/content from a local developer-roadmap git clone into app data."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "app" / "data" / "official-roadmap-catalog.json"
DEST = ROOT / "app" / "data" / "roadmap-syllabus" / "roadmaps"

sys.path.insert(0, str(ROOT))
from app.services.official_roadmap_service import _GRAPH_FETCH_SLUG_ALIASES  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("clone_dir", type=Path, help="Path to developer-roadmap repo root")
    args = parser.parse_args()
    clone = args.clone_dir.resolve()
    roadmaps = clone / "roadmaps"
    if not roadmaps.is_dir():
        raise SystemExit(f"missing {roadmaps}")

    commit = subprocess.check_output(["git", "-C", str(clone), "rev-parse", "HEAD"], text=True).strip()
    rows = json.loads(CATALOG.read_text(encoding="utf-8")).get("roadmaps", [])
    slugs = [str(r["family_slug"]) for r in rows if r.get("family_slug")]

    stats: list[dict] = []
    for catalog_slug in slugs:
        repo_slug = _GRAPH_FETCH_SLUG_ALIASES.get(catalog_slug, catalog_slug)
        src = roadmaps / repo_slug / "content"
        dst = DEST / catalog_slug / "content"
        if not src.is_dir():
            stats.append({"catalog_slug": catalog_slug, "repo_slug": repo_slug, "files": 0, "missing": True})
            continue
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        count = len(list(dst.glob("*.md")))
        stats.append({"catalog_slug": catalog_slug, "repo_slug": repo_slug, "files": count, "missing": False})

    manifest = {
        "source_repo": "kamranahmedse/developer-roadmap",
        "source_commit": commit,
        "import_method": "sparse_git_clone",
        "dest": "backend/app/data/roadmap-syllabus/roadmaps",
        "slugs": stats,
    }
    out = DEST.parent / "ROADMAP_SYLLABUS_MANIFEST.json"
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    with_files = sum(1 for s in stats if s.get("files", 0) > 0)
    print(json.dumps({"commit": commit, "slugs_with_content": with_files, "total": len(slugs), "manifest": str(out)}))


if __name__ == "__main__":
    main()
