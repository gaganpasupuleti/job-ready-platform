# Mistake Book (Build 10)

Aggregates incorrect practice from MCQ, SQL, prompt, scenario, interview needs-review, and coding failures (when submissions exist).

## Status

- `open` → `reviewed` → `resolved`
- Re-open on repeat failure

## MCQ retry

`POST /api/v1/practice/sessions/retry` with `{ "question_ids": [...] }`

## Backfill

Included in `python -m app.readiness.backfill`
