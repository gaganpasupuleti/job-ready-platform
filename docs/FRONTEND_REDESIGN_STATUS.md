# Frontend Redesign Status

Sprint ledger for JobReady Master Plan Phase 0 + Reliability Sprint 1.

| Field | Value |
|-------|-------|
| Workstream | dual (`feature/jobready-frontend-experience-v4`, `feature/jobready-learning-runtime-v4`) |
| Phase | Phase 0 + Sprint 1 reliability gates ? **Sprint 1 verification **GREEN** (2026-09-10)** |
| Base | FE: `origin/master` @ `7155ce0`; BE: includes `feb8d65` Alembic 014 tip (PR #3 supersedable by PR #4 ancestry) |
| Premium UI inspect | `feature/jobready-ui-skeleton-premium` @ `c217e4e` ? frontend-only; reuse tokens/shells/nav selectively later; **not** base for Sprint 1 |
| Master merge / deploy | **blocked** ? Gk owns release; do **not** merge to master or deploy from this stream |

## Sprint 1 scope

| Stream | Focus | Status |
|--------|-------|--------|
| Backend | ?26 A?E: auth bootstrap, mistakes, readiness, trusted completion, alembic 014 tip | **done** on learning-runtime (`5f59544` tip as of 2026-09-10) |
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
| Integration | Local worktree merge FE?BE for paired verify ? **not pushed**, not merged to master | see Checks |


## CI green evidence (2026-09-10 UTC)

| PR | Branch tip | Actions run | Result |
|----|------------|-------------|--------|
| #4 | `d76da28d8476fcb1976c6c7d55e22d81a6f03627` | [34431721897](https://github.com/gaganpasupuleti/job-ready-platform/actions/runs/34431721897) | pytest + lint/build + Playwright **success** |
| #5 | `00bab6388b8d6f6847898a2e9d75099fdb0d62c7` | [34431716792](https://github.com/gaganpasupuleti/job-ready-platform/actions/runs/34431716792) | pytest + lint/build + Playwright **success** |
| #3 | Alembic 014 only | ? | Superseded by #4 ancestry; comment recorded; do not double-merge |
| Integ worktree | `sprint1-integ-local-only` @ `f5126f1` (local-only, not pushed) | FE+BE paired checkout | Contains 014+015 + AUTH-01 `queryClient` |

## Phase 2 ? Coding experience (in progress)

| Checkpoint | Status | Notes |
|------------|--------|-------|
| Sprint 1 verification | **GREEN** (prior CI) | PR #4/#5 Playwright + pytest + lint |
| Verification gap close-out (2026-09-10) | **landed** | BE `c6a1666` / `db55bab`; FE `eb9f871` / `87f7018` |
| Python Playground (distinct from assessed) | **landed FE** | `/practice/python` + `/practice/playground` |
| Playground API | **landed BE** (learning-runtime) | `POST /api/v1/coding/playground/run` honest unavailable |
| Visual foundation (compact shells/tokens) | **started FE** | Source Sans 3, denser controls, standard/focused/assessment shells |
| Assessed coding workspace polish | pending | Monaco DSA already has Run/Submit/drafts; compact assessment chrome next |
| E2E | `frontend/e2e/playground.spec.ts` | main-scoped h1; unavailable no fake stdout |

## Verification gap close-out (this checkpoint)

| Gap | Result | Evidence |
|-----|--------|----------|
| Playground heading | Fixed | Header title is `<p>`; page keeps single main `h1`; e2e uses `getByRole('main').getByRole('heading', { level: 1 })` |
| AUTH-01 | Strengthened | Real `/applications` note via API; SPA switch; delayed A success + A 401 after B; no sessionStorage-only markers; logout requires visible Logout |
| Stale 401 after switch | Fixed | `api/client.ts` ignores 401 when request Authorization does not match current token |
| Lesson verification | Replaced | `test_lesson_attempt_verification_via_service` hits `/lessons/{id}/attempt` + completion gate |
| Mistake concurrency | Extended | Same-event replay retained; distinct-event barrier race + item-create IntegrityError recovery |

## Explicitly deferred

- Full Master Plan Phase 2?5 remainder (MCQ exam shell polish, GSAP, whole-product restyle)
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
| Local stack restore | **up** | Native Postgres `:5432`; portable Redis `:6379`; SQL sandbox DB on same Postgres (`:5432`, not Docker `:5433`); uvicorn `:8000`; Vite `:5173` |
| Health | `database/redis/sql_sandbox=ok`, `judge0=disabled` | `GET /api/v1/health` |
| Documented `docker compose` | **unavailable locally** | `docker` not on PATH; WSL2 Hyper-V not installed (`HCS_E_HYPERV_NOT_INSTALLED`) |
| `pytest` sprint1 + playground + auth hardening | **12 passed** | integ worktree against local DB |
| Playwright auth + playground (desktop) | **11 passed** | AUTH-01 fixed (probe `/api/v1/...` + query marker); live stack |
| Frontend tip | `5352613` | PR #5 |
| Backend tip | `dbc03e7` | PR #4 |
| Integration revision | `16d40b9` (`tmp/sprint1-integration`, local-only) | BE∪FE |

## Uvicorn exit root cause (prior session)

Fatal bind error was **not** Redis. Evidence from failed start attempt: `Application startup complete` then `ERROR: [Errno 10048] ... bind on address ('127.0.0.1', 8000)` (port already held by a hung python). Redis `ConnectionError` lines were non-fatal warnings in lifespan. Later healthy process was killed while hung (`Stop-Process`), producing clean exit.

## Blockers

1. **PR #3** (Alembic 014) — OPEN. Prefer close/skip once PR #4 lands; do not double-merge 014.
2. Docker Desktop / WSL2 Hyper-V missing — cannot use documented `infra/docker-compose.yml` until installed; local workaround uses native Postgres + portable Redis.
3. Gk gate before any master merge / Railway redeploy.

## File change log (filled as work lands)

### Backend (`feature/jobready-learning-runtime-v4`)

- `docs/FRONTEND_REDESIGN_STATUS.md`, `docs/FRONTEND_BACKEND_DEPENDENCIES.md` ? Phase 0 ledgers
- `backend/app/core/config.py` ? login throttle + admin bootstrap settings
- `backend/app/services/auth_throttle.py` ? Redis/process-local login failure budget
- `backend/app/services/auth_service.py` ? throttle on login
- `backend/app/seed/runner.py` ? `ensure_seed_admin`; no default prod credentials
- `backend/app/services/mistake_service.py` ? event-idempotent upsert; live helpers; retry href fixes
- `backend/alembic/versions/015_mistake_source_events.py` ? DB unique event identity for concurrency
- `backend/app/services/sql_practice_service.py` / `coding_service.py` ? live wrong-submit mistakes
- `backend/app/readiness/skill_mapping.py` ? remove unsafe aliases
- `backend/app/readiness/formulas.py` + `readiness_service.py` + `schemas/readiness.py` ? denominator + formula version
- `backend/app/services/learn_service.py` ? stop trusting client `is_correct` for verified achievement
- `backend/tests/test_auth_hardening.py`, `test_sprint1_reliability.py`

### Frontend (`feature/jobready-frontend-experience-v4`)

- `frontend/src/queryClient.ts` ? shared QueryClient + `clearAuthQueryCache`
- `frontend/src/App.tsx`, `hooks/useAuth.tsx` ? clear cache on login/logout/register; cross-tab; failed logout
- `frontend/src/api/client.ts` ? 401 clears token + query cache
- `frontend/src/components/navigation/navConfig.ts` ? primary Today set + demoted deep links
- Dashboard / Mistakes / Readiness / Jobs private queryKeys scoped with `user.id`
- `frontend/src/pages/readiness/ReadinessPage.tsx` ? withhold misleading overall %; formula honesty
- `frontend/src/pages/practice/PracticePathPage.tsx` ? always show `N% progress` (+ test id)
- `frontend/e2e/auth.spec.ts` ? AUTH-01, failed logout, stale 401, cross-tab
- `frontend/e2e/hub.spec.ts`, `smoke.spec.ts`, `helpers.ts` ? Playwright stability
- Ledgers mirrored across streams for PR reviewability
