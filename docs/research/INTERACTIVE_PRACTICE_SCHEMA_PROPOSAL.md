# Interactive Practice — schema proposal (Job Ready)

**Status:** design only. Do **not** migrate until a later implementation build.

Reuse existing `jobready_db`. Do **not** create a second database. Do **not** duplicate `coding_problems` as a second judge bank. Lessons and project tasks should **point at** coding (or SQL) problems when they need execution.

---

## Design principles

1. **Paths** are catalogs (Practice Hub cards): language, DSA topic, difficulty band, company, project collection.
2. **Courses** are ordered Learn experiences (modules → lessons). A path may *contain* courses and/or direct problem lists.
3. **Lessons** are pedagogical units: markdown/statement, optional MCQ, optional coding problem, hints, doubts, media.
4. **Projects** are ordered tasks; each task is a lesson-like step, often with a coding/SQL problem.
5. **Progress** is per-user on path, course, lesson, and project — separate from `coding_problem_progress` (which stays the execution truth).
6. Content is **original**, loaded via Content Factory-style JSON + admin review (extend `content_type`, do not call LLM APIs in production).

---

## Reuse as-is

| Existing | Role |
|----------|------|
| `coding_problems`, `coding_test_cases`, `coding_submissions`, `coding_submission_results` | Judge0-backed run/submit |
| `coding_problem_progress` | Solved/attempted/unsolved for a problem |
| `sql_problems` + SQL submissions | SQL tasks inside SQL/data projects |
| `skills`, `job_roles`, `companies` | Path tagging; company interview packs |
| `bookmarks` | Bookmark a lesson or problem |
| `interview_questions` + packs | Verbal interview Q&A — **not** coding interview paths |
| `questions` / practice sessions | Optional lesson type = MCQ using existing MCQ bank **or** `lesson_mcq_items` if we want course-local quizzes |
| Taxonomy `domains/categories/topics` | Optional extra tagging |

---

## Proposed tables

### `practice_paths`

Hub cards.

- `id`, `slug`, `title`, `short_description`
- `path_kind`: `language` \| `beginner_dsa` \| `data_structure` \| `algorithm` \| `difficulty` \| `star` \| `interview` \| `project_collection` \| `other`
- `difficulty_label` (easy/beginner/… our enum, not CodeChef stars)
- `cover_icon_key` (our icon name, not their assets)
- `is_published`, `sort_order`
- optional `skill_id`, `company_id`
- `estimated_hours`, `item_count_cache` (denormalized)

### `practice_path_sections`

Ordered groups on a path landing (“Google Coding Questions”, “2020 Problems”, “Level 2”).

- `path_id`, `title`, `sort_order`, `section_key`

### `practice_path_items`

What appears in the list. Polymorphic target.

- `section_id`
- `item_type`: `course` \| `lesson` \| `coding_problem` \| `sql_problem` \| `project`
- `course_id`, `lesson_id`, `coding_problem_id`, `sql_problem_id`, `project_id` (exactly one set)
- `sort_order`
- `is_preview` (free vs later gated **our** entitlement, not CodeChef Pro)

### `courses`

- `slug`, `title`, `summary`, `level` (beginner/intermediate/advanced)
- `primary_language_key` (python, java, …)
- `estimated_hours`, `is_published`
- `certificate_enabled` (boolean; certificate rows later)

### `course_modules`

- `course_id`, `slug`, `title`, `sort_order`

### `course_lessons`

- `module_id`, `slug`, `title`, `sort_order`
- `lesson_kind`: `instruction` \| `coding` \| `mcq` \| `review`
- `statement_md` (our content)
- `coding_problem_id` nullable
- `sql_problem_id` nullable
- `unlock_mode`: `always` \| `previous_complete`
- `estimated_minutes`

### `lesson_steps` (optional)

For multi-part statements without extra problems.

- `lesson_id`, `sort_order`, `title`, `body_md`

### `lesson_code_templates`

Prefer **reusing** `coding_problems.starter_code` JSON. Only add this table if a lesson needs a *different* starter than the shared problem (rare). Otherwise skip.

### `lesson_test_cases`

Do **not** duplicate judge cases. Use `coding_test_cases`. If a lesson needs pedagogical samples only, store `is_sample` on existing test cases.

### `lesson_hints`

- `lesson_id`, `sort_order`, `title`, `body_md`
- `reveal_after_failed_attempts` (int, default 0)

### `lesson_doubts`

Common doubts.

- `lesson_id`, `sort_order`, `question_text`, `answer_md`

