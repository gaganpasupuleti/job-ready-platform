# Known Issues — MVP

## Intentional / accepted

1. **Judge0 disabled** — coding Run/Submit unavailable; banner expected; live Judge0 tests skip.
2. **No external LLM** — prompt/scenario engines are rule-based.
3. **No job alerts** — users must browse/save jobs manually.
4. **Redis optional** — catalog cache may skip when Redis is down.
5. **JWT in localStorage** — not HttpOnly cookies yet.
6. **CSP not set** — scoped out of the jobs-first pilot. Monaco and the Jobs shell share one HTML document, so a Jobs-only CSP is not available. `nosniff`, `Referrer-Policy`, and `X-Frame-Options` stay set.
7. **Leaderboard / contests / assessments** — future placeholders, not product features.
8. **Main JS bundle** — measured production build is one 781 kB JS chunk (gzip 205 kB). Monaco is in that document. Splitting is outside the jobs-first pilot.

Scoped with the jobs-first candidate (do not treat coding lock as production-ready):

- **Retry Incorrect** — still deferred. It does not block signup → Jobs → save → explicit Mark applied.
- **`validated_jobs`** — leftover table, 0 rows locally, no current app consumer. Do not drop it to match Alembic table counts. See `docs/JOBS_PILOT_RELEASE.md`.

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
