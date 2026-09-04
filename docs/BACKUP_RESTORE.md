# Backup and Restore

Verified as of MVP hardening (`release/mvp-hardening`). Do not claim continuous automated backups unless Railway/provider settings are confirmed in the dashboard.

## What to back up

| Data store | Contains irreplaceable user data? | Notes |
|------------|-----------------------------------|--------|
| App PostgreSQL | **Yes** | Users, practice, interviews, jobs, readiness, mistakes |
| Redis | No | Disposable cache; app degrades without it |
| SQL sandbox PostgreSQL | No | Ephemeral practice schemas; recreate from seed/problem definitions |
| Judge0 (if enabled later) | No | Stateless executor |

## Railway / provider backups

1. Open Railway project → each Postgres service → **Backups** / snapshot settings.
2. Confirm automated snapshots are enabled for the **application** Postgres (`Postgres` / primary app DB).
3. Record retention period and last successful snapshot timestamp before any production migration.

The SQL sandbox Postgres (`Postgres--4Qi` or similarly named) does not need long-term backups for MVP.

## Logical dump (recommended periodic)

Requires `pg_dump` / `psql` (PostgreSQL client tools) against the **app** database URL (never the sandbox):

```bash
# Dump
pg_dump "$DATABASE_URL_SYNC" --format=custom --file="jobready_app_$(date +%Y%m%d_%H%M%S).dump"

# Example with discrete URL (asyncpg URLs need postgresql:// for pg_dump)
pg_dump "postgresql://USER:PASS@HOST:5432/DB" -Fc -f jobready_app.dump
```

Store dumps outside the app container (object storage or encrypted disk). Do not commit dumps to git.

## Restore procedure

```bash
# 1. Create empty target database (or new Railway Postgres)
createdb jobready_restore

# 2. Restore
pg_restore --clean --if-exists --no-owner --dbname="postgresql://USER:PASS@HOST:5432/jobready_restore" jobready_app.dump

# 3. Point a staging backend at the restored DB
# 4. alembic upgrade head   # only if dump was taken mid-migration; usually already at head
# 5. Boot backend and run smoke
python scripts/smoke.py --base-url http://127.0.0.1:8000
```

### Local restore drill (performed 2026-09-04)

Without `pg_dump` on PATH, a logical round-trip was verified in the app DB:

1. Counted `domains`, `jobs`, `questions`
2. `CREATE SCHEMA restore_drill` + `CREATE TABLE ... AS SELECT * FROM domains`
3. Snapshot row count matched source
4. Dropped `restore_drill`

Result: `snapshot_match: true` (domains=6, jobs≥10, questions=408).

Re-run a full `pg_dump`/`pg_restore` drill on a machine with client tools before the first production data cutover with real users.

## Disaster recovery notes

| Failure | Action |
|---------|--------|
| App DB lost | Restore latest dump/snapshot → migrate if needed → redeploy backend → smoke |
| Redis lost | Restart Redis; no restore required |
| SQL sandbox lost | Recreate Postgres + runner role (`scripts/verify_sandbox_roles.py` / CI bootstrap SQL) |
| Frontend deploy broken | Redeploy frontend; SPA `serve -s` preserves deep links |
| Backend deploy broken | Roll back Railway deployment; keep DB intact |

## Pre-release checklist

- [ ] Confirm Railway Postgres backup/snapshot setting
- [ ] Take manual dump if real user data already exists
- [ ] Record timestamp of backup before `alembic upgrade head` on production
