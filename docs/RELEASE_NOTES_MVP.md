# MVP Release Notes

**Candidate version:** `v1.0.0-mvp`  
**Code line:** `release/mvp-hardening` (from Build 10 `9900256` + hardening fixes)  
**Date:** 2026-09-04

## What works

- Auth (register/login/JWT), student vs admin authorization
- Practice hub: MCQ, coding (editor; execution gated), SQL sandbox practice
- Learn paths/courses, projects
- Prompt challenges (deterministic, no LLM)
- Cloud / DevOps / Cyber scenarios (deterministic)
- Interview packs, self-review, company prep
- Jobs browse/save/apply tracking + requirement coverage (not hiring probability)
- Readiness scoring, mistake book, next-best recommendations
- Admin content/jobs/readiness config
- CI: backend pytest, frontend lint/build, Playwright desktop E2E, SQL sandbox in CI

## Known limitations (intentional)

| Limitation | Status |
|------------|--------|
| Judge0 coding execution | **Disabled** (`JUDGE0_ENABLED=false`) — Run/Submit disabled in UI |
| External LLM | Not used — prompts/scenarios are deterministic |
| Job alerts / email digests | Not implemented |
| Hiring probability / candidate ranking | Explicitly not claimed |
| Redis | Optional; app degrades if unavailable |
| HttpOnly cookie auth | Still localStorage JWT — future migration documented |
| CSP header | Deferred (Monaco); other security headers present |

## Production cutover note

Railway production (as of 2026-09-04) still serves an **August 29** backend image: `/api/v1/readiness` and `/api/v1/mistakes` return 404. SQL sandbox status reports `available: true` on that older deploy.

**Before calling production “MVP live”:** redeploy backend + frontend from `release/mvp-hardening` (or merged `master`), run `alembic upgrade head`, seed/backfill as needed, then re-smoke.

## Smoke

```bash
python scripts/smoke.py --base-url https://<api-host>
```