### `lesson_resources`

Media and links (our URLs).

- `lesson_id`, `resource_kind`: `audio` \| `video` \| `image` \| `file` \| `external_doc`
- `url`, `caption`, `sort_order`
- Fields the product asked for map here: `lesson_audio_url` can be the first audio resource, not a separate column required on `course_lessons` (optional denormalized columns on lesson for convenience).

### `projects`

- `slug`, `title`, `summary`, `difficulty_label`
- `path_id` nullable (collection membership)
- `prerequisite_md` nullable

### `project_modules`

- `project_id`, `title`, `sort_order` (e.g. “Part 1–3 Loan approval”)

### `project_tasks`

- `module_id`, `lesson_id` **or** inline fields
- Recommended: each task **is** a `course_lessons` row (`lesson_kind=coding`) so the workspace is one component. Then `project_tasks.lesson_id` + `sort_order`.

### Progress

`user_course_progress`

- `user_id`, `course_id`
- `status`: `not_started` \| `in_progress` \| `completed`
- `percent`, `last_lesson_id`, `started_at`, `completed_at`

`user_lesson_progress`

- `user_id`, `lesson_id`
- `status`: `locked` \| `available` \| `in_progress` \| `completed`
- `completed_at`
- Completion rule: coding lesson complete iff linked `coding_problem_progress.status=solved` (or MCQ correct).

`user_project_progress`

- `user_id`, `project_id`, `percent`, `status`, `last_task_id`

`user_path_progress`

- `user_id`, `path_id`, `percent` (derived from items)

`lesson_attempts`

Optional if we want course-level attempts distinct from `coding_submissions`. **Prefer** coding submissions as attempts. Add this table only for MCQ-only lessons:

- `user_id`, `lesson_id`, `payload_json`, `is_correct`, `created_at`

`lesson_feedback`

- `user_id`, `lesson_id`
- `vote`: `up` \| `down` \| null
- `reported`: bool
- `note` nullable
- unique (`user_id`, `lesson_id`)

---

## Entitlements (later)

Do not copy CodeChef Pro. If we need free/paid:

- `entitlements` or flag on `practice_path_items.is_preview`
- Solutions: `solution_unlock`: `never` \| `after_solve` \| `always_for_role`

Store official solution **on `coding_problems`** (new columns `editorial_md`, `reference_solutions JSONB`) or `coding_editorials` — one editorial system for DSA + lessons.

---

## Content load

Extend Content Factory:

- `content_type`: `practice_path` \| `course` \| `lesson` \| `project` \| `lesson_doubt`
- JSON under `backend/content/generated/YYYY-MM-DD/learn_python.json` etc.
- Same validate → candidate → admin approve → publish.

No OpenAI/Gemini/Claude in the app.

---

## Proposed APIs (later)

All auth-required, student sees published + unlocked only.

```
GET  /api/v1/practice/hub                 # sections + path cards
GET  /api/v1/practice/paths/{slug}
GET  /api/v1/learn/courses/{slug}
GET  /api/v1/learn/lessons/{slug}         # statement, doubts, hints (gated), templates
POST /api/v1/learn/lessons/{id}/complete  # MCQ/review; coding uses existing submit
GET  /api/v1/learn/lessons/{id}/next
GET  /api/v1/projects/{slug}
POST /api/v1/learn/lessons/{id}/feedback
GET  /api/v1/learn/continue               # last in-progress course/path
```

Coding run/submit **unchanged**: `POST /api/v1/coding/problems/{id}/run|submit`.

Admin:

```
CRUD /api/v1/admin/learn/courses
CRUD /api/v1/admin/learn/lessons
publish path/course
```

---

## Proposed frontend routes (later)

Keep `AppLayout` + existing tokens.

| Route | Screen |
|-------|--------|
| `/practice` | Practice Hub (new; today DSA lives at `/practice/dsa`) |
| `/practice/paths/:slug` | Path landing |
| `/learn` | Course catalog |
| `/learn/courses/:slug` | Outline |
| `/learn/courses/:slug/lessons/:lessonSlug` | Split workspace |
| `/projects` | Project collections |
| `/projects/:slug` | Project landing |
| `/projects/:slug/tasks/:taskSlug` | Same workspace component as lessons |

Do not replace `/practice/dsa` in phase 1; hub **links into** existing DSA bank until paths are populated.

---

## Indexing / constraints

- Unique slugs on paths, courses, lessons, projects.
- Check constraints: exactly one target on `practice_path_items`.
- Partial unique progress tables on `(user_id, *_id)`.
