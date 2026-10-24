# MCQ Excel question bank (admin)

## Workflow

1. **Download template** — `/admin/mcq-bank` → *Download template* (or `GET /api/v1/admin/mcq-bank/template?bank_key=...`).
2. **Edit** `MCQ_Questions` in Excel (keep `content_key` stable for corrections).
3. **Select bank** and **import mode** (`add_update` default, or `replace_bank`).
4. **Upload** `.xlsx` → validation errors appear per sheet/row/column.
5. **Preview** counts: added, updated, unchanged, archived, invalid.
6. **Publish** — atomic; invalid workbooks cannot partially publish.
7. **History / rollback** — published runs can be rolled back to pre-import snapshots (updates/archives; newly added keys in that run are not auto-deleted).

Students receive published questions after catalog cache invalidation and `GET /api/v1/practice/content-version` bumps. Ongoing practice sessions keep `snapshot_json` from session start.

## Import modes

| Mode | Behaviour |
|------|-----------|
| `add_update` | Insert new keys; update keys in this bank; leave omitted keys unchanged. |
| `replace_bank` | Same as above, plus **archive** published questions in this bank that are omitted from the file. Requires preview confirmation; empty file needs `allow_empty_replace`. |

Cross-bank `content_key` collisions are rejected.

## Files

- Template generator: `backend/app/content/mcq_workbook_template.py`
- JSON Schema: `backend/content/mcq-bank/mcq_workbook_schema.json`
- Generation prompt: `backend/content/mcq-bank/mcq_generation_prompt.md`
- Coding follow-up: `backend/content/mcq-bank/coding_workbook_plan.md`

## Legacy questions

Questions without per-option explanations remain valid; practice feedback shows the general `solution_explanation` only. New **published** imports must include all four option explanations plus the worked solution.
