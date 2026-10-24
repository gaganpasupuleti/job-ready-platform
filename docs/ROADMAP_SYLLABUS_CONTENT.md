# Official roadmap syllabus content (developer-roadmap)

Syllabus Markdown for official roadmaps is **not** embedded in roadmap JSON. The backend serves articles from on-disk files under the content root (see `official_roadmap_service._content_root()`).

## Bundled content (default)

- **Path:** `backend/app/data/roadmap-syllabus/roadmaps/{catalog_slug}/content/*@{nodeId}.md`
- **Manifest:** `backend/app/data/roadmap-syllabus/ROADMAP_SYLLABUS_MANIFEST.json`
- **Upstream:** [kamranahmedse/developer-roadmap](https://github.com/kamranahmedse/developer-roadmap) at commit recorded in the manifest (`source_commit`).
- **Attribution:** API responses include the standard developer-roadmap attribution string.

When `ROADMAP_CONTENT_ROOT` is unset, the backend uses the bundled directory above if it exists in the image/checkout.

## Re-import / refresh

1. Sparse-clone upstream at the desired commit:

   ```bash
   git clone --filter=blob:none --sparse https://github.com/kamranahmedse/developer-roadmap.git /tmp/developer-roadmap
   cd /tmp/developer-roadmap
   git sparse-checkout set roadmaps
   git checkout e906c5f60c2e72623a73cce4bea51153b319c0d8
   ```

2. Copy into app data (respects catalog slug → repo folder aliases such as `r` → `r-programming`):

   ```bash
   cd backend
   python scripts/import_roadmap_syllabus_from_clone.py /tmp/developer-roadmap
   ```

3. Verify file coverage against warmed graph cache:

   ```bash
   python -m scripts.verify_roadmap_article_coverage
   ```

   Writes `docs/ci-evidence/roadmap-article-file-coverage.json`.

Alternative (GitHub API): `python scripts/sync_roadmap_syllabus_content.py` — may hit rate limits; prefer sparse clone in CI/automation.

## Railway / hosted backend

- **Recommended:** commit bundled syllabus under `backend/app/data/roadmap-syllabus/` so the Docker image includes articles without extra mounts.
- **Optional override:** set `ROADMAP_CONTENT_ROOT` to an absolute path inside the container **only if** that path is populated (volume or build step). Setting the variable without files does not enable articles.
- **Persistence:** syllabus is static relative to a deploy SHA; refresh by redeploying an image built after re-import, or mount a volume and run `import_roadmap_syllabus_from_clone.py` in a one-off job.

## Known gaps (truthful missing content)

- Some upstream folders use non–`title@nodeId.md` names (e.g. `code-review/content/*.md` without node ids). Those topics remain **404** for id-based lookup until upstream naming aligns or a separate mapping is added.
- File coverage report lists per-slug `missing_files` vs readable graph nodes; the authenticated catalog audit samples **one** readable node per slug and does not imply full corpus coverage.
