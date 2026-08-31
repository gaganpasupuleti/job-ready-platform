# Content Factory

Cursor generates interview Q&A **offline**. The production app never calls an LLM API.

```
Cursor (dev-time)
    → JSON files in backend/content/generated/
    → python -m app.content.validate
    → python -m app.content.import_batch   (staging candidates)
    → Admin review at /admin/content
    → Approved rows in interview_questions (student-facing)
```

## Daily workflow

1. `python -m app.content.gaps` — see weak skill/role coverage.
2. Generate JSON with Cursor for the gaps (SQL, Python, RAG, etc.).
3. Save under `backend/content/generated/YYYY-MM-DD/interview_<topic>.json`.
4. `python -m app.content.validate path/to/file.json`
5. `python -m app.content.import_batch path/to/file.json`  
   Staging only. Do **not** use `--approve` in unattended production.
6. Review at `/admin/content` and `/admin/content/batches/:id`.
7. Approve (publishes) or reject. Edit payload before approval if needed.
8. `python -m app.content.daily_report`

`python -m app.content.gaps` reports interview coverage plus catalog lines for projects, **AI MCQs**, **prompt challenges**, **AWS IAM / Kubernetes / Terraform / SOC / API Security**, and **incident scenarios**.

Staging kinds also include `prompt_challenge`, `ai_mcq`, `cloud_mcq`, `devops_mcq`, `cybersecurity_mcq`, `scenario_challenge`, `scenario_step`, and `scenario_option`. Production still does **not** call an LLM. No auto-publish.

See [AI_PRACTICE.md](AI_PRACTICE.md) and [PROMPT_CHALLENGES.md](PROMPT_CHALLENGES.md).

## JSON schema

Canonical file: `backend/content/generated/schema.json`.

```json
{
  "target_skill": "SQL",
  "target_role": "Data Engineer",
  "questions": [
    {
      "question_text": "...",
      "question_type": "technical",
      "difficulty": "medium",
      "experience_level": "fresher",
      "expected_answer": "...",
      "explanation": "optional",
      "key_points": ["...", "..."],
      "skills": ["SQL"],
      "roles": ["Data Analyst", "Data Engineer"],
      "companies": [],
      "jobs": [],
      "domain": "optional taxonomy name",
      "category": "optional",
      "topic": "optional"
    }
  ]
}
```

### Enums

| Field | Values |
|-------|--------|
| question_type | technical, hr, behavioral, scenario, conceptual, troubleshooting, architecture, situational |
| difficulty | easy, medium, hard |
| experience_level | fresher, junior, intermediate, senior |

Skills, roles, companies, and jobs must already exist in `jobready_db` (same Postgres). Unknown names fail validation.

## Deduplication

Question text is normalized (lowercase, trim, collapse whitespace, strip punctuation) then SHA-256 hashed. Exact hash matches are rejected. High Jaccard similarity only **warns**.

## Jobs Portal (later)

`jobs` is a catalog stub. `interview_question_jobs` maps Q&A onto jobs. A future Jobs Portal can assemble a pack: job skills + role + company → matching approved questions → `interview_packs`.

## Interview packs (Build 8)

Admin manages packs at `/admin/interviews/packs` (API `/api/v1/admin/interviews/packs`).

Before activating a pack:

- title + description required
- at least 3 **approved / active** questions mapped
- no pending/rejected questions on an active pack

Gaps reporting should consider role × skill × experience × question type × pack coverage. Session practice APIs live under `/api/v1/interviews/*` and do **not** call LLMs.

## Student APIs

Only approved live questions:

- `GET /api/v1/interview/questions`
- `GET /api/v1/interview/questions/{slug}`
- `GET /api/v1/interview/packs`
- Sessions / hub / company-prep: `/api/v1/interviews/...` (see [INTERVIEW_PRACTICE.md](INTERVIEW_PRACTICE.md))

## Learn catalog batches (Build 5.1)

`content_kind` may be `project`, `practice_path`, `lesson`, or `project_task`. Schema: `backend/content/generated/learn_schema.json`.

`python -m app.content.validate` routes by `content_kind`. Staging/publish for interview Q&A is unchanged; learn JSON is validated only until a dedicated importer is added. No automatic publishing.

`python -m app.content.gaps` also reports projects by category, paths by type, lessons, and MCQ domain counts.

## Future content types

`ContentType` includes `course`, `lesson`, `practice_path`, and `project`. Interview Q&A is the only auto-import pipeline today.
