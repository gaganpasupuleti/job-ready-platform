# Production Content Activation (Phase 1.1)

**Branch:** `chore/production-content-activation`  
**Base release:** `v1.0.0-mvp` (`ed6ea8b`)  
**Production migration:** `013_build10`  
**Report date:** 2026-09-05  

This is **not** Build 11. No new product domains, no LLMs, no LinkedIn scraping, no readiness formula changes.

## Tools added

| Command | Purpose |
|---------|---------|
| `python -m app.content.quiz_coverage` | Domain/category/topic MCQ coverage, bands, duplicates |
| `python -m app.jobs.coverage` | Active jobs + mapping % + URL gaps |
| `python -m app.seed.phase11_activate` | Idempotent aptitude + technical MCQ activation |
| `python -m app.jobs.import_csv <file> [--confirm]` | Preview NEW/UPDATE/DUPLICATE/INVALID; import only with `--confirm` |

CSV used: `backend/content/phase11_jobs_sample.csv` (all titles/descriptions marked **SAMPLE DEMO**).

## Quizzes — production counts (post-activation)

| Metric | Value |
|--------|------:|
| Total active MCQs | **642** |
| With explanations | **642 (100%)** |
| With valid options (≥4 opts, 1 correct) | **634 (98.8%)** |
| Exact duplicate groups | **0** |
| Topics GOOD (10+) | **24** |
| Topics THIN (5–9) | **7** |
| Topics VERY THIN (1–4) | **298** *(mostly fine-grained Cloud/DevOps/Cyber micro-topics)* |
| Topics EMPTY | **32** |

### By domain

| Domain | Active MCQs |
|--------|------------:|
| Placement (Aptitude) | **119** |
| Technical | **121** |
| AI | **117** |
| Cloud | **107** |
| DevOps | **98** |
| Cybersecurity | **80** |

### By difficulty

| Difficulty | Count |
|------------|------:|
| easy | 308 |
| medium | 261 |
| hard | 73 |

### Priority aptitude / technical topics (after activation)

All targeted topics are now **GOOD (≥10)**, e.g. percentages 12, SQL fundamentals 11, joins 11, aggregations 11, DSA basics/arrays 11, OOP principles 12, OS core-concepts 12.

### Questions added this phase

- **219** new MCQs inserted (`phase11_activate`; 1 skipped as duplicate)
- Source banks: 110 aptitude + 110 technical originals
- Duplicates removed: **0** (none found; activation is hash-idempotent)

### Remaining quiz gaps

- Many Cloud/DevOps/Cyber **leaf topics** remain VERY_THIN (often 1 question each) even though domain totals are strong.
- DATA specialty tracks (Snowflake/Spark/Flink/Databricks/Power BI/ServiceNow as dedicated MCQ topics) were **not** expanded in this phase beyond existing taxonomy/seed coverage.
- Further content can use Content Factory staging → review → publish for interview Q&A; MCQ banks remain seed/activation based.

## Jobs — production counts (post-activation)

| Metric | Value |
|--------|------:|
| Active jobs | **21** |
| Expired | **0** |
| Company mapped | **21 (100%)** |
| Role mapped | **20 (95.2%)** |
| Skill mapped | **20 (95.2%)** |
| Location present | **20 (95.2%)** |
| Valid apply URL | **21 (100%)** |
| Saved jobs (smoke) | **1** |
| Applications (smoke) | **1** |
| Status history rows | **4** (applied→screening→assessment→interview) |

### By role (active, approximate)

Data Engineer 4 · Data Analyst 3 · SOC Analyst 3 · AI/GenAI/Python/SQL/DevOps 2 each · Cloud Engineer 1 · (+1 legacy unmapped edge)

### Import this phase

| Result | Count |
|--------|------:|
| NEW | 12 |
| UPDATE | 0 |
| DUPLICATE | 0 |
| INVALID | 0 |
| Created on confirm | **12** |

All imported postings are labeled **`[SAMPLE DEMO]`** / `(SAMPLE DEMO)` — not presented as live career-site scrapes. Sources remain `manual` / `csv-import`.

## Verification performed

### Quiz API / flow

- Catalog: OK (6 domains)
- Practice session (Percentages, 5 Q): created, answered, completed, results returned
- Options do **not** leak `is_correct` before answer handling
- Exam mode (SQL fundamentals): timer/`expires_at` set; answer response has **no explanation/feedback** before completion
- Student blocked from `/admin/questions` (**403**)

### Jobs API / flow

- Browse `/jobs`, `/jobs/recommended`: OK
- Save job → `/jobs/saved`: OK
- Mark applied → `/applications`: OK
- Status transitions Applied → Screening → Assessment → Interview: OK (history persisted)
- Frontend SPA routes `/practice/aptitude`, `/jobs`, `/jobs/saved`, `/jobs/applications`, `/admin/*`: HTTP 200 (SPA shell)

### Smoke

`scripts/smoke.py --base-url https://backend-production-a0c9.up.railway.app` → **Smoke PASSED**

### Safety

- No truncate/drop/reset
- No E2E seed executed in production
- Temporary Postgres TCP proxy used for admin scripts, then **deleted**

## Acceptance checklist

### Quizzes

- [x] Meaningful content in priority domains (Placement/Technical/AI/Cloud/DevOps/Cyber totals)
- [x] No important aptitude/SQL/Python/DSA/OOP/OS priority topics empty
- [x] DB counts verified
- [x] Questions/options largely valid (98.8% quality-complete)
- [x] Practice works
- [x] Exam works (no early explanation leak)
- [x] Results work
- [ ] Full browser UI click-through (manual tomorrow pass still recommended)
- [ ] Mistake book + Retry Incorrect end-to-end (API smoke did not force wrong answers)
- [x] Admin management ACL (student denied)

### Jobs

- [x] Jobs exist in production
- [x] Company / role / skill / location mapping
- [x] Browse/search API surfaces populated
- [x] Save + application + status history
- [x] Admin CSV validate/confirm path (`--confirm`)
- [ ] Full browser filter/sort/detail UX pass (manual tomorrow)
- [ ] Job Match / Practice Missing Skills / Interview Prep deep-link click-through (manual)

## Final decision

| Area | Decision |
|------|----------|
| **QUIZZES** | **COMPLETE** for priority aptitude + technical activation; residual micro-topic thinning remains as **content expansion**, not architecture |
| **JOBS DB** | **COMPLETE** for wiring + usable sample catalog; expand with real curated career-site CSV when available |

## Ops reminder

Cutover backup was metadata-only. Prefer Railway Postgres PITR / scheduled `pg_dump` as the next ops priority.
