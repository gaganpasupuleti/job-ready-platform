# Jobs-first pilot — release candidate notes

This is not a production-ready declaration. Coding execution stays locked. Judge0 stays deferred. SQL, MCQ, and Jobs remain independent of Judge0.

Production must not depend on this Windows machine, `127.0.0.1`, or `D:\judge0-local`.

## Required environment

Set these on the API host. Do not copy this Windows `.env`.

- `APP_ENV=production`
- `DATABASE_URL` — hosted Postgres for the application database. Not the laptop.
- `JWT_SECRET_KEY` — long random value. The default is refused in production.
- `CORS_ORIGINS` — the public frontend origin only.
- `JUDGE0_ENABLED=false` — also the code default. Do not point `JUDGE0_URL` at localhost.
- `REDIS_URL` — required if SQL or coding rate limits must hold. Jobs browse does not require Redis.
- `SQL_EXECUTION_ENABLED` and sandbox URLs only if SQL Run/Submit is in the same deploy. Use a separate sandbox database, not the application database.
- Frontend build arg `VITE_API_BASE_URL` — public API origin. `VITE_ENABLE_DEV_LOGIN=false`. An empty API base URL is for the local Vite proxy only.

No new paid vendor is required for this pilot. Do not add a paid job feed or scraper. Hosting cost is whatever already pays for the API, static frontend, Postgres, and optional Redis. A Judge0 VM is not part of this deploy.

## Migration order

1. Take a backup of the application database (`pg_dump` of `jobready_db` or the hosted equivalent). Keep it off the laptop if this is the public cutover.
2. Confirm `alembic current` is `015_mistake_source_events` or an ancestor that can upgrade linearly.
3. `alembic upgrade head` applies `016_practice_answer_uniqueness` after `015`.
4. `016` deletes extra `practice_answers` rows for the same session and question, then adds `uq_practice_answer_session_question`.
   Keep rule: a finalized row (`answered_at` set) beats a draft sibling; otherwise the latest `updated_at`, then `created_at`, then `id`.
5. Do not drop `validated_jobs` to match table counts.

Rollback: restore the backup. `alembic downgrade 015_mistake_source_events` only drops the unique constraint. It does not restore deleted duplicate rows.

## Health and smoke

- `GET /api/v1/health` — database ok; judge0 disabled; redis and sql_sandbox match the env you actually configured.
- `GET /api/v1/coding/execution-status` — `available` false. Do not award coding completion.
- Signup lands on `/jobs/preferences`, then Jobs. Existing routes such as `/` stay.
- Browse, filter, open a job, save, Apply externally (no Applied status), explicit Mark applied, application appears under Applications.
- A second account does not see the first account's save or application.
- SQL Run/Submit and MCQ complete only if those services are enabled. They must not depend on Judge0.
- Admin can create, edit, and archive a job. Archive removes it from student browse.

## Explicitly not in this release

- Judge0 provisioning and live coding grades.
- Content-Security-Policy. Monaco and Vite still share one SPA document, so a strict CSP on Jobs alone is not available. API headers stay `nosniff`, `Referrer-Policy`, and `X-Frame-Options`.
- Main-bundle splitting. A production build of this candidate is one JS chunk: `dist/assets/index-BE3pcRtk.js` at 781.19 kB (gzip 204.64 kB) plus 49.22 kB CSS. Monaco is still inside that document. Splitting it is outside this pilot; Jobs does not add a paid CDN.
- Retry Incorrect.
- Dropping `validated_jobs`.
- Treating this lock as production-ready.

## `validated_jobs`

Local `jobready_db` has public.validated_jobs, owner `jobready`, 0 rows, unique `job_id`, no foreign keys and no views. Current backend models, Alembic revisions, and repo scripts do not read or write it. Treat it as leftover ingestion storage, not a required pilot table. Do not drop it only to match Alembic's table count.
