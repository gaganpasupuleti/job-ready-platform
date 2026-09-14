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

A later Saturday batch is a new directory under `content/batches/` with a new `batch_id`. Reuse item keys to update. A hash change without a version bump is rejected. An identical apply reports unchanged and does not duplicate rows. A version bump updates project text and existing milestone rows in place. It does not delete student task history.

## Verification reused or still open

- Batch plan, identical reapply, assignment isolation, and coding-lock contract were already verified. Do not rerun those as failures.
- Question snapshots keep an open attempt's stem after the live question text changes.
- Redis was not running. Cache, rate-limit, and any flow that depends on Redis were not exercised. Treat them as unverified.
- Isolated student SQL sandbox Run was not exercised in this pass. Authoring checks used a temporary schema that was dropped.
- Desktop and 390px hub screenshots were not successfully captured. Do not treat the login-page capture as visual acceptance of the hub.

## Migration

`019_learning_studio` revises `018_job_source_taxonomy`. Applied locally. Not applied to production.
