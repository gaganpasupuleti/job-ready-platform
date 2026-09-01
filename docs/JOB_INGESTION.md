# Job ingestion

## Sources (seeded)

- `manual` — admin UI
- `csv-import` — CSV upload
- `legacy-import` — donor adapter (manual, not runtime-linked)

## CSV flow

1. Template: [examples/jobs_import_template.csv](examples/jobs_import_template.csv)
2. Admin: **Imports** tab → upload → validate preview → confirm
3. CLI: `python -m app.jobs.import_csv path/to/file.csv`

## Dedup order

1. Same `source_id` + `external_id` → update
2. Same `content_hash` → skip duplicate
3. Otherwise create

`content_hash` from normalized title, company, location snippet, description snippet, external id, source slug.

## Partial imports

Bad rows recorded in `job_ingestion_errors`. Run status: `completed`, `partial`, or `failed`.

## Security

- 10 MB upload limit
- URLs: http/https only
- CSV treated as untrusted (no formula execution)
