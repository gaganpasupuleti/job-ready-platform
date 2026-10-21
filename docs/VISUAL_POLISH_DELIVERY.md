# Visual polish delivery (PR #24)

## Branch and commits

| Item | Value |
|------|--------|
| Branch | `feat/roadmap-ui-clean` |
| Base (PR #24) | `master` |
| Prior audit head | `d9709ea6e0cae1a185e60747391623a88a545e00` |
| Polish head | *(see `git rev-parse HEAD` after push)* |
| PR | [#24](https://github.com/gaganpasupuleti/job-ready-platform/pull/24) — **not merged** |

## Screenshot vs runtime discrepancy (resolved for evaluation)

The five user-supplied screenshots were captured from the **main workspace** on `feat/official-roadmaps-retro-ui` (e.g. **Reports** in top nav, **Career roadmap** in More). PR #24’s `feat/roadmap-ui-clean` intentionally omits some Power BI / Reports WIP routes.

| Environment | Path | Branch | Nav note |
|-------------|------|--------|----------|
| User screenshots | `New folder (5)` | `feat/official-roadmaps-retro-ui` | Reports + extended More |
| PR #24 verification | `jobready-roadmap-ui-clean` worktree | `feat/roadmap-ui-clean` | Jobs-first nav, no Reports |

Polish CSS/component changes apply on **clean** branch first; mirror the same files onto `feat/official-roadmaps-retro-ui` for local dev parity without removing retro-only routes.

## Finding register (supplied screenshots → fix)

### 1. Roadmap handles, dots, connectors (`/roadmaps/:slug`)

| Field | Before | After |
|-------|--------|-------|
| Issue | Visible black handle dots; loud blue edges; busy grid | Handles hidden in explore mode; softer edges/grid |
| Handles | React Flow defaults + weak `.ors-handle` | `.ors-canvas--explore .react-flow__handle` forced transparent; editing mode shows handles |
| Edges | `#2B78E4` @ 3.5px (`graph.ts`) | Default `#5a6f7f` @ 2px + CSS `stroke-width: 2` |
| Grid | 12% dot mix | 5% mix; `--ors-paper-dot` |
| Component/CSS | `OfficialRoadmapView.tsx`, `official-roadmap.css`, `graph.ts` | |
| Evidence | `frontend/e2e/artifacts/acceptance-shots/roadmap-ui/roadmap-viewer-1366.png` (mocked, post-polish) | |

### 2. Main nav + More (`/` … `/jobs`)

| Field | Detail |
|-------|--------|
| Issue | Competing highlights; More not showing owned route; Admin parent active for all `/admin/*` |
| Fix | `isMoreNavRouteActive`, `aria-current` + `.is-route-active` underline on More; Admin link active only on `/admin/questions`; menus close on route change; Account closes More |
| CSS | `jobready-v4-shell.css` — scrollable More panel, shared underline with primary nav |
| Evidence | Manual / mocked navigation; re-check on retro branch for Reports row |

### 3. Library Resume white-on-yellow (`/library/:id`)

| Field | Before | After |
|-------|--------|-------|
| Issue | `Link` > `Button variant="primary"` + `.jr-retro-btn:hover { background: milestone }` → **white text on yellow** |
| Resume FG/BG (broken hover) | `#ffffff` on `#fff200` (~1.1:1) | N/A — pattern removed |
| Resume (fixed) | — | `.jr-action-link`: `#ffffff` on `var(--color-accent)` (~4.5:1+); secondary link uses dark text on surface |
| Component | `LibraryBookPage.tsx`, `Button.tsx`, `jobready-retro.css` | |

### 4. Jobs heading / tabs / search (`/jobs`)

| Field | Detail |
|-------|--------|
| Issue | Heavy retro borders/shadows; tab underline competes with content |
| Fix | Thinner borders, accent tab underline (2px), no hover lift on summary cards (`jobready-retro.css`, `jobready-v4-shell.css`) |
| Behavior | Save/Unsave error copy unchanged; mocked e2e still passes |
| Evidence | `jobs-save-error-1366.png` in acceptance shots |

### 5. Account menu + header controls

| Field | Detail |
|-------|--------|
| Issue | Account vs More both open; icon buttons inherited retro yellow hover |
| Fix | `setMoreOpen(false)` when opening account; ghost/icon buttons use muted hover only |
| CSS | Shared popover styles already aligned in v4-shell |

## Shared tokens / components changed

- `frontend/src/components/common/Button.tsx` — `jr-btn` + `data-variant` explicit state pairs
- `frontend/src/styles/jobready-retro.css` — restrained palette, `--jr-selection-bg`, `.jr-action-link`, removed generic yellow hover
- `frontend/src/styles/jobready-v4-shell.css` — More panel viewport bounds; no card hover transform
- Roadmap: `official-roadmap.css`, `graph.ts`, `OfficialRoadmapView.tsx`

## Tests (mocked vs live)

| Check | Result |
|-------|--------|
| `npm run build` | Pass |
| `npx vitest run` (node:test modules) | Pass (roadmap graph helpers) |
| `CI=true npx playwright test e2e/roadmap-mock.spec.ts` | **4/4 pass** (fresh Vite on 5173) |
| Live login + full 93-path graphs | **Not run** — requires credentials and provisioned graphs |

**Note:** Running Playwright against a **stale** dev server on port 5173 (other branch) fails topic-search and jobs-save tests. Always use `CI=true` or restart Vite from this commit.

Console: React Flow `#004` parent size warning may still appear on first paint; layout uses `min-height: 420px` on `.ors-layout` / canvas — re-check if warning persists in production build.

## Remaining audit blockers (unchanged)

- Catalog validator does not prove every official graph is fetchable on the server.
- Legacy assembly endpoint / draft graphs without bundled content.
- Full live graph + topic provisioning for all 93 paths.
- Independent review of PR #24 before merge.

## Screenshot mapping (user attachments)

1. Roadmap handles/connectors → §1 + `roadmap-viewer-1366.png`
2. More dropdown → §2 (retro branch shows Reports; clean branch does not)
3. Library Resume → §3
4. Jobs layout → §4
5. Account/header → §5
