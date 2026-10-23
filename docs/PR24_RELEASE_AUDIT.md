# PR #24 release audit — roadmap / UI only

**Branch:** `feat/roadmap-ui-clean`  
**PR:** https://github.com/gaganpasupuleti/job-ready-platform/pull/24  
**Candidate SHA:** `bd6265c` (graph cache warm in CI; lock/unlock drag fix; upstream fetch retries; builds on `929b198`/`7002aca`)  
**Status:** Open — not merged, not deployed.

## CI run 39840247519 (`4105c38` docs on `0a78a21`) — four failures (root cause)

| # | Spec | Root cause | Fix in `929b198` |
|---|------|------------|------------------|
| 1 | `roadmap-catalog-render` totals | **Test budget:** single 93-slug loop exceeded time; last slugs classified **`unavailable`** (8×) via timeout regex — not backend down | Serial **batches** (~24 slugs); per-slug `graphUrl` + HTTP status + payload validation; timeouts → **`fail`** with reason; CI artifact upload |
| 2 | `roadmap-graph-interaction` drag + edge | **Test harness:** first edge in DOM not tied to dragged topic; path `d` unchanged | Pick topic + edge from **graph API**; assert `data-id` node translate + edge `d`; camera stable during drag |
| 3 | `roadmap-graph-interaction` lock/reset | **Test harness:** locator `.draggable` lost after lock | Stable **`data-id`**; graph **translate** assertions; unlock drag + reset coords |
| 4 | `roadmap-graph-interaction` viewport | **Application:** article open triggered **fitOverview** (~scale 0.55); blanket `onViewportChange` freeze blocked user pan/zoom/Fit | **750ms layout-transition guard** on panel toggle + topic click; `onMoveStart` clears guard; skip fit during guard; no permanent freeze |

**Counts (39840247519):** Backend pass, Frontend pass, Playwright **135 passed, 4 failed, 6 skipped** (~41 min).

## Application changes (`929b198`)

- `RoadmapFlowCanvas`: replace permanent viewport freeze with short **layout-transition** preservation (`ResizeObserver` + block `fitOverview` only during guard); user pan/zoom/Fit clears guard via `onMoveStart`.
- `OfficialRoadmapView`: remove `freezeRoadmapViewportRef` (canvas owns transition guard).

## E2E changes (`929b198`)

- `roadmap-catalog-shared.ts` + batched `roadmap-catalog-render.spec.ts`: per-slug API + browser rows; favicon-only console allowlist (documented); no blanket React Flow / ResizeObserver suppression.
- `roadmap-graph-helpers.ts` + hardened `roadmap-graph-interaction.spec.ts`: API-driven node/edge ids, viewport settle polling, panel-resize stability window.
- CI: upload `roadmap-catalog-browser-results.json` on every E2E run.

## Runtime

- Node **22+** (`frontend/.nvmrc`, CI `node-version: "22"`).
- E2E API: `E2E_API_URL` / `VITE_API_BASE_URL` → `http://127.0.0.1:8000` on Actions.

## CI evidence

| Run | SHA | Frontend | Backend | Playwright | Notes |
|-----|-----|----------|---------|------------|-------|
| [39840247519](https://github.com/gaganpasupuleti/job-ready-platform/actions/runs/39840247519) | `4105c38` | pass | pass | **135 pass, 4 fail, 6 skip** | Pre-fix baseline |
| [39908836677](https://github.com/gaganpasupuleti/job-ready-platform/actions/runs/39908836677) | `7002aca` | pass | pass | **142 pass, 2 fail, 6 skip** | Catalog 7×502 upstream; lock/unlock drag coords |
| [39913806026](https://github.com/gaganpasupuleti/job-ready-platform/actions/runs/39913806026) | `bd6265c` | _pending_ | _pending_ | _pending_ | Warm cache + retries + lock test fix |

Playwright skips (~6): `release-smoke-preview` when `E2E_SKIP_WEBSERVER` unset (expected).

## Catalog audit (authenticated script)

```powershell
$env:ROADMAP_AUDIT_EMAIL="e2e.student@jobready.dev"
$env:ROADMAP_AUDIT_PASSWORD="<from frontend/e2e/fixtures/seed-manifest.json — do not commit>"
node scripts/audit-roadmap-catalog.mjs --api http://127.0.0.1:8000
```

**Local (2026-10-22):** Auth OK on `127.0.0.1:8000` but graphs **HTTP 404** for all 93 slugs — service on :8000 was **not** CI E2E seed (`GET /api/v1/roadmap/official/{slug}/graph`). **Unverified** on that host; not labeled “wrong API” without URL evidence.

**CI:** Authoritative totals from `roadmap-catalog-browser-results.json` artifact after green E2E on `929b198`.

## Production preview smoke

```powershell
cd frontend
powershell -ExecutionPolicy Bypass -File scripts/run-release-smoke.ps1 -ApiBase http://127.0.0.1:8000 -PreviewPort 4175
```

**Local preview (mocked / partial API):** `ui-cohesion` **5/5**; `release-smoke-preview` **2/3** when :8000 lacks official graphs.

**Railway:** Separate from GitHub Actions; blocks hosted production API verification only.

## Visual evidence

- CI artifact: `ui-cohesion-after` (final SHA when green).
- **Contrast:** `unsupported_transparency` = **unverified**, not pass.

## Remaining release blockers

1. **Green CI** on `929b198` — [run 39905417205](https://github.com/gaganpasupuleti/job-ready-platform/actions/runs/39905417205) must finish with full Playwright desktop green.
2. **Catalog artifact** — 93/93 `pass`, zero `unavailable`/`fail` in uploaded JSON.
3. **Authenticated catalog audit** on CI-equivalent warmed backend + sampled articles.
4. **Production preview smoke** with compatible API (save/reload, live roadmap article).
5. **Contrast / screenshot** human sign-off for final SHA.

Do not merge or deploy until blockers are cleared.
