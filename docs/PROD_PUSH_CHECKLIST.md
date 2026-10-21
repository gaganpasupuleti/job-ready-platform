# Production push checklist — roadmaps + Jobs UI (2026-10-21)

## Ship branch

| Item | Value |
|------|--------|
| **Primary branch** | `feat/official-roadmaps-retro-ui` |
| **GitHub PR** | [#23](https://github.com/gaganpasupuleti/job-ready-platform/pull/23) (full audit delivery) |
| **Clean UI PR** | [#24](https://github.com/gaganpasupuleti/job-ready-platform/pull/24) — sync’d from main workspace; prefer merging **#23** or rebasing #24 onto #23 HEAD |
| **Base** | `master` @ `bd7269c` |

## Local verification (main workspace)

| Check | Result |
|-------|--------|
| `frontend` `npm run lint` | Pass (warnings only) |
| `frontend` `npm run build` | Pass |
| `frontend` `npm run test:unit` | **29/29** pass |
| `jobready-roadmap-ui-clean/frontend` `npm run build` | Run after sync (same tree as main UI slice) |
| `backend` full `pytest` | Run before merge; CI last run on #24: **338 passed, 1 failed** (`test_library_storage` — registration policy 403, likely env/fixture; not roadmap/Jobs UI) |

## Included in this push (committed slice)

- **Nav:** `More` dropdown (no Explore search / bottom sheet), `exploreNavRegistry`, `explore-nav.css`
- **Jobs:** compact cards, default sort by JobReady `first_seen_at`, hub chrome (`AppLayout`, `PageIntro`, retro CSS)
- **Roadmaps:** viewer fit/zoom (`RoadmapFlowCanvas`), handles/graph polish, catalog service tweaks
- **Backend:** `job_service.py` browse sort, `roadmap.py` + optional `warm_roadmap_graph_cache.py`

## Explicitly out of scope (leave uncommitted on main)

- `backend/design-reference/` (binaries, torrents, reference clones)
- Power BI workshop WIP (`frontend/pages/reports`, `executive-sales-toast-lab`, lab scripts) unless you intend a separate reports release
- `.agents/`, `.superdesign/`, snapshot zips, CSV evidence dumps

## Pre-deploy (production)

1. Merge PR to `master` (or tag release branch).
2. Run DB migrations as usual (`alembic upgrade head`).
3. **Roadmap graphs:** warm cache if official graphs 404 in prod:
   ```powershell
   cd backend
   python scripts/warm_roadmap_graph_cache.py
   ```
4. Deploy backend + frontend; set `VITE_API_URL` / Google client ID per existing runbook.
5. Smoke: `/jobs` (browse + family pills), `/roadmaps` (catalog), `/roadmaps/api-design` (fit view + topic click), **More** menu destinations.

## Post-merge

- Close or retarget **#24** if **#23** supersedes it.
- Re-run GitHub Actions on `master`; fix `test_library_storage` if it fails on main (registration open in test env).
