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
