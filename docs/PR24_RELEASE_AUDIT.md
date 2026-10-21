# PR #24 release audit — roadmap / UI only

**Branch:** `feat/roadmap-ui-clean`  
**Do not merge** until CI is green on the release SHA.  
**Do not merge PR #23** into this release without explicit combined-scope sign-off.

## Runtime

- **Node.js 22+** (see `frontend/.nvmrc`, `package.json` `engines`, CI `node-version: "22"`).
- Unit tests use `node --experimental-strip-types` (Node 22+ only).

## #23 vs #24

| Area | PR #23 | PR #24 |
|------|--------|--------|
| Scope | Roadmaps + retro UI + Power BI WIP | Roadmap viewer + Jobs hub + nav cohesion (no Power BI test file) |
| Unit tests | Includes Power BI workshop tests when present | `roadmapOfficial`, `roadmapCatalogAudit`, `frontend-checks` only |

## Clean checkout verification

```powershell
cd jobready-roadmap-ui-clean\frontend
npm ci
npm run lint
npm run test:unit
$env:VITE_API_BASE_URL="http://127.0.0.1:8000"
npm run build
```

## Catalog audit (authenticated)

Endpoint: `GET /api/v1/roadmap/official/{slug}/graph`

```powershell
$env:ROADMAP_AUDIT_EMAIL="e2e.student@jobready.dev"
$env:ROADMAP_AUDIT_PASSWORD="<from frontend/e2e/fixtures/seed-manifest.json>"
node scripts/audit-roadmap-catalog.mjs --api http://127.0.0.1:8000
```

- Exit **2** if credentials are missing.
- Exit **3** if the token is rejected or login fails.
- Exit **1** if any slug fails graph validation or HTTP errors.
- Report: `frontend/e2e/artifacts/roadmap-catalog-audit.json` (graph vs article per slug).

## Production build smoke (not CI)

Build must see production API URL **before** `vite build`. Serve `dist` with `vite preview` on a fixed port; point Playwright at that URL and skip the dev webserver.

```powershell
cd frontend
$env:VITE_API_BASE_URL="http://127.0.0.1:8000"
$env:VITE_ENABLE_DEV_LOGIN="false"
npm run build
npm run preview -- --host 127.0.0.1 --port 4173
# separate shell:
$env:E2E_BASE_URL="http://127.0.0.1:4173"
$env:E2E_SKIP_WEBSERVER="1"
$env:E2E_API_URL="http://127.0.0.1:8000"
npx playwright test e2e/auth.spec.ts -g "AUTH-01" --project=desktop
```

Or: `powershell -File scripts/run-release-smoke.ps1`

**Do not** run smoke with only the default `5173` dev server unless `E2E_BASE_URL` explicitly targets it.

## UI cohesion screenshots

```powershell
npx playwright test e2e/ui-cohesion.spec.ts --project=desktop
```

- Output: `frontend/e2e/artifacts/ui-cohesion/after/` (+ `meta.json` with SHA, viewports, mocked data).
- Dark theme: `localStorage` key `jrp-theme` (not `classList.add('dark')` alone).
- Viewports: 390, 768, 1280 (laptop), 1366, 1920.

## Blockers (update on each release SHA)

- Full green **GitHub Actions CI** on the candidate commit.
- **Authenticated catalog** pass/fail totals recorded below.
- **Production preview smoke** with real backend when available.

### Evidence log (fill after run)

| Check | SHA / link | Result |
|-------|------------|--------|
| CI | | |
| Catalog `graphPass` / `graphFail` | | |
| Preview smoke | | |
| Screenshots | `e2e/artifacts/ui-cohesion/after/meta.json` | |
