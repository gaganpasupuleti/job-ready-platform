# Jobs Portal (Build 9)

Student job browse, save, apply, and application tracking — all inside job-ready-platform Postgres.

## Routes

- `/jobs` — Hub + browse
- `/jobs/:jobId` — Detail
- `/jobs/recommended` — Relevant jobs (no match %)
- `/jobs/saved`
- `/jobs/applications`
- `/jobs/applications/:applicationId`

## APIs

- `/api/v1/jobs/*` — listings, save, apply, summary, recommended
- `/api/v1/applications/*` — tracker, status history
- `/api/v1/admin/jobs/*` — CRUD, CSV import

## Principles

- No readiness score or job-match percentage (Build 10)
- No live scraping on student page load
- No LLM skill extraction
- Dedup via `content_hash` + `external_id`
- Company prep links only when company is mapped

See also: [JOB_INGESTION.md](JOB_INGESTION.md), [APPLICATION_TRACKING.md](APPLICATION_TRACKING.md)
