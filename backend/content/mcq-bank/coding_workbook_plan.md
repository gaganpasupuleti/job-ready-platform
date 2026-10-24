# Coding problem Excel import (proposed — not implemented)

## Sheets

| Sheet | Purpose |
|-------|---------|
| `Settings` | `schema_version`, `intended_bank_key` |
| `Coding_Problems` | Problem identity, taxonomy, statement, limits, status |
| `Coding_Test_Cases` | `problem_key`, `case_key`, I/O, visibility, order |
| `Coding_Languages` | Starter code and **server-only** reference solutions |

## Integration plan

1. Reuse `McqImportRun`-style staging/preview/publish for a separate `coding_import_runs` table.
2. Map `problem_key` to existing `CodingProblem.slug` or new `content_key` column.
3. Hidden tests and reference solutions never exposed via student APIs (same as today).
4. Pin `CodingSubmission` / exam sessions to problem revision snapshots (mirror `PracticeSessionQuestion.snapshot_json`).
5. Admin UI tab next to MCQ bank; no student upload endpoints.

## Status

Templates and schema to be added in a follow-up PR. **Coding Excel import is not active in this delivery.**
