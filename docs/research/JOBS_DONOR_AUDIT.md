# Jobs Donor Audit (codequest-jobs-ops)

**Donor repo:** https://github.com/gaganpasupuleti/codequest-jobs-ops  
**Status:** Reference only — not modified, not linked at runtime.

## Reusable ideas

- Normalized job fields: title, company, location, description, apply URL, posted date
- CSV/JSON batch import with row-level error reporting
- Content hashing for deduplication across imports
- Admin import preview before commit
- Job ↔ skill tagging for practice recommendations

## Rejected ideas

- Live scraping (LinkedIn, etc.) and CAPTCHA workarounds
- Shared database or cross-repo imports
- Provider API tokens in import payloads
- Automatic “ghosted” detection from time alone
- Job match / readiness scoring (Build 10)

## Schema mapping (donor → job-ready-platform)

| Donor concept | Platform table |
|---------------|----------------|
| Job posting | `jobs` (expanded from content-factory stub) |
| Company | `companies` (reused) |
| Skills | `job_skills` → `skills` |
| Role | `job_role_mappings` → `job_roles` |
| Import run | `job_ingestion_runs` |
| Import errors | `job_ingestion_errors` |

## Import plan

1. **Manual admin** — `/admin/jobs` create/edit/archive
2. **CSV** — `POST /admin/jobs/imports/validate` → preview → `confirm`
3. **CLI** — `python -m app.jobs.import_csv <file>` (optional wrapper around same service)
4. **Legacy donor** — one-time adapter if JSON/CSV export is obtained; no direct DB coupling

## Build 9 scope delivered

- In-platform jobs domain with Postgres only
- No Elasticsearch, no Celery worker, no external job API subscription
- Seed + CSV sufficient for product verification
