# Coordinated pass — PR #24 (`feat/roadmap-ui-clean`)

**PR:** [#24](https://github.com/gaganpasupuleti/job-ready-platform/pull/24) — **not merged**  
**Base reviewed:** `055b22824f24951e2b9d3d210e88d125d744b62d`  
**Preview:** see [PREVIEW_DELIVERY.md](./PREVIEW_DELIVERY.md)

## Implemented in this pass

### Explore launcher (replaces More dropdown)

- `exploreNavRegistry.ts` — destinations, categories, longest-prefix active route, search filter.
- `ExploreLauncher.tsx` — desktop anchored popover (search + category rail + destination panel); mobile bottom sheet.
- `explore-nav.css` — shared surface/border/focus with account menu.
- `Masthead.tsx` — primary nav + Explore; Feedback in toolbar; Explore/Account mutex.

### Roadmap interaction

- **Topic/subtopic draggable by default**; **Lock layout** checkbox freezes positions.
- Per-`graphKey` session layout cache (in-memory, not persisted to backend).
- Click vs drag: `nodeDragThreshold` + drag flag suppresses article open after move.
- `ResizeObserver` on flow host before initial `fitView`.
- Collapsible minimap control.
- Handle ids: `{slot}-s` / `{slot}-t` mapped in `toFlowEdge()`.

### Catalog audit tooling

- `frontend/scripts/audit-roadmap-catalog.mjs` — concurrent graph fetch + edge/handle report → `e2e/artifacts/roadmap-catalog-audit.json`.

## Verification status

| Check | Status |
|-------|--------|
| `npm run build` | Run after each commit |
| Mocked Playwright `roadmap-mock.spec.ts` | Re-run with `CI=true` on delivery port |
| Full catalog browser render | **Pending** — run audit script with valid API token |
| Before/after screenshots | **Pending** — capture from 5175 after login |
| Live 93-path visual sign-off | **Pending** |

## Remaining blockers (unchanged)

- Validator vs server graph parity for every slug.
- Legacy assembly endpoint / draft-only graphs.
- Topic provisioning + attribution for all official articles.
- Retro workspace (`5173`) still holds uncommitted nav/auth/Power BI — merge from delivery branch when ready.

## Tests

- `tests/roadmapOfficial.test.ts` — handle mapping unit test.
- Catalog audit — `node frontend/scripts/audit-roadmap-catalog.mjs --api http://127.0.0.1:8000` (auth required for pass counts).
