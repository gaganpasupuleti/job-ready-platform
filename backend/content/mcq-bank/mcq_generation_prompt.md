# MCQ generation prompt (Excel contract v1)

Generate **single_choice** rows compatible with `mcq_workbook_schema.json` and the JobReady `MCQ_Questions` sheet.

## Output

Return a JSON array of row objects (not Excel). Each object must include every required field. Use `status: "draft"` until a human editor sets `published`.

## Rules

- Assign a new stable `content_key` (lowercase, dotted); never derive identity from question text.
- Set `bank_key` to the target bank (e.g. `phase11-aptitude`).
- Use only taxonomy triples provided in the editor brief.
- Four **distinct** distractors; exactly one correct letter A–D.
- For each option, write `explanation_*` stating why that option is correct or incorrect (1–2 sentences).
- `solution_explanation`: short worked solution (not duplicate of option A text).
- Difficulty: easy | medium | hard.
- Marks 0–100, negative_marks 0–100, estimated_time_seconds 5–3600.
- No trick questions; verify arithmetic and code facts before marking published.

## Review

Schema validation does **not** prove factual correctness. A subject-matter editor must review before `status: published`.
