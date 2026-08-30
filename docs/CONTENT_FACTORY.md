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

Generated content is **never** student-facing until `review_status=approved` and `is_active=true`.

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

## Student APIs

Only approved live questions:

- `GET /api/v1/interview/questions`
- `GET /api/v1/interview/questions/{slug}`
- `GET /api/v1/interview/packs`

## Future content types

`ContentType` also includes `course`, `lesson`, `practice_path`, and `project` for later Content Factory pipelines into Build 5 learning entities. Interview Q&A remains the only generated pipeline in production today.
