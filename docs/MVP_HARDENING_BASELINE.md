# MVP Release Hardening — Baseline (pre-fix)

**Branch:** `release/mvp-hardening`  
**Checkpoint:** `9900256` — build 10 complete - readiness job match mistakes recommendations  
**Recorded:** 2026-09-03

## Git

| Check | Result |
|-------|--------|
| Working tree | clean |
| Local HEAD | `9900256` |
| `origin/master` | `9900256` (identical) |
| Release branch | `release/mvp-hardening` pushed |

## GitHub Actions (`9900256` on master)

Run: https://github.com/gaganpasupuleti/job-ready-platform/actions/runs/33594775262

| Job | Result |
|-----|--------|
| Backend (pytest + migrate + seed + SQL sandbox) | **PASS** |
| Frontend (lint + build) | **PASS** |
| Playwright E2E desktop | **FAIL** — 40 passed, 2 skipped, **7 failed** |

### Playwright failures (CI)

1. `jobs.spec.ts` — save unsave and saved page → Saved page empty (“No saved jobs yet”)
2. `jobs.spec.ts` — mark applied and application detail → no application titles
3. `sql.spec.ts` — syntax error recovers from Running
4. `sql.spec.ts` — blocked statement is rejected safely (message present but **hidden**)
5. `sql.spec.ts` — wrong submit does not reveal expected rows
6. `sql.spec.ts` — accepted submit unlocks solution path (`Submit verdict sql error`)
7. `sql.spec.ts` — draft persists across reload (Monaco not visible)

### Root-cause hypotheses (from CI artifacts)

- **Jobs:** race — `saveBtn.count()` / apply checked before job detail finishes loading; save/apply skipped → empty lists.
- **SQL visibility:** `WorkspaceSplit` double-renders mobile (`hidden`) + desktop panels; Playwright `.first()` matches the **hidden** mobile ErrorState.
- **SQL “syntax” fixture:** `SELEC ...` is rejected by **safety** (“Only a single read-only SELECT…”), not Postgres syntax.
- **SQL submit/accepted:** Monaco `fillMonaco` (Ctrl+A + type) flaky → wrong query submitted → `sql_error`.

## Local baseline (same day)

| Gate | Result | Notes |
|------|--------|-------|
| `fresh_db_gate.py` | **PASS** (`fresh_db_gate_ok`) | Schema reset when CREATE DATABASE denied |
| `npm run lint` | **PASS** | oxlint warnings (set-state-in-effect) — non-blocking |
| `npm run build` | **PASS** | main chunk ~721 kB (Monaco) — warn only |
| `pytest` (parallel w/ fresh_db) | **5 failed** | Contaminated: fresh_db wiped DB mid-run |
| `pytest` after `seed_all` restore | practice/coding **PASS** | Need full suite re-run after seed |

## Release stance (baseline)

**NO-GO** until CI Playwright is green. Backend/frontend CI jobs already pass.

## Next fixes (in order)

1. Jobs E2E: wait for job detail controls before save/apply
2. SQL E2E: assert on **visible** results; harden Monaco fill; fix invalid-query fixture
3. Optionally dedupe `WorkspaceSplit` DOM (product a11y fix)
4. Seed idempotency hardening (fresh_db → always includes placement/technical)
5. Continue checklist §§3–73
