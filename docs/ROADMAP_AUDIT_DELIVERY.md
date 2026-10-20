# Roadmap & UI audit delivery report

## Baseline

| Item | Value |
|------|--------|
| Audited commit | `24ea439f31edcdd4e90d6ed827cd081cc057cc8c` |
| Working branch | `feat/official-roadmaps-retro-ui` |
| Delivery commits | `962e657` (roadmap), `baaa4a6` (Jobs/UI), `51501e1` (delivery doc) |
| PR (not merged) | https://github.com/gaganpasupuleti/job-ready-platform/pull/23 |
| Prior baseline issue | `JobsHubPage` imported `PageIntro` / `FilterDisclosure` but files were not in the audited commit (clean checkout build break). |

Unrelated local WIP (Power BI lab, library, workshop scripts, design-reference junk) was **not** staged or committed.

## Finding status (summary)

| Area | Status |
|------|--------|
| Catalog accepts single legacy row when API misconfigured | **Fixed** — API must return ≥10 official rows; else bundled `official-roadmaps-index.json`. |
| Production graph via Vite proxy | **Fixed** — production uses API only; dev proxy remains for local work. |
| Sync `urlopen` in async route | **Fixed** — `httpx` async fetch + atomic cache write. |
| Undocumented `design-reference` only | **Fixed** — `ROADMAP_CONTENT_ROOT` / `data/roadmap-syllabus/roadmaps`; bundled catalog JSON in repo. |
| Student-facing “start backend” copy | **Fixed** — neutral topic errors. |
| Stale topic on slug change | **Fixed** — selection cleared in `useEffect`. |
| Unsafe markdown HTML | **Fixed** — DOMPurify + allowed URI scheme filter. |
| Accidental drag on explore | **Fixed** — drag gated behind “Rearrange layout”. |
| Missing outline / mobile topic sheet | **Fixed** — outline panel + mobile bottom sheet. |
| `PageIntro` / `FilterDisclosure` missing | **Fixed** — components committed. |
| Jobs clipped role pills | **Fixed** — collapsed height `4.6rem` vs pill min-height. |
| Jobs search hierarchy | **Improved** — primary keyword/location/search always visible; advanced in disclosure. |
| Full nav / logout menu redesign | **Deferred** — scope limited to shared tokens + Jobs layout. |
| Browser screenshots | **Not captured** in this session — paths reserved under `frontend/e2e-artifacts/acceptance-shots/` (create manually). |

## Content provisioning

1. **Catalog:** `backend/app/data/official-roadmap-catalog.json` and `frontend/public/official-roadmaps-index.json` (keep in sync).
2. **Graphs:** Backend downloads and caches under `backend/app/data/roadmap-cache/` (configurable via `ROADMAP_GRAPH_CACHE_DIR`, TTL `ROADMAP_GRAPH_CACHE_TTL_HOURS`).
3. **Articles (optional):** Mount syllabus at `ROADMAP_CONTENT_ROOT` pointing at `.../roadmaps/{slug}/content/*.md` (Developer Roadmap content; preserve license attribution returned in API).

## Catalog validation

```bash
node frontend/scripts/validate-roadmap-catalog.mjs
cd backend && python -m pytest tests/test_roadmap_official.py -q
```

Expected: **93** catalog slugs; validation checks slug shape and FE/BE parity.

**Limitation:** Catalog validation does **not** prove each graph or article exists — only index integrity. Graph availability requires API/cache or manual spot checks.

## Test commands run

| Command | Result |
|---------|--------|
| `npm run build` (frontend) | **Pass** (2026-10-20, Vite 8.2.2) |
| `python -m pytest tests/test_roadmap_official.py -q` | **4 passed** |
| `node frontend/scripts/validate-roadmap-catalog.mjs` | **93 entries, 0 failures** |

## Suggested PR split

1. **PR A — Roadmap reliability & viewer** — base `24ea439`, tip `962e657`.
2. **PR B — Jobs + shared retro tokens** — base `962e657`, tip `baaa4a6` (stack on A or cherry-pick UI commit).

PR links: add after `git push` + `gh pr create` (not merged).

## Reproduce (clean checkout)

```bash
git fetch origin feat/official-roadmaps-retro-ui
git checkout feat/official-roadmaps-retro-ui
cd frontend && npm ci && npm run build
cd ../backend && pip install -r requirements.txt && pytest tests/test_roadmap_official.py -q
```

Start API + frontend; open `/roadmaps`, `/roadmaps/api-design`, `/jobs`.
