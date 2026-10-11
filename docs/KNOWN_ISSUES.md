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
- **`validated_jobs`** — local leftover table, 0 rows, no app reader. Not the Railway `Jobs server` catalog. Do not drop it. See `docs/JOBS_PILOT_RELEASE.md`.
- **Jobs catalog approval** — Railway `public.validated_jobs` has 5321 rows and 0 explicitly approved records. `PENDING` stays unpublished. The first review batch proposes no source writes. See `docs/JOBS_REVIEW_BATCH.md`.

## Ops / environment

9. **Production deployment state** — Historical: `docs/MVP_RELEASE_AUDIT.md` (2026-09-04) found production on the 2026-08-29 image without Build 10. `docs/PRODUCTION_CONTENT_ACTIVATION.md` (2026-09-05) later recorded production migration `013_build10`. Current production deployment: Production verification pending.
10. **Local Docker Desktop** may be off — SQL sandbox E2E skips locally if sandbox unreachable; CI provides the release proof.
11. **`pg_dump` not always on PATH** — full dump/restore drill documented; logical schema snapshot drill completed locally.

## Content

12. **Content counts** — Source-level counts, topic coverage, and duplicates are in `docs/audits/2026-10-11-content-inventory/`. Production content counts: Production verification pending.
13. **Phase 11 banks are not seeded by `python -m app.seed`** — the 220 aptitude and technical definitions need `python -m app.seed.phase11_activate`.
14. **Re-seeding opens coming-soon DSA paths** — a second `python -m app.seed` marks every existing DSA path available, including the 15 declared coming soon. Shown on a disposable local database on 2026-10-11; see the audit `README.md`.
15. **Four runner sample rows never seed** — `cloud-fundamentals/architecture` and `aws`, `azure`, `gcp` `/compute` are not taxonomy topics, so the rows are skipped.

## Fixed during hardening (do not reopen without regression)

- E2E seed order (users before Build 9 job fixtures)
- WorkspaceSplit duplicate hidden panels breaking Playwright visibility
- Monaco controlled-state fills for SQL E2E
- Mistake backfill `InterviewQuestion.title` → `question_text`
- Interview E2E false positive on “not an interview score” disclaimer
