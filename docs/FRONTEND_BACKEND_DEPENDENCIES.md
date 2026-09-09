# Frontend ↔ Backend Capability Register

Shared contracts and operational dependencies for JobReady Sprint 1+.

| Capability | Owner | Status | Notes |
|------------|-------|--------|-------|
| Judge0 coding execution | Backend + ops | **Disabled in prod** (expected) | FE must not fake success; workbench shows unavailable honestly |
| SQL sandbox | Backend | Live when runner/admin DSN configured | Isolated from app DB; role bootstrap on boot |
| Alembic head | Backend | `014_phase12_listing_type` on hotfix/PR #3 | Prod DB already stamped 014; master lacked file until PR #3 |
| Seed / admin bootstrap | Backend | Sprint 1 hardening | No default `admin@jobready.dev` / `Admin123!` when `APP_ENV=production` |
| Login abuse throttle | Backend | Sprint 1 | Redis-backed; degraded allow if Redis down (documented) |
| Mistake Book | Backend + FE | Sprint 1 | Live record on wrong SQL submit; idempotent backfill by submission/event id |
| Readiness formula | Backend | Sprint 1 → `formula_version` | Missing required skills in denominator; unsafe aliases removed; not a hiring probability |
| Trusted lesson achievement | Backend | Sprint 1 scoped | Do not trust client `is_correct` for verified completion |
| AUTH-01 query cache | Frontend | Sprint 1 | Clear/scope TanStack Query on login/logout/register |
| Primary nav | Frontend | Sprint 1 | Smaller student primary set; deep links remain |

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
- Gk merge of PR #3 + production redeploy only after gates pass.
