# PR #24 release audit — roadmap / UI only

**Branch:** `feat/roadmap-ui-clean`  
**PR:** https://github.com/gaganpasupuleti/job-ready-platform/pull/24  
**Candidate SHA:** `56172e3` (fix on `88e18dd`; CI [39834374466](https://github.com/gaganpasupuleti/job-ready-platform/actions/runs/39834374466) in progress)  
**Status:** Open — not merged, not deployed.

## CI run 39724330440 (`88e18dd`) — five failures (investigated)

| # | Spec | Root cause class | Root cause | Correction in `56172e3` |
|---|------|------------------|------------|-------------------------|
| 1 | `roadmap-catalog-render` catalog inventory | **Test harness** | `GET /api/v1/roadmap/catalog` requires auth; raw Playwright `request` returned **401** | Student bearer via `loginAccessToken` |
| 2 | `roadmap-catalog-render` per-slug loop | **Test harness + timing** | Counted `.react-flow__node` immediately; `onlyRenderVisibleElements` can yield **0 DOM nodes** before fit/viewport settles (`devops` reported) | Poll until node count &gt; 0 (90s cap per slug); still fails if graph truly empty |
| 3–4 | `roadmap-graph-interaction` drag + lock/reset | **Test harness** | Selector `.react-flow__node.draggable.ors-node--topic` invalid — `ors-node--topic` is on **inner** card, not the RF wrapper | `.react-flow__node.draggable` filtered with `:has(.ors-node--topic)` |
| 5 | `roadmap-graph-interaction` viewport stability | **Application** | Article panel resize triggered **fitOverview** (scale ≈ 0.55); transform jumped from ~1px translate to ~505px | Freeze viewport before non-focus topic select; `ResizeObserver` restore; skip auto-fit while article open |

**Counts (39724330440):** Backend pass, Frontend pass, Playwright **134 passed, 5 failed, 6 skipped** (~34.2 min). No flaky retries reported beyond configured retry=1.

**Per-slug browser (39724330440):** Loop completed all **93** slugs; only `devops` recorded `fail` (zero nodes) before assertion — full `roadmap-catalog-browser-results.json` not uploaded from CI (artifact gap).

## Application changes (`56172e3`)

- `OfficialRoadmapView` / `RoadmapFlowCanvas`: preserve pan/zoom when opening article from canvas (not outline focus-camera path).
- `roadmap-viewport.ts`: parse transform + tight FP tolerance (±1.5px, ±0.02 zoom).

## Prior candidate `88e18dd` (still relevant)

| Area | Fix |
|------|-----|
| UI cohesion | Separate browser context per theme; contrast probes flag `unsupported_transparency` |
| Preview smoke script | GUID readiness marker, port preflight, `taskkill /T` |
| Release preview spec | Save/reload/unsave + article body length check |

## Runtime

- Node **22+** (`frontend/.nvmrc`, CI `node-version: "22"`).
- Unit tests: `npm run test:unit` — **35/35** on `56172e3` locally.

## CI evidence

| Run | SHA | Frontend | Backend | Playwright | Notes |
|-----|-----|----------|---------|------------|-------|
| [39715695335](https://github.com/gaganpasupuleti/job-ready-platform/actions/runs/39715695335) | `02507f8` | pass | pass | **success** | Pre–live catalog/interaction specs |
| [39724330440](https://github.com/gaganpasupuleti/job-ready-platform/actions/runs/39724330440) | `88e18dd` | pass | pass | **134 pass, 5 fail, 6 skip** | See table above |
| [39834374466](https://github.com/gaganpasupuleti/job-ready-platform/actions/runs/39834374466) | `56172e3` | _pending_ | _pending_ | _pending_ | Current candidate |

Playwright skips (~6): `release-smoke-preview` when `E2E_SKIP_WEBSERVER` unset (expected).

## Catalog audit (authenticated script)

```powershell
$env:ROADMAP_AUDIT_EMAIL="e2e.student@jobready.dev"
$env:ROADMAP_AUDIT_PASSWORD="<from frontend/e2e/fixtures/seed-manifest.json — do not commit>"
node scripts/audit-roadmap-catalog.mjs --api http://127.0.0.1:8000
```

**Local (2026-10-22):** Auth succeeded against `127.0.0.1:8000` but **not** CI E2E backend — all **93** graph probes returned **HTTP 404** (wrong/stale API on :8000, not PR #24 seed). Totals: `graphPass=0`, `graphFail=93`, `articleUnverified=93`. **Unverified** for release on this host.

**CI:** Authoritative graph + browser totals expected from run **39834374466** + `roadmap-catalog-browser-results.json` when green.

## Production preview smoke

```powershell
cd frontend
powershell -ExecutionPolicy Bypass -File scripts/run-release-smoke.ps1 -ApiBase http://127.0.0.1:8000 -PreviewPort 4175
```

**Local preview (`88e18dd`, port 4175, `E2E_SKIP_WEBSERVER=1`):**

| Spec | Result |
|------|--------|
| `ui-cohesion.spec.ts` | **5/5 pass** (mocked API) |
| `release-smoke-preview.spec.ts` | **2/3 pass** — save/unsave OK; live roadmap article **fail** (no official graph on :8000) |

**Railway outage:** Separate from GitHub CI; blocks hosted production API/deploy verification, not Actions E2E.

## Visual evidence (mocked)

- Path: `frontend/e2e/artifacts/ui-cohesion/after/` + `meta.json` (`sha: 88e18dd`), `contrast-report.json`
- **Contrast:** All primary/action probes flagged **`unsupported_transparency`** (semi-transparent stacks) — **not** WCAG sign-off; manual screenshot review still required.
- Inspected locally: `jobs-light-1366.png`, `jobs-dark-1366.png` — readable Search control; dark theme coherent.

## Live vs mocked evidence

| Check | Mocked | Live (CI backend) |
|-------|--------|-------------------|
| UI cohesion screenshots | Local preview 4175 | CI artifact `ui-cohesion-after` |
| Roadmap catalog 93× browser | — | `roadmap-catalog-render.spec.ts` |
| Graph drag/lock/reset/viewport | — | `roadmap-graph-interaction.spec.ts` |
| Catalog audit script | — | CI-compatible API only |
| Preview smoke | Partial local | `run-release-smoke.ps1` + seed API |

## Remaining release blockers

1. **Green CI** on `56172e3` (full Playwright desktop, including 93-slug loop).
2. **Authenticated catalog audit** on **CI-equivalent** warmed backend (graph + sampled articles).
3. **Production preview smoke** end-to-end with compatible API (all scripted specs + live article).
4. **Contrast / screenshot** human sign-off (`contrast-report.json` + `ui-cohesion-after` for final SHA).
5. **Railway** recovery if production smoke against hosted API is required before merge.

Do not merge or deploy until blockers are cleared.
