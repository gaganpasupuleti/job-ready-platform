# MVP Release Hardening — Baseline

**Branch:** `release/mvp-hardening`  
**Checkpoint (start):** `9900256` — build 10 complete  
**Current tip:** `931fcbe` — CI green after Playwright fixes  
**Recorded:** 2026-09-03

## Git

| Check | Result |
|-------|--------|
| Working tree at start | clean |
| Local HEAD (start) | `9900256` |
| `origin/master` (start) | `9900256` |
| Release branch | `release/mvp-hardening` pushed |

## GitHub Actions

### Baseline on `9900256` (master) — RED

Run: https://github.com/gaganpasupuleti/job-ready-platform/actions/runs/33594775262

| Job | Result |
|-----|--------|
| Backend | PASS |
| Frontend lint + build | PASS |
| Playwright desktop | FAIL — 40 pass / 7 fail |

### After hardening fixes (`931fcbe`) — GREEN

Run: https://github.com/gaganpasupuleti/job-ready-platform/actions/runs/33717512505

| Job | Result |
|-----|--------|
| Backend (pytest + migrate + seed + SQL sandbox) | **PASS** |
| Frontend (lint + build) | **PASS** |
| Playwright E2E desktop | **PASS** |

## Root causes fixed

1. **Jobs E2E:** Build 9 sample saved/application ran before E2E user existed; tests raced past Save/Apply.
2. **SQL visibility:** `WorkspaceSplit` double-rendered mobile+desktop; Playwright matched hidden nodes.
3. **Monaco fills:** textarea fill did not update React controlled state → `sql_error` on submit.
4. **Invalid SQL fixture:** `SELEC` hit safety; incomplete `WHERE` parse message lacked test keywords.
5. **Interview E2E:** disclaimer “not an interview score” falsely matched forbidden-phrase check.

## Local gates (start)

| Gate | Result |
|------|--------|
| `fresh_db_gate.py` | PASS |
| `npm run lint` / `build` | PASS |
| pytest parallel with fresh_db | contaminated — re-run after seed |

## Stance

CI gate cleared on `release/mvp-hardening`. Continue seed/migration/security/docs audits. **Do not merge/tag MVP until remaining checklist §§3–73 complete.**
