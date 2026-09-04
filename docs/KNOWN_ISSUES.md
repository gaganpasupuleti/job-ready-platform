# Known Issues — MVP

## Intentional / accepted

1. **Judge0 disabled** — coding Run/Submit unavailable; banner expected; live Judge0 tests skip.
2. **No external LLM** — prompt/scenario engines are rule-based.
3. **No job alerts** — users must browse/save jobs manually.
4. **Redis optional** — catalog cache may skip when Redis is down.
5. **JWT in localStorage** — not HttpOnly cookies yet.
6. **CSP not set** — Monaco/Vite asset risk; `nosniff`, `Referrer-Policy`, `X-Frame-Options` are set.
7. **Leaderboard / contests / assessments** — future placeholders, not product features.
8. **Main JS bundle ~700kB+** — Monaco; lazy-loading deferred.

## Ops / environment

9. **Railway production not yet on Build 10** — last successful backend deploy ~2026-08-29; readiness/mistakes APIs absent until redeploy.
10. **Local Docker Desktop** may be off — SQL sandbox E2E skips locally if sandbox unreachable; CI provides the release proof.
11. **`pg_dump` not always on PATH** — full dump/restore drill documented; logical schema snapshot drill completed locally.

## Fixed during hardening (do not reopen without regression)

- E2E seed order (users before Build 9 job fixtures)
- WorkspaceSplit duplicate hidden panels breaking Playwright visibility
- Monaco controlled-state fills for SQL E2E
- Mistake backfill `InterviewQuestion.title` → `question_text`
- Interview E2E false positive on “not an interview score” disclaimer
