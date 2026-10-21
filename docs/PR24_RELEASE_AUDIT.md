# PR #24 release audit — roadmap / UI only

**Branch:** `feat/roadmap-ui-clean`  
**Do not merge** until this checklist is green on the release SHA.  
**Do not merge PR #23** into this release without explicit combined-scope sign-off.

## #23 vs #24 (reconcile)

| Area | PR #23 (`feat/official-roadmaps-retro-ui`) | PR #24 (`feat/roadmap-ui-clean`) |
|------|--------------------------------------------|----------------------------------|
| Scope | Roadmaps + retro UI + **Power BI workshop** commits in branch history | Roadmap viewer + Jobs hub + nav cohesion **without** Power BI WIP |
| `graphValidation.ts` | Present | Present (kept) |
| More menu | Dropdown, no Explore sheet | Same (release target) |
| Deploy env | Documented `VITE_API_BASE_URL` | Same (not `VITE_API_URL`) |

**Release vehicle:** #24 for roadmap/UI. Power BI stays on #23 / local WIP only.

## Audit items (this pass)

| # | Item | Status |
|---|------|--------|
| 1 | AUTH-01 register link (`Create one`) + same-document switch | Code fix in `e2e/helpers.ts` |
| 2 | Jobs save error + retry banner | `JobsHubPage` |
| 3 | Jobs save E2E scoped to first card | `roadmap-mock.spec.ts` |
| 4 | More menu focus + ui-cohesion More panel | `ExploreLauncher`, `ui-cohesion.spec.ts` |
| 5 | Roadmap pan/zoom preserved on article/panel toggle | Removed layout resize refit |
| 6 | Catalog auditor endpoint + auth + schema + pass rules | `audit-roadmap-catalog.mjs` → `/api/v1/roadmap/official/{slug}/graph` |
| 7 | Dark theme action-link / ghost button contrast | `jobready-retro.css` |
| 8 | Frontend unit tests in CI | `.github/workflows/ci.yml` |
| 9 | `VITE_API_BASE_URL` in build/CI | Already in workflow; see `frontend/.env.example` |
| 10 | Reconcile #23 / #24 | This doc |

## Commands (release SHA)

```powershell
cd jobready-roadmap-ui-clean\frontend
npm run lint
npm run test:unit
npm run build

# Catalog (backend on :8000, seeded user):
$env:ROADMAP_AUDIT_EMAIL="e2e.student@jobready.dev"
$env:ROADMAP_AUDIT_PASSWORD="<from e2e manifest>"
node scripts/audit-roadmap-catalog.mjs --api http://127.0.0.1:8000

# Production build smoke (local):
npm run build
$env:VITE_API_BASE_URL="http://127.0.0.1:8000"
npm run preview
npx playwright test e2e/auth.spec.ts -g "AUTH-01" --project=desktop
npx playwright test e2e/phase5-mock.spec.ts -g "More menu" --project=desktop
npx playwright test e2e/roadmap-mock.spec.ts --project=desktop
npx playwright test e2e/ui-cohesion.spec.ts --project=desktop
```

## Roadmap cache + articles (deploy)

1. `alembic upgrade head` on target DB.
2. `python backend/scripts/warm_roadmap_graph_cache.py` (or equivalent official graph warm).
3. Confirm topic markdown/content paths for official slugs on that environment.

## Remaining blockers (honest)

- **Full catalog pass** requires authenticated backend with warmed graphs; expect some slugs to fail validation until cache/content is complete.
- **Full Playwright desktop suite** must be green on CI for the release SHA (not waived).
- **Production smoke** is not automated in CI yet; run manually on `vite preview` build before deploy.
