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

The source catalog is the existing Railway service named `Jobs server`. That name is not the database engine. It is PostgreSQL 18, database `railway`, schema `public`, table `validated_jobs` — a different database from the application Postgres. Do not point `JOBS_SOURCE_DATABASE_URL` at the application database. Leave the password unset in git. The source session is read-only.

Publication requires an explicit `APPROVED` or `PUBLISHED` status, `manual_review_needed` false, an active link, a usable https application URL, a title and company, and source description text. `PENDING` is not approval. A 2026-09-13 read-only dry-run saw 5321 rows and 0 eligible. Do not bypass approval to fill the listing.

The Jobs server does not set those statuses. It is a Postgres volume with no triggers, functions, comments, or check constraint on `approved_status`. This application has no catalog review screen. The only documented writer is the external CodeQuest collector (`push_validated_to_job_ready`), which is not in this repository. The older sync in `aa4c311` (`docs/VALIDATED_JOBS_SYNC.md` on that commit) imported every active link and did not treat approval as a gate. That older meaning is not the publication rule. Do not invent a `REJECTED` status or treat `PENDING` as approved.

Observed pairs, 2026-09-13: `NEEDS_REVIEW` with `manual_review_needed=true` (4590); `PENDING` with the flag false (731). `APPROVED` and `PUBLISHED` have never been stored. The first review batch is `docs/JOBS_REVIEW_BATCH.md`. Its proposed source update is empty. Do not write source statuses from this app.

`--apply` refuses production and source writes. A local apply is allowed only for database `jobready_sync_disposable` on localhost, and it still does not write the source. An empty or failed fetch must not archive local jobs. A nonempty snapshot with zero eligible rows unpublishes only jobs whose `external_id` starts with `jobs-server:`.

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

Two different tables share this name.

The catalog is Railway `Jobs server` / database `railway` / `public.validated_jobs` (5321 rows as of 2026-09-13). Unique source identity is text `job_id`. The app stores a published copy as `jobs.external_id = jobs-server:{job_id}` and upserts that same row, so saved jobs and applications keep their job id. Sync credentials stay on the API host. The CSV importer is not this path: it has no approval gate.

Local `jobready_db.public.validated_jobs` is a different leftover table: owner `jobready`, 0 rows, no foreign keys, and no current app reader. Do not treat it as the catalog, and do not drop it only to match Alembic's table count.
