# Frontend ↔ Backend Capability Register

Shared contracts and operational dependencies for JobReady Sprint 1+.

| Capability | Owner | Status | Notes |
|------------|-------|--------|-------|
| Judge0 coding execution | Backend + ops | **Disabled in prod** (expected) | FE must not fake success; workbench shows unavailable honestly |
| SQL sandbox | Backend | Live when runner/admin DSN configured | Isolated from app DB; role bootstrap on boot |
| Alembic head | Backend | `014` on PR #4 tip (`feb8d65` ancestry); `015_mistake_source_events` on learning-runtime | **Do not merge PR #3 after PR #4** — duplicate 014 risk. Close #3 or mark superseded. |
| Seed / admin bootstrap | Backend | Sprint 1 hardening | No default `admin@jobready.dev` / `Admin123!` when `APP_ENV=production` |
| Login abuse throttle | Backend | Sprint 1 | Redis-backed; degraded allow if Redis down (documented) |
| Mistake Book | Backend + FE | Sprint 1 | Live record on wrong SQL/coding submit; DB-enforced event idempotency (`mistake_source_events`) + concurrency tests |
| Readiness formula | Backend | Sprint 1 → `formula_version` | Missing required skills in denominator; unsafe aliases removed; not a hiring probability |
| Trusted lesson achievement | Backend | Sprint 1 + gap close | Do not trust client `is_correct`; require matching owned accepted SUBMIT; completion_requires_submit gated |
| AUTH-01 query cache | Frontend | Sprint 1 + gap close | Clear/scope TanStack Query on login/logout/register; stale prior-account 401 must not clear current session |
| Primary nav | Frontend | Sprint 1 | Smaller student primary set; deep links remain |
| Visual shells | Frontend | Phase foundation started | `data-shell=standard|focused|assessment` via AppLayout |
| Playground run | Backend + FE | Phase 2 checkpoint | Non-assessed; honest unavailable when Judge0 off |

## Readiness UI contract

- Response includes `formula_version` and must not be labeled as hiring probability.
- Frontend may withhold a single overall % until `formula_version` / `overall_score_ready` is present and trusted.
- Prefer demonstrated skills + gaps (`strong_skills`, `missing_skills`, `core_coverage`) over a lone headline score.

## Mistake Book retry hrefs (canonical)

| Source | `retry_href` |
|--------|----------------|
| SQL | `/practice/sql/{problem.slug}` |
| MCQ | `/practice/sessions/{session_id}/results` |
| Interview | `/interviews/review?question={question.id}` |
| Prompt | `/ai/prompts/{challenge.slug}` (or track list if slug route differs) |

## Ops follow-ups (not Sprint 1)

- Move migrate/seed/backfill off container CMD into an explicit release command.
- Gk merge order: prefer **PR #4** (includes 014) + **PR #5**; treat **PR #3** as superseded once #4 is accepted — do not land duplicate 014.
- Production redeploy only after Gk gate.
