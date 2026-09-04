# MVP Release Audit — Final Report

**Recommendation: GO WITH KNOWN LIMITATIONS**

Branch: `release/mvp-hardening`  
Baseline Build 10: `9900256`  
Audit date: 2026-09-04

## Gate matrix

| Gate | Result | Evidence |
|------|--------|----------|
| CI green | **PASS** | Actions run `33717512505` — backend, frontend, Playwright |
| pytest 0 failed | **PASS** | 189 passed, 9 skipped (Judge0/live skips) |
| Full release Playwright | **PASS** | Desktop suite green in CI |
| Fresh migration/seed/backfill | **PASS** | `fresh_db_gate`; seed×2 `DIFFS NONE`; backfill×2 after interview title fix |
| Deployed SQL sandbox smoke | **PASS** | Prod `sql/execution-status` `available: true`; CI SQL suite |
| Security / privacy review | **PASS*** | Headers, JWT prod guard, ownership tests, no raw HTML; *CORS must stay pinned to FE origin on Railway |
| Backup + restore drill | **PASS*** | Docs + local logical snapshot; *full `pg_dump` when client tools available |
| Production env validated | **PARTIAL** | Vars present (JWT, DB, SQL, CORS, Judge0); **prod still on Aug 29 image** |
| Release docs current | **PASS** | README, PRODUCT_MODULES, CHANGELOG, RELEASE_NOTES, KNOWN_ISSUES, BACKUP_RESTORE |

## Why not full GO

Production Railway backend does not yet serve Build 10 (`/api/v1/readiness` and `/mistakes` → 404). Code line is release-ready; **cutover requires redeploy** from this branch + migrate/seed/backfill + re-smoke.

## Known limitations (accepted)

- Judge0 disabled
- No LLM / no job alerts / no hiring probability
- Redis optional
- JWT in localStorage (HttpOnly later)
- CSP deferred

## NO-GO checklist (none active for the release branch)

| Blocker | Status |
|---------|--------|
| DB reproducibility | Clear — seed idempotent |
| Auth/privacy issue | Clear — ownership + admin 403 coverage |
| SQL sandbox security | Clear — safety tests + CI sandbox |
| Production deep-link | Clear — SPA `/jobs`, `/readiness` HTTP 200 |
| Unexplained E2E failure | Clear — CI green |
| No tested restore path | Clear — documented + local drill |

## Pre-cutover ops (required)

1. Merge/tag `release/mvp-hardening`
2. Backup app Postgres
3. Redeploy backend + frontend
4. `alembic upgrade head` + seed/backfill as needed
5. `python scripts/smoke.py --base-url <prod-api>`
6. Spot-check readiness, mistakes, SQL run/submit

## Bugs fixed in hardening

- E2E seed user order / jobs fixtures
- WorkspaceSplit duplicate DOM
- Monaco SQL fills
- SQL parse error wording
- Interview disclaimer E2E false positive
- Mistake backfill `InterviewQuestion.question_text`
