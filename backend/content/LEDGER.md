# Learning studio ledger

Batch `2026-09-19-saturday-001`. Local application database only. Not published to production.

## Totals

- Materials: 6 (two each for data-analyst, data-engineer, python-dev)
- Assignments: 3 (one per focus family). No due dates.
- Project: 1 (`orders-payment-quality`), 4 milestones, families data-analyst and data-engineer
- SQL problems: 3, synthetic shop dataset
- Questions: 50 (30 technical + 20 CRT). One multi-select (`da-q02`, version 2). The rest are single-select, version 1.
- Packs: 4 (`pack-data-analyst`, `pack-data-engineer`, `pack-python-dev`, `pack-crt-shared`)
- Rejected items: 0
- Families with published content: data-analyst, data-engineer, python-dev. The other 15 filter keys exist and return count 0.

## Commands

From `backend` on `feature/learn-content-be`:

```
python -m content.build_saturday_001
python scripts/content_batch.py --batch content/batches/2026-09-19-saturday-001
python scripts/content_batch.py --batch content/batches/2026-09-19-saturday-001 --apply --target local
```

`--apply` refuses a non-local database. There is no boot-time publish and no production command in this change.

A later Saturday batch is a new directory under `content/batches/` with a new `batch_id`. Reuse item keys to update. A hash change without a version bump is rejected. An identical apply reports unchanged and does not duplicate rows. A version bump updates project text and existing milestone rows in place. It does not delete student task history. Before that in-place edit, each existing progress row keeps a copy of the milestone brief. Assignment submissions keep the brief and rubric they were filed against.

SQL problems are versioned with the batch. An unchanged SQL version does not rewrite schema, seed, or expected results. A higher version replaces those for new Run and Submit calls only. Stored submission status is not recomputed. There is no in-progress SQL session: a draft is not an attempt, and the submit stores the published version it was graded against. Expected rows stay off the student payload.

## Verification

Reused: batch completeness, assignment isolation, question snapshots, and the coding-lock contract. Do not rerun those as failures.

Fresh, local only:

- Migration `020_content_version_history` applied on the local application database. Not production.
- Identical reapply after SQL tracking: materials 6, assignments 3, questions 50, packs 4, project 1, SQL 3 unchanged. Rejected 0.
- SQL version proof used the application runner and restricted runner role. Version 1 graded `[[2, 1800]]`. Version 2 changed the seed and expected result to `[[3, 2000]]`. The version-1 accepted row stayed accepted. Reapplying version 2 did not add a problem or rewrite table ids.
- The three published SQL problems were Run and Submit through the student API. Correct queries were accepted. Incorrect queries were wrong_answer. Student Run reported the restricted runner role. Expected samples were empty.
- Docker Redis and the :5433 sandbox could not be started here (no Docker CLI; WSL needs Hyper-V). A temporary local Redis on 127.0.0.1:6379 exercised the existing cache and limit code. Catalog cache TTL 300. SQL run limit 10 then 429. Held concurrency slot 429, then a run succeeded after release. Submit limit 5 was hit on the student proof account. This is not a production Redis change.
- Studio catalog returns 18 families, 6 materials, 3 assignments, 4 packs, and 15 zero counts.

## Migration

`019_learning_studio` revises `018_job_source_taxonomy`. `020_content_version_history` revises 019. Both applied locally. Neither is applied to production.

## Rotation

Completed group 1: `2026-09-19-saturday-001` (data-analyst, data-engineer, python-dev).

Next completed group after the batch below: group 3 (qa-testing, business-analyst, powerbi-analyst). Do not repeat group 2.

## Batch 2026-09-14-weekly-001

Date 2026-09-14, Asia/Kolkata, Monday. Not Saturday. Run because the weekly prompt was pasted that day. Preview only. Not production.

Rotation group 2: java-backend, frontend-react, fullstack-web. Shared CRT is a new pack, `pack-crt-2026-09-14`. `pack-crt-shared` was not rewritten.

- Materials: 6. Java class/main and blank-title methods. React props and controlled state. HTTP request reading and page/API boundary.
- Assignments: 3. Mode `manual_review`. Rubrics total 100. Private answers are in `solutions.json`, not in student briefs.
- Project: `ticket-request-log`. New. Does not extend `orders-payment-quality`. Four written milestones. Technology `http`. This app does not run Java, React, or the ticket API.
- Questions: 50. Difficulty stored as easy/medium/hard because the loader requires those names: 25 easy, 17 medium, 8 hard. That is the requested 25 beginner, 17 intermediate, 8 advanced.
- CRT table is a channel open/closed/reopened table, not the prior shop table.
- SQL problems: 3 unchanged. No new SQL milestone.
- Rejected: 0.
- Apply created the new items. An identical reapply left materials 6, assignments 3, questions 50, packs 4, project 1, and SQL 3 unchanged.
- First preview manifest sha256: `fc4a715c7f5b3f0543c5283947c83a5ba00a2e69d4a300c41ea9d4a38d671046`
- Review correction: citations that did not support the lesson claim were replaced, the six-row log was added to the material and assignment, and weak hard questions were rewritten or relabeled. Changed items are version 2. Do not publish the first preview hash.
- Reviewed manifest sha256: `44365ae5db37b6e36ddb0a6a4e166c8bef611043609f93fc7b8632ec88d8410e` — superseded. Do not publish.
- Citation closure: the HTTP class sentence now uses the RFC 9110 names verified in the plain-text body (`1xx (Informational)` through `5xx (Server Error)`), and the citation is `https://www.rfc-editor.org/rfc/rfc9110.txt`. `fs-request-response` and `fs-two-programs` are version 3. Earlier manifests `fc4a715c…` and `44365ae5…` must not be published.
- Final weekly manifest sha256: `d05331548a7d8f717696cfe1c405ded1c02b113496f07e6787d60a9e517e0e66`
- Saturday manifest sha256 is unchanged: `02d697efa25d03161f5bb096d4ed3028ed1076a319a0946bd7f569fdc2b36700`
- Local preview API on 127.0.0.1:8001. UI on 127.0.0.1:5176. Not the live site.
