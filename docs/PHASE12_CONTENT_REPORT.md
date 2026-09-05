# Phase 1.2 Content Expansion Report

**Branch:** `chore/real-jobs-content-expansion`  
**Base:** `master` after Phase 1.1 merge (`73856c8`, contains `24d51e7`)  
**Report date:** 2026-09-05  

Not Build 11. No LinkedIn scraping, no LLM generation, no readiness formula changes, no architecture redesign.

## Goals

1. Provenance-honest job listing types (`real` vs `sample_demo` vs curated)
2. Curated real career-board jobs (Greenhouse/Lever URLs only)
3. Targeted quiz expansion for data platforms + AI/infra thin topics
4. Sample badges / filter / external apply / practice click-throughs
5. Coverage + URL validation tooling

## Schema / tooling

| Item | Detail |
|------|--------|
| Migration | `014_phase12_listing_type` — adds `jobs.listing_type`, backfills Phase 1.1 samples → `sample_demo` |
| Enum | `real`, `sample_demo`, `curated_import`, `manual`, `career_site` |
| API | `include_sample`, `listing_type` query params; cards/detail expose `is_sample`, `source_label` |
| Coverage | `python -m app.jobs.coverage` — real vs sample, freshness, quality |
| URL check | `python -m app.jobs.validate_urls` — VALID/REDIRECT/DEAD/UNKNOWN (no auto-delete) |
| Quiz activate | `python -m app.seed.phase12_activate` |
| Real CSV | `backend/content/jobs/real/2026-09-05_curated_career_boards.csv` (**13** rows) |

## Quizzes (seed banks ready for activation)

| Bank | Count |
|------|------:|
| Data platform (Snowflake/Spark/Flink/Databricks/ETL/PBI/ServiceNow/AWS-Azure data) | **128** |
| AI + infra (embeddings/RAG/agents/Docker/K8s depth) | **86** |
| **Total Phase 1.2 bank** | **214** |

Activation is idempotent (content-hash skip). Production counts after `phase12_activate` should be recorded here once run against prod.

### Phase 1.1 baseline (prod, pre–1.2)

| Metric | Value |
|--------|------:|
| Active MCQs | **642** |
| Topics GOOD (10+) | 24 |
| Topics THIN (5–9) | 7 |

Expected after Phase 1.2 activate: ~850+ active MCQs if all 214 insert cleanly (minus any hash collisions).

## Jobs

### Policy

- Never invent real-looking vacancies.
- `listing_type=real` / `career_site` requires http(s) apply/source URL.
- If no verified public board URL → keep as `sample_demo`.

### Catalog (this branch)

| Kind | Count | Notes |
|------|------:|-------|
| Curated real (CSV) | **13** | Crunchyroll, Easyship, Coupang, Capital TG, Brillio, Cloudflare — Greenhouse/Lever |
| Phase 1.1 samples | **12** CSV / ~21 prod active (mixed with prior seeds) | Clearly SAMPLE DEMO |
| Target band | 50–100 real | **Not yet met** |

### UI

- Sample / New / Remote badges on cards
- Jobs hub: **Show sample demos** (`include_sample=1`)
- Detail: provenance line, **Apply on company site** (`rel=noopener`), practice / interview / company prep links

## Production activation checklist (after merge + Railway deploy)

```text
1. alembic upgrade head          # 014
2. python -m app.seed.phase12_activate
3. python -m app.jobs.import_csv content/jobs/real/2026-09-05_curated_career_boards.csv --confirm
4. python -m app.jobs.coverage
5. python -m app.jobs.validate_urls
6. python -m app.content.quiz_coverage
```

Use temporary Postgres TCP proxy if needed; do not reset DB; do not run E2E seed on production.

## Verdict

**NEEDS MORE REAL JOB DATA**

Phase 1.2 delivers the provenance model, tooling, quiz banks, and a first honest real-job slice (**13**). Catalog depth for a production “real jobs” experience still needs more verified Greenhouse/Lever (or equivalent official) postings toward **50–100**, plus URL freshness passes after import.

## CI / merge gate

Require on this branch before merge to `master`:

```text
Backend pytest      ✅
Frontend lint/build ✅
Playwright           ✅
```

Then deploy backend (migration + activate + import) before frontend.
