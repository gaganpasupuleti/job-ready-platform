# Roadmap & UI audit delivery report (corrective pass)

## Baseline and scope

| Item | Value |
|------|--------|
| Audited head (prior) | `b0dbff1051ba85611f0efdecfbb595b80acc03b0` |
| Branch | `feat/official-roadmaps-retro-ui` |
| PR | https://github.com/gaganpasupuleti/job-ready-platform/pull/23 (unmerged) |
| PR scope note | See `docs/PR23_SCOPE.md` — full PR vs `master` includes Power BI commits `6feebb7`–`e12b145`; roadmap audit commits start at `24ea439` / `962e657`. |

Unrelated local WIP (Power BI unstaged edits, design-reference, etc.) remains unstaged.

## Corrective pass — finding status

| Finding | Status | Evidence |
|---------|--------|----------|
| Node `draggable: true` overrides explore mode | **Implemented** | `graph.ts` defaults `draggable: false`; `applyNodesDraggable` toggles edit mode |
| Outline hide breaks 3-column grid | **Implemented** | `ors-layout--outline-*` / `--article-*` grid classes |
| Dark mode hardcoded roadmap colors | **Implemented** | `official-roadmap.css` uses `--color-*` / `--jr-*` tokens |
| Jobs Browse Save not wired | **Implemented** | `JobsHubPage` `saveMutation` + `onToggleSave` |
| Mobile sheet a11y | **Implemented** | Native `<dialog>` + `showModal`, Escape, focus on open, restore on close |
| Reduced motion (camera) | **Implemented** | `flowDuration()` on fit/zoom/reset |
| Markdown link slug validation | **Implemented** | `rewriteRoadmapShMarkdown(md, allowedSlugs)` |
| Catalog 401 vs 403 | **Implemented** | Both rethrown in `roadmapService.ts` |
| Malformed graphs | **Implemented** | `_validate_graph_payload` backend; `normalizeOfficialGraph` frontend |
| `graph_available` overstated | **Implemented** | Backend: cache file exists; bundle defaults false |
| Catalog “≥10 rows” heuristic | **Implemented** | `source === 'official' && meta.has_bundled_catalog` |
| Topic Retry | **Implemented** | `RoadmapTopicPanel` + `topicQuery.refetch()` |
| Role pill clipping | **Implemented** | First N pills + “More roles”; no fixed-height clip |
| Viewport reset on article load | **Implemented** | `cameraFocusId` only from outline; graph key fit only on slug change |
| PR Power BI scope | **Documented** | `docs/PR23_SCOPE.md` |

## Instability causes addressed

| Cause | Fix |
|-------|-----|
| `fitView` on every `initialNodes` reference change | Fit only when `graphKey` (slug) changes |
| Per-node `draggable: true` | Explore mode forces `draggable: false` on all nodes |
| Empty article column always reserved | Article column only when a topic is selected |
| Selection from map triggering camera refit | Camera focus only from outline selection |

## Tests (actual results)

| Command | Result |
|---------|--------|
| `npm run build` | **Pass** |
| `npm run test:unit` | **29 passed** (includes `tests/roadmapOfficial.test.ts`) |
| `python -m pytest tests/test_roadmap_official.py -q` | **5 passed** |
| `node scripts/validate-roadmap-catalog.mjs` | Run in CI/local (not re-run this pass) |

## Browser verification

| Check | Status |
|-------|--------|
| Multi-viewport / theme screenshots | **Unverified** unless captured under `frontend/e2e-artifacts/acceptance-shots/` in this session |
| Authenticated roadmap + topic content | Requires running API + login; use dev mock or staging |

## Content provisioning

Unchanged: bundled catalog JSON; graphs via API cache; articles via `ROADMAP_CONTENT_ROOT` mount.

## Reproduce

```bash
git fetch origin feat/official-roadmaps-retro-ui
git checkout feat/official-roadmaps-retro-ui
cd frontend && npm ci && npm run build && npm run test:unit
cd ../backend && pip install -r requirements.txt && pytest tests/test_roadmap_official.py -q
```

After corrective commit: record **HEAD SHA** below in git log.
