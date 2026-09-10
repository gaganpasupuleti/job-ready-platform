# Frontend Redesign Status

Sprint ledger for JobReady Master Plan Phase 0 + Reliability Sprint 1.

| Field | Value |
|-------|-------|
| Workstream | dual (`feature/jobready-frontend-experience-v4`, `feature/jobready-learning-runtime-v4`) |
| Phase | Phase 0 + Sprint 1 reliability gates → **Sprint 1 verification **GREEN** (2026-09-10)** |
| Base | FE: `origin/master` @ `7155ce0`; BE: includes `feb8d65` Alembic 014 tip (PR #3 supersedable by PR #4 ancestry) |
| Premium UI inspect | `feature/jobready-ui-skeleton-premium` @ `c217e4e` — frontend-only; reuse tokens/shells/nav selectively later; **not** base for Sprint 1 |
| Master merge / deploy | **blocked** — Gk owns release; do **not** merge to master or deploy from this stream |

## Sprint 1 scope

| Stream | Focus | Status |
|--------|-------|--------|
| Backend | §26 A–E: auth bootstrap, mistakes, readiness, trusted completion, alembic 014 tip | **done** on learning-runtime (`5f59544` tip as of 2026-09-10) |
| Frontend | AUTH-01 cache isolation; primary nav reduction; honesty for readiness/mistakes UI | **done** + CI/AUTH hardening commits after `85a28c5` |

## Verification evidence (Sprint 1 close-out)

| Item | Evidence | SHA / ref |
|------|----------|-----------|
| Backend tip | PR #4 head | `5f59544152a33f84ed3357c7046e15649e00a4db` |
| Frontend tip (current tip) | PR #5 prior harden | `dba3ef712c2cc5c060759ffc3758af8a38ff0bc4` |
| Alembic 014 | Present on PR #4 via `feb8d65`; **do not double-merge PR #3** into master after #4 | `014_phase12_listing_type` |
| Mistake concurrency | `mistake_source_events` unique constraint + `test_mistake_concurrent_same_event_does_not_double_count` | migration `015_mistake_source_events` on BE branch |
| AUTH-01 | Cache clear on login/register/logout; private queryKeys scoped; 401 clears cache; cross-tab storage listener; failed logout still clears | FE `useAuth` + `api/client` + `e2e/auth.spec.ts` |
| Playwright (historical red) | PR #5 @ `85a28c5`: hub path progress + AI RAG smoke; PR #4 @ `ef188d5`: logout navigation race | Fixed in follow-up commits; re-run CI required |
| Integration | Local worktree merge FE∪BE for paired verify — **not pushed**, not merged to master | see Checks |


## CI green evidence (2026-09-10 UTC)

| PR | Branch tip | Actions run | Result |
|----|------------|-------------|--------|
| #4 | `d76da28d8476fcb1976c6c7d55e22d81a6f03627` | [34431721897](https://github.com/gaganpasupuleti/job-ready-platform/actions/runs/34431721897) | pytest + lint/build + Playwright **success** |
| #5 | `00bab6388b8d6f6847898a2e9d75099fdb0d62c7` | [34431716792](https://github.com/gaganpasupuleti/job-ready-platform/actions/runs/34431716792) | pytest + lint/build + Playwright **success** |
| #3 | Alembic 014 only | � | Superseded by #4 ancestry; comment recorded; do not double-merge |
| Integ worktree | `sprint1-integ-local-only` @ `f5126f1` (local-only, not pushed) | FE+BE paired checkout | Contains 014+015 + AUTH-01 `queryClient` |

## Phase 2 � Coding experience (in progress)

| Checkpoint | Status | Notes |
|------------|--------|-------|
| Sprint 1 verification | **GREEN** | PR #4/#5 Playwright + pytest + lint |
| Python Playground (distinct from assessed) | **landed FE** | `/practice/python` + `/practice/playground` |
| Playground API | **landed BE** (learning-runtime) | `POST /api/v1/coding/playground/run` honest unavailable |
| Assessed coding workspace polish | pending | Monaco DSA already has Run/Submit/drafts; compact assessment chrome next |
| E2E | `frontend/e2e/playground.spec.ts` | load + unavailable no fake stdout |

## Explicitly deferred

- Full Master Plan Phase 2–5 (playground UX, MCQ exam shell, GSAP, whole-product restyle)
- Validated-jobs / PR #1 content expansion
- Production Railway deploy / Judge0 enablement
- Broad `learn_service.py` rewrite (only scoped `is_correct` trust fix in Sprint 1)

## Inventory (baseline)

| Area | Path | Notes |
|------|------|-------|
| Routes | `frontend/src/routes/index.tsx` | Deep links for SQL/DSA/AI/infra preserved |
| Tokens | `frontend/src/index.css` | Light density only in Sprint 1 |
| Nav | `frontend/src/components/navigation/navConfig.ts`, `Sidebar.tsx` | Primary Today set; deep links under Practice tracks / More |
| Auth cache | `frontend/src/hooks/useAuth.tsx`, `queryClient.ts`, `api/client.ts` | AUTH-01 clear on auth transitions + 401 + cross-tab |
| SQL/DSA workbench | PR #2 on master | Not regressed |

## Checks

| Check | Result | When |
|-------|--------|------|
| `npm run lint` (frontend) | pass (existing warnings only) | Sprint 1 verification |
| `npm run build` (frontend) | pass (CI) | PR #5 |
| `pytest` (backend) | Sprint 1 suites green (`test_auth_hardening`, `test_sprint1_reliability` incl. concurrency) | learning-runtime CI |
| Playwright CI | **green** on PR #4 (`d76da28`) and PR #5 (`00bab63`) � pytest + lint/build + Playwright E2E | PR #4/#5 |

## Blockers

1. **PR #3** ([Alembic 014](https://github.com/gaganpasupuleti/job-ready-platform/pull/3)) — OPEN & CI green. Safe resolution: **close or skip merge** once PR #4 lands (already contains identical 014 ancestry). Do **not** merge both as separate 014 introductions.
2. Boot-time `alembic upgrade` + seed + readiness backfill in Dockerfile remains an ops follow-up (not removed this sprint).
3. Gk gate before any master merge / Railway redeploy.

## File change log (filled as work lands)

### Backend (`feature/jobready-learning-runtime-v4`)

- `docs/FRONTEND_REDESIGN_STATUS.md`, `docs/FRONTEND_BACKEND_DEPENDENCIES.md` — Phase 0 ledgers
- `backend/app/core/config.py` — login throttle + admin bootstrap settings
- `backend/app/services/auth_throttle.py` — Redis/process-local login failure budget
- `backend/app/services/auth_service.py` — throttle on login
- `backend/app/seed/runner.py` — `ensure_seed_admin`; no default prod credentials
- `backend/app/services/mistake_service.py` — event-idempotent upsert; live helpers; retry href fixes
- `backend/alembic/versions/015_mistake_source_events.py` — DB unique event identity for concurrency
- `backend/app/services/sql_practice_service.py` / `coding_service.py` — live wrong-submit mistakes
- `backend/app/readiness/skill_mapping.py` — remove unsafe aliases
- `backend/app/readiness/formulas.py` + `readiness_service.py` + `schemas/readiness.py` — denominator + formula version
- `backend/app/services/learn_service.py` — stop trusting client `is_correct` for verified achievement
- `backend/tests/test_auth_hardening.py`, `test_sprint1_reliability.py`

### Frontend (`feature/jobready-frontend-experience-v4`)

- `frontend/src/queryClient.ts` — shared QueryClient + `clearAuthQueryCache`
- `frontend/src/App.tsx`, `hooks/useAuth.tsx` — clear cache on login/logout/register; cross-tab; failed logout
- `frontend/src/api/client.ts` — 401 clears token + query cache
- `frontend/src/components/navigation/navConfig.ts` — primary Today set + demoted deep links
- Dashboard / Mistakes / Readiness / Jobs private queryKeys scoped with `user.id`
- `frontend/src/pages/readiness/ReadinessPage.tsx` — withhold misleading overall %; formula honesty
- `frontend/src/pages/practice/PracticePathPage.tsx` — always show `N% progress` (+ test id)
- `frontend/e2e/auth.spec.ts` — AUTH-01, failed logout, stale 401, cross-tab
- `frontend/e2e/hub.spec.ts`, `smoke.spec.ts`, `helpers.ts` — Playwright stability
- Ledgers mirrored across streams for PR reviewability
