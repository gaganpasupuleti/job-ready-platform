# PR #24 release audit — roadmap / UI only

**Branch:** `feat/roadmap-ui-clean`  
**PR:** https://github.com/gaganpasupuleti/job-ready-platform/pull/24  
**Candidate SHA:** _(update after push — see `git rev-parse HEAD` on branch)_  
**Status:** Open — not merged, not deployed.

## Root causes fixed (this pass)

| Issue | Root cause | Fix |
|-------|------------|-----|
| `phase6-layout` `/practice/projects` | `/api/v1/assignments` mock returned a generic object; `ManualAssignmentSection` called `.filter` on non-array → runtime error, blank shell | Mock returns `[]`; component guards with `Array.isArray` |
| Project links | API `href` pointed at legacy `/projects/...` | `ProjectsPage` links use `/practice/projects/{slug}` |
| Catalog article audit | Title-only counted as “available” | `roadmapArticleAudit.mjs` requires meaningful `markdown`; separate graph vs article exit codes |
| Release smoke script | No exit-code checks; fixed sleep; port collision risk | `run-release-smoke.ps1` checks `$LASTEXITCODE`, `--strictPort`, readiness poll, preview-only process cleanup |

## Runtime

- Node **22+** (`frontend/.nvmrc`, CI `node-version: "22"`).
- Unit tests: `npm run test:unit` (35 tests including graph + article audit).

## Clean checkout

```powershell
cd jobready-roadmap-ui-clean\frontend
npm ci
npm run lint
npm run test:unit
$env:VITE_API_BASE_URL="http://127.0.0.1:8000"
npm run build
```

## CI evidence

| Run | SHA | Frontend | Backend | Playwright | Notes |
|-----|-----|----------|---------|------------|-------|
| [39671871542](https://github.com/gaganpasupuleti/job-ready-platform/actions/runs/39671871542) | `ab2c904` | pass | pass | **129 pass, 1 fail, 3 skip** | Failed `phase6-layout` at `/practice/projects` (assignments mock) |
| _(latest)_ | _(push)_ | | | | Re-run after this commit |

Playwright skips (baseline): document from CI log when green.

## Catalog audit (authenticated)

```powershell
$env:ROADMAP_AUDIT_EMAIL="e2e.student@jobready.dev"
$env:ROADMAP_AUDIT_PASSWORD="<from frontend/e2e/fixtures/seed-manifest.json — do not commit>"
node scripts/audit-roadmap-catalog.mjs --api http://127.0.0.1:8000
```

- Graph: `GET /api/v1/roadmap/official/{slug}/graph`
- Articles: **one topic/subtopic sample per slug** (not full topic inventory)
- Report: `frontend/e2e/artifacts/roadmap-catalog-audit.json`
- Exit: `2` missing creds, `3` auth, `1` graph fail, `4` sampled article fail

**Local run (this machine):** backend not reachable — catalog totals **unverified**.

## Production preview smoke

```powershell
cd frontend
powershell -ExecutionPolicy Bypass -File scripts/run-release-smoke.ps1 -ApiBase http://127.0.0.1:8000 -PreviewPort 4173
```

Verify failure propagation:

```powershell
powershell -File scripts/run-release-smoke.ps1 -TestFailurePropagation  # expect exit 42
```

- Build with `VITE_API_BASE_URL` set **before** `npm run build`
- Preview: `http://127.0.0.1:4173` with `E2E_SKIP_WEBSERVER=1`
- Live specs: `e2e/release-smoke-preview.spec.ts` (plus scripted auth/more/roadmap-mock)

**Local run:** unverified without backend + successful build on this host.

## Visual evidence (mocked)

```powershell
$env:E2E_FORCE_FRESH_WEBSERVER="1"
$env:CI="1"
npx playwright test e2e/ui-cohesion.spec.ts --project=desktop
```

- Output: `frontend/e2e/artifacts/ui-cohesion/after/` + `meta.json`
- Themes: light + dark via `jrp-theme`; viewports 390, 768, 1280, 1366, 1920
- CI artifact: `ui-cohesion-after` (workflow upload)

## Live roadmap render (CI E2E)

- `e2e/roadmap-catalog-render.spec.ts` — catalog + `api-design` React Flow mount (live seed backend)

## Remaining blockers

1. **Green CI** on final candidate SHA (full Playwright desktop).
2. **Authenticated catalog** graph + sampled article totals on a warmed backend.
3. **Production preview smoke** executed end-to-end with live API.
4. **Screenshot review** of CI `ui-cohesion-after` artifact (human sign-off).

Do not claim release-ready until the above are pass/verified.
