# Roadmap UI stabilization — audit package

## Branches and PRs

| Item | Value |
|------|--------|
| Audited commit (prior pass) | `56ba9a676603fcbce6183523306098742ad422d6` on `feat/official-roadmaps-retro-ui` |
| **Clean scope branch** | `feat/roadmap-ui-clean` (from `origin/master`, no Power BI routes/pages) |
| Inherited PR (unchanged) | [#23](https://github.com/gaganpasupuleti/job-ready-platform/pull/23) — still open; includes Power BI history |
| Worktree path | `c:\Users\Admin\OneDrive\Documents\cursor\jobready-roadmap-ui-clean` |

Relationship: review **`feat/roadmap-ui-clean`** for roadmap/Jobs/UI only. PR #23 remains for combined branch history; do not close #23 automatically.

## Major behavioral fixes

| Issue | Status | Notes |
|-------|--------|-------|
| Editing toggle reloads graph positions | **Regression-tested** | Graph init effect no longer depends on `nodesDraggable`; draggable applied in separate effect |
| First-mount viewport skipped | **Browser-verified (mock)** | `fittedGraphKeyRef` starts `null`; double `rAF` fit after nodes present |
| Viewport reset on article/panels | **Implemented** | Fit only on slug change; camera focus from outline only |
| Mobile dialog blocks desktop | **Implemented** | `matchMedia(901px)` closes dialog |
| Topic search with outline closed | **Browser-verified (mock)** | Toolbar search results panel |
| Jobs Save errors | **Browser-verified (mock)** | `saveError` + `saveMutation.isError` alert |
| Graph validation parity | **Regression-tested** | FE `assertValidGraphShape`; BE expanded `_validate_graph_payload` |
| Cache dir creation failures | **Implemented** | Catalog listing does not fail if cache mkdir fails |

## Visual redesign

- Canvas-first roadmap workspace (compact header, toolbar, collapsible outline, article-on-demand).
- Token-based `official-roadmap.css` + restored connector/section/linksgroup/handle styles.
- Shared shell tokens in `index.css`; restrained retro (`jobready-retro.css`) without heavy card hover motion.
- Jobs hierarchy and compact summary retained.

## Tests

| Command | Result |
|---------|--------|
| `npm run build` (worktree frontend) | **Pass** |
| `npm run test:unit` | **29 passed** (includes `graphValidation` test) |
| `pytest tests/test_roadmap_official.py` | **5 passed** |
| `npx playwright test e2e/roadmap-mock.spec.ts --project=desktop` | **4 passed (mocked auth/API)** |

**Live integration:** not run (requires real login + backend). Mocked browser tests use `localStorage` token + Playwright route interception only — no auth bypass in shipped code.

## Screenshots (mocked browser)

Under `frontend/e2e/artifacts/acceptance-shots/roadmap-ui/`:

- `catalog-light-1366.png`
- `viewer-no-article-1366.png`
- `viewer-article-open-1366.png`
- `viewer-outline-closed-1366.png`
- `viewer-dark-1366.png`
- `mobile-topic-sheet-390.png`
- `jobs-save-error-1366.png`

Viewports: 1366×900 and 390×844; dark via `emulateMedia`.

## Topic content provisioning

1. Sync `frontend/public/official-roadmaps-index.json` and `backend/app/data/official-roadmap-catalog.json`.
2. Graphs: API fetch + optional cache (`ROADMAP_GRAPH_CACHE_DIR`); catalog `graph_fetchable` vs cached `graph_available`.
3. Articles: mount `ROADMAP_CONTENT_ROOT` → `{slug}/content/*.md` with API attribution string.

## Remaining gaps

- Live backend graph fetch, real credentials, and full 390/768/1920 matrix **unverified**.
- Full `index.css` / v4-shell deduplication is partial (retro layer trimmed, not fully deleted).
- React Flow container height warnings in dev console during mock runs (monitor on short laptop heights).

## Reproduce

```bash
git clone ... && cd job-ready-platform
git checkout feat/roadmap-ui-clean
cd frontend && npm ci && npm run build && npm run test:unit
npx playwright test e2e/roadmap-mock.spec.ts --project=desktop
cd ../backend && pip install -r requirements.txt && pytest tests/test_roadmap_official.py -q
```

Unrelated Power BI WIP on `feat/official-roadmaps-retro-ui` was not modified in the clean worktree.
