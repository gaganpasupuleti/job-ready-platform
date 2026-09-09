# Frontend Redesign Status

Sprint ledger for JobReady Master Plan Phase 0 + Reliability Sprint 1.

| Field | Value |
|-------|-------|
| Workstream | dual (`feature/jobready-frontend-experience-v4`, `feature/jobready-learning-runtime-v4`) |
| Phase | Phase 0 + Sprint 1 reliability gates |
| Base | FE: `origin/master` @ `7155ce0`; BE: `hotfix/alembic-014-production-bridge` @ `feb8d65` (014 included; PR #3 pending Gk merge) |
| Premium UI inspect | `feature/jobready-ui-skeleton-premium` @ `c217e4e` — frontend-only; reuse tokens/shells/nav selectively later; **not** base for Sprint 1 |
| Master merge / deploy | **blocked** — Gk owns release |

## Sprint 1 scope

| Stream | Focus | Status |
|--------|-------|--------|
| Backend | §26 A–E: auth bootstrap, mistakes, readiness, trusted completion, alembic 014 tip | in progress |
| Frontend | AUTH-01 cache isolation; primary nav reduction; honesty for readiness/mistakes UI | in progress |

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
| Nav | `frontend/src/components/navigation/navConfig.ts`, `Sidebar.tsx` | Reduce primary student set |
| Auth cache | `frontend/src/hooks/useAuth.tsx`, `App.tsx` QueryClient | AUTH-01 |
| SQL/DSA workbench | PR #2 on master | Do not regress |

## Checks

| Check | Result | When |
|-------|--------|------|
| `npm run lint` (frontend) | TBD | Sprint 1 exit |
| `npm run build` (frontend) | TBD | Sprint 1 exit |
| `pytest` (backend) | TBD | Sprint 1 exit |
| Playwright CI baseline | green on PR #3 | recorded Phase 0 |

## Blockers

1. **PR #3** ([Alembic 014](https://github.com/gaganpasupuleti/job-ready-platform/pull/3)) — OPEN, CI green, MERGEABLE; Gk must merge before production redeploy. Backend workstream already includes `014_phase12_listing_type` via hotfix tip.
2. Boot-time `alembic upgrade` + seed + readiness backfill in Dockerfile remains an ops follow-up (not removed this sprint).

## File change log (filled as work lands)

### Backend (`feature/jobready-learning-runtime-v4`)

- `docs/FRONTEND_REDESIGN_STATUS.md`, `docs/FRONTEND_BACKEND_DEPENDENCIES.md` — Phase 0 ledgers
- `backend/app/core/config.py` — login throttle + admin bootstrap settings
- `backend/app/services/auth_throttle.py` — Redis/process-local login failure budget
- `backend/app/services/auth_service.py` — throttle on login
- `backend/app/seed/runner.py` — `ensure_seed_admin`; no default prod credentials
- `backend/app/services/mistake_service.py` — event-idempotent upsert; live helpers; retry href fixes
- `backend/app/services/sql_practice_service.py` / `coding_service.py` — live wrong-submit mistakes
- `backend/app/readiness/skill_mapping.py` — remove unsafe aliases
- `backend/app/readiness/formulas.py` + `readiness_service.py` + `schemas/readiness.py` — denominator + formula version
- `backend/app/services/learn_service.py` — stop trusting client `is_correct` for verified achievement
- `backend/tests/test_auth_hardening.py`, `test_sprint1_reliability.py`

### Frontend (`feature/jobready-frontend-experience-v4`)

- (pending AUTH-01 + nav)
