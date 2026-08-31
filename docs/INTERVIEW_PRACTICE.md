# Interview Practice (Build 8)

Student interview preparation on **prebuilt reviewed Q&A** — no LLM evaluation.

## Principles

- Reuses `interview_questions`, `interview_answer_points`, `interview_packs`, `interview_pack_questions`
- Adds session state only (`011_build8`)
- **No** OpenAI/Gemini/Claude, speech, video, or answer auto-grading
- Metrics are **self-review**: key-point coverage, confidence, self-rating

## Modes

| Mode | Behavior |
|------|----------|
| Study | Expected answer available; learn + self-review |
| Mock | Answer hidden until **Reveal / Review My Answer** |
| Rapid review | Minimal reveal → confidence → next |

## Student routes

- `/interviews` Hub
- `/interviews/questions` Browser
- `/interviews/packs`, `/interviews/packs/:slug`
- `/interviews/session/new`
- `/interviews/sessions/:id`, `.../results`
- `/interviews/history`, `/review`, `/progress`
- `/company-prep`, `/company-prep/:slug`

## APIs

Content (unchanged): `/api/v1/interview/questions`, `/packs`

Sessions: `/api/v1/interviews/...` (hub, sessions, reveal, review, history, progress, company-prep)

Admin packs: `/api/v1/admin/interviews/packs`

## Company provenance

Company Prep shows:

> Preparation content is based on commonly relevant skills and hiring patterns. It is not affiliated with or endorsed by the listed companies.

Do **not** claim “asked by Company X” without verified provenance.

## Seed

```bash
cd backend
python -m app.seed.build8_seed
# or full: python -m app.seed
```

## Migration

`011_build8` after `010_build71` — sessions, session questions, notes, latest review snapshots.
