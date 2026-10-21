# UI delivery — PR #24 (`feat/roadmap-ui-clean`)

**PR:** https://github.com/gaganpasupuleti/job-ready-platform/pull/24 (not merged)  
**Frontend worktree:** `jobready-roadmap-ui-clean`  
**Backend used for proxy/audit:** `New folder (5)/backend` @ `56ba9a676603fcbce6183523306098742ad422d6` (uvicorn `:8000` when running)

**Final SHA:** `6d886716f6aedc05d900c2c9d990acf89b059a3b`

## Screenshot evidence (mocked auth)

All pairs under `frontend/e2e/artifacts/ui-cohesion/{before,after}/` (identical viewports and fixtures).

| Area | Before | After |
|------|--------|-------|
| Jobs | `before/jobs-{390,768,1366,1920}.png` | `after/jobs-{390,768,1366,1920}.png` |
| Library (Resume + reading) | `before/library-book-*.png` | `after/library-book-*.png` |
| Explore + Account | `before/explore-open-1366.png`, `before/account-open-1366.png` | `after/explore-open-1366.png`, `after/account-open-1366.png` |
| Roadmap catalog | `before/roadmap-catalog-1366.png` | `after/roadmap-catalog-1366.png` |
| Roadmap + article | `before/roadmap-article-1366.png` | `after/roadmap-article-1366.png` |
| Mobile nav + article | `before/mobile-nav-390.png`, `before/roadmap-mobile-article-390.png` | `after/mobile-nav-390.png`, `after/roadmap-mobile-article-390.png` |
| Dark (Jobs) | `before/jobs-dark-1366.png` | `after/jobs-dark-1366.png` |

**How captured:** Playwright `e2e/ui-cohesion.spec.ts` with API mocks. **Before** = git worktree @ `ecbb64a` on port `5200` (`UI_COHESION_DIR` → `before/`). **After** = delivery worktree on port `5199`. Also `e2e/roadmap-mock.spec.ts` (4 tests) for roadmap viewer regression shots in `acceptance-shots/roadmap-ui/`.

**Live signed-in verification:** Not run (no credentials in CI). Mocked checks cover layout, nav, jobs hub, library detail, roadmap viewer, dark class toggle.

## Visible changes (page-by-page)

| Area | Changes |
|------|---------|
| **Global** | Warm-neutral `body` background; single token source in `index.css`; merged duplicate `:root` in `jobready-retro.css`; heading weight 600 (removed 800 overrides). |
| **Header / Explore / Account** | Account menu: token radius, no heavy drop shadow; Explore launcher unchanged functionally; mobile nav sheet unchanged. |
| **Jobs** | Shared pills/tabs/chips via retro tokens; Card/Badge/Button surfaces align with shell. |
| **Library** | Book detail Card header; Resume via `.jr-action-link` (no white-on-yellow nested primary); reading-status buttons use shared Button variants. |
| **Roadmaps** | Toolbar/canvas/article panel use same borders/radii; draggable topics + Lock layout preserved. |
| **Auth** | `auth-shell.css` + aligned `LoginPage` (ported from dev workspace). |
| **Dashboard / practice / assessment** | Inherit Card, Badge, Button, page background without page-specific overrides in this pass. |

## Shared components & CSS

| Changed | Notes |
|---------|--------|
| `Button.tsx` | `jr-btn` + explicit `data-variant` states |
| `Card.tsx` | 1px border, `--radius-md`, no ink block shadow |
| `Badge.tsx` | Muted success/warning surfaces |
| `index.css` | Page background; imports `auth-shell.css` |
| `jobready-retro.css` | Single alias `:root`; softer kickers; jobs portal tabs/pills; `.jr-action-link` |
| `jobready-v4-shell.css` | Account menu radius/shadow |
| **Removed / avoided** | Second `:root` accent overrides; `font-weight: 800` on headings; heavy card `box-shadow` on account menu |

## Browser / test results (this pass)

| Command | Result |
|---------|--------|
| `npm run build` | Pass |
| `npm run test:unit` | 30/30 pass (incl. `roadmapOfficial.test.ts`) |
| `npx playwright test e2e/roadmap-mock.spec.ts` | 4/4 pass (mocked) |
| `npx playwright test e2e/ui-cohesion.spec.ts` | 1/1 pass (mocked screenshots) |

## Roadmap catalog audit (`audit-roadmap-catalog.mjs`)

**Run:** `node frontend/scripts/audit-roadmap-catalog.mjs --api http://127.0.0.1:8000`  
**Totals:** pass **0**, fail **93**, auth **0**, unverified **0**  
**Reason:** Every slug returned HTTP **404** from `/api/v1/roadmap/official/{slug}/graph` on the backend at `56ba9a6` (graphs not served at that URL in this environment — **not** counted as passed). Full JSON: `frontend/e2e/artifacts/roadmap-catalog-audit.json`.

**Mocked graph coverage:** `api-design` fixture in Playwright — drag, article open, mobile sheet, dark viewer (see `roadmap-mock.spec.ts`).

## Blockers vs local work

| Item | Status |
|------|--------|
| Cohesive UI tokens across app | **Addressed** in this commit (not every page individually re-audited in live browser) |
| Live 93-roadmap render sign-off | **Blocked** — API 404 for official graphs on tested backend |
| Validator parity with server graphs | **Open** — audit script runs; needs backend that serves graphs + auth if required |
| Edge geometry on all large graphs (e.g. Angular/RxJS) | **Partial** — handle `-s`/`-t` mapping + unit test; live geometry unverified where graph 404 |

## Reproducible preview

```powershell
cd jobready-roadmap-ui-clean\frontend
npm run dev -- --host 127.0.0.1 --port 5175
# Backend (separate terminal):
cd "New folder (5)\backend"
# uvicorn per project README on :8000
```

Mocked screenshots:

```powershell
$env:E2E_SKIP_WEBSERVER='true'
$env:E2E_BASE_URL='http://127.0.0.1:5199'
npx playwright test e2e/ui-cohesion.spec.ts e2e/roadmap-mock.spec.ts --project=desktop
```
