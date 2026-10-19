# JobReady system flow

This is the live product as it runs in production. It covers the student app, the API, the databases, and the engines that sit beside them. Skip `MAIN_PRODUCT_FLOW.md`. That file only shows screens.

Production today:

- Browser app: `https://frontend-production-f65c0.up.railway.app`
- API: `https://backend-production-a0c9.up.railway.app`
- Every student call is `https://backend-production-a0c9.up.railway.app/api/v1/...`
- The frontend bakes `VITE_API_BASE_URL` in at build time. It does not discover the API at runtime.

---

## 1. What is running

Railway project `job-ready-platform`, production environment. Five services. Only two of them are apps.

| Service | What it is | What it is allowed to do |
|---|---|---|
| frontend | React 19 + Vite, served as a static SPA (`serve -s dist`) | Draw screens. Call the API. Hold the login token in `localStorage`. |
| backend | FastAPI modular monolith | Auth, catalogs, sessions, scoring, job reads, admin writes. |
| Postgres | Application database | Users, questions, sessions, progress, saved jobs, applications, course progress. |
| Redis | Coordination store | SQL and coding rate limits and concurrency slots. Not a queue of student code. |
| Jobs server | A second Postgres, table `public.validated_jobs` | Source catalog of live listings. The app reads it. The app must never write it. |

Two more engines exist in the design but are not inside the FastAPI process:

- SQL sandbox. A separate Postgres. The runner role can only read the problem schema. The admin role seeds tables. The application database is not the sandbox.
- Judge0. A separate code runner. Student Python, Java, C++, and JavaScript must never execute inside FastAPI. Production ships with Judge0 off until a privileged runner exists. The playground and coding Run buttons stay disabled when `execution-status` says unavailable.

There is no LLM in the student path. Prompt challenges and Cloud / DevOps / Cybersecurity scenarios are graded by deterministic checks written into the content.

---

## 2. How one click becomes data

1. The student is on a React route under `AppLayout`. Guest routes (`/login`, `/register`) sit outside that shell.
2. The page asks TanStack Query to load data. The query function lives in `frontend/src/services/*`.
3. Axios (`frontend/src/api/client.ts`) sends `Authorization: Bearer <token>` if `localStorage` has one. Timeout is 15 seconds. Base URL is `VITE_API_BASE_URL`.
4. FastAPI matches `/api/v1/...` in `backend/app/api/v1/router.py`. The router is thin. It calls a service. The service reads or writes Postgres through SQLAlchemy.
5. The JSON comes back. React Query caches it. A 401 that belongs to the current token clears the token and the cache and sends the student to `/login`.

Logout does the same clear even if the logout API call fails. A stale 401 from a previous account is ignored if the bearer no longer matches the token now in storage.

Admin and trainer accounts use the same login. `AdminRoute` checks `user.role`. Anyone else who opens `/admin/...` is sent to `/`.

---

## 3. Sign-in

Screens: `/login`, `/register`.

API:

- `POST /api/v1/auth/register` creates the user and returns a JWT.
- `POST /api/v1/auth/login` checks email and password and returns a JWT.
- `GET /api/v1/auth/me` is how the app knows who is signed in after a refresh.
- `POST /api/v1/auth/logout` tells the server the session is done. The browser still clears local state if that call fails.

After a successful sign-in, a first-time jobs onboarding flag sends the student to `/jobs/preferences`. Otherwise they land on `/jobs`. Preferences are `GET` and `PUT /api/v1/jobs/preferences` and live in the application Postgres, not in the Jobs server.

The token is an access token in `localStorage`. It is not an HttpOnly cookie.

---

## 4. The student spine

The product is jobs-first. Everything else exists to close a skill gap and come back to a listing.

1. Sign in.
2. Set job preferences.
3. Browse live jobs.
4. Open a listing. Save it, or mark it applied.
5. The listing can point at practice for a missing skill.
6. Practice, learn, review mistakes, or check readiness.
7. Return to Jobs. Relevant jobs and applications are still the same job objects.

The top bar is only a door. Jobs, Overview, Practice, Learn, Playground, Assessments, and Review each open one area. More does not create a second product. It opens the rest of the same areas.

---

## 5. Jobs

### Screens

- `/jobs` browse. Family pills, keyword, skill, location, sort, pagination, URL state. Those filters are not separate routes.
- `/jobs/recommended` relevant roles. Relevance, not a match percentage.
- `/jobs/saved`
- `/jobs/applications` and `/jobs/applications/:id`
- `/jobs/preferences`
- `/jobs/:jobId` the listing itself

### What the browser calls

| Action | API | Where the data lives |
|---|---|---|
| List and filter | `GET /api/v1/jobs` | Application copy of published jobs |
| Family counts on the pills | `GET /api/v1/jobs/family-counts` | Same catalog |
| Filter dropdowns | `GET /api/v1/jobs/filter-options` | Same catalog |
| Saved / applied counts on the hub | `GET /api/v1/jobs/summary` | `saved_jobs`, `job_applications` |
| Relevant list | `GET /api/v1/jobs/recommended` | Preferences plus published jobs |
| Open a job | `GET /api/v1/jobs/{id}` | Job row plus company, skills, role |
| Match note | `GET /api/v1/jobs/{id}/match` | Computed from preferences and skills. Not a readiness score. |
| Save / unsave | `POST` or `DELETE /api/v1/jobs/{id}/save` | `saved_jobs` |
| Mark applied | `POST /api/v1/jobs/{id}/apply` | Creates or updates `job_applications` |
| Prepare | `POST /api/v1/jobs/{id}/prepare` | Application row used as a prep tracker |
| Change application status | `PATCH /api/v1/applications/{id}` and `POST /api/v1/applications/{id}/status` | Application plus status history |
| Status history | `GET /api/v1/applications/{id}/history` | History table |

### How a listing gets into the app

Jobs do not start in the application database.

1. The Jobs server holds `public.validated_jobs`. That database is a catalog. The app connects with `JOBS_SOURCE_DATABASE_URL` and only reads.
2. A controlled sync (`jobs_source_reader` / `jobs_source_sync`) copies reviewed rows into the application `jobs` tables. It refuses to run if the target looks like the source database.
3. Publication into the student catalog is an explicit approve step. A source `approved_status` is not the student-facing gate.
4. The student never talks to the Jobs server. Only the backend does, and only to read.

Admin import is a second door for CSV: `POST /api/v1/admin/jobs/imports/validate`, then `POST /api/v1/admin/jobs/imports/confirm`. Validate does not publish. Confirm does.

Missing company is stored as not provided and kept out of the company filter. That is data hygiene, not a second job product.

---

## 6. Overview, readiness, and review

Overview is `/`. It is the dashboard, not a second jobs list. It can link into jobs, practice, and readiness. It does not own its own tables.

Job readiness:

- Screens: `/readiness`, `/readiness/skills`
- API: `GET /api/v1/readiness`, `/skills`, `/roles`, `/roles/{slug}`, `/recommendations`, and `POST /api/v1/readiness/refresh`
- It reads progress already stored from practice, coding, SQL, and learning. Refresh recomputes. It does not invent a match percentage on a job card.

Mistake book:

- Screen: `/mistakes` (the Review item in the top bar)
- API: `GET /api/v1/mistakes`, `GET /api/v1/mistakes/summary`, `POST /api/v1/mistakes/{id}/review`, `PATCH /api/v1/mistakes/{id}`
- Retry starts a real MCQ session: `POST /api/v1/mistakes/retry-session` returns a practice session. The student then follows the session flow below.

Bookmarks (`/bookmarks`) are a shelf across engines. MCQ bookmarks, coding bookmarks, SQL bookmarks, and prompt bookmarks are stored by their own engines and shown together.

---

## 7. Practice catalog versus the three engines

`/practice` is a hub. It does not run code and it does not grade an answer. It asks `GET /api/v1/practice-hub` and `GET /api/v1/practice/search` and then sends the student to one engine.

| Destination | Screen | Engine |
|---|---|---|
| SQL | `/practice/sql` then `/practice/sql/:slug` | SQL sandbox |
| DSA and Coding | `/practice/dsa`, `/practice/coding`, then `/practice/dsa/:id` | Coding engine. Judge0 if enabled, otherwise locked. |
| Technical MCQs | `/practice/mcq` | Universal question engine |
| Aptitude / CRT | `/practice/aptitude` | Same question engine, different taxonomy |
| Projects | `/practice/projects` | Learn engine |
| Playground | `/practice/python` | Coding playground. Not a problem. Not a session. |

Assessments in the top bar opens Aptitude. It is the same MCQ session engine, not a second product.

---

## 8. MCQ and exam sessions

Used by Aptitude, Technical MCQs, and mistake retry. Also used inside AI, Cloud, DevOps, and Cybersecurity when the item is a multiple-choice question. Those domains do not have a second quiz stack. They use the same questions, tagged by taxonomy domain.

Flow:

1. The catalog page loads `GET /api/v1/practice/catalog`. The student picks a topic, difficulty, question count, and mode (`practice` or `exam`).
2. `POST /api/v1/practice/sessions` creates the session in Postgres and returns its id.
3. The browser goes to `/practice/sessions/:id`. That shell is the assessment shell.
4. Each question is `GET /api/v1/practice/sessions/:id/questions/:n`.
5. Practice mode: `POST .../answer` can return feedback. Exam mode hides answers until submit. Exam selections autosave with `POST .../autosave`.
6. `POST /api/v1/practice/sessions/:id/complete` grades the session and writes mistakes for wrong items.
7. Results live at `/practice/sessions/:id/results` and `GET .../results`.
8. History is `GET /api/v1/practice/history`. An unfinished exam can be resumed from that history because the session row is still open.

The button the student presses is **Start Session**. Topic, difficulty, and mode are already on the card. The button name does not change per topic.

---

## 9. SQL

Screens: `/practice/sql`, `/practice/sql/:slug`, `/sql/submissions`, `/sql/submissions/:id`.

A problem load:

1. `GET /api/v1/sql/problems` for the list.
2. `GET /api/v1/sql/problems/{slug}` for the prompt.
3. `GET /api/v1/sql/problems/{id}/schema` and `.../tables/{name}/preview` for the schema explorer.
4. `GET /api/v1/sql/execution-status` tells the editor whether Run is allowed.
5. `GET /api/v1/sql/problems/{id}/navigation` moves to the next problem without leaving the workbench.

Run:

1. The browser posts the query to `POST /api/v1/sql/problems/{id}/run`.
2. The API checks the JWT, then a Redis rate limit and a concurrency slot for that user (`namespace=sql`).
3. The service parses the SQL and rejects mutating statements before anything reaches the sandbox.
4. The query runs in the SQL sandbox as the runner role, read-only, against the seeded tables for that problem.
5. The response is result rows or an error. It is not a grade.

Submit:

1. `POST /api/v1/sql/problems/{id}/submit` uses the same sandbox path, then compares the result to the expected result stored in the application database.
2. The submission and progress rows are written in the application Postgres.
3. Bookmarks are `POST /api/v1/sql/problems/{id}/bookmark`. The official solution is a separate `GET .../solution` and is not returned by run.

If the sandbox is down, the status endpoint says so, the banner shows, and Run and Submit stay disabled. The UI must not pretend the query passed.

---

## 10. Coding, DSA, and the playground

DSA and Coding share one engine. The catalog screens differ. The problem screen is `/practice/dsa/:id`.

Calls:

- List and filters: `GET /api/v1/coding/problems`
- Problem: `GET /api/v1/coding/problems/{id}`
- Languages: `GET /api/v1/coding/languages` (Python 71, Java 62, C++ 54, JavaScript 63 in the Judge0 language map)
- Can I run: `GET /api/v1/coding/execution-status`
- Run public tests: `POST /api/v1/coding/problems/{id}/run`
- Submit, including hidden tests: `POST /api/v1/coding/problems/{id}/submit`
- History: `GET /api/v1/coding/submissions` and `GET /api/v1/coding/submissions/{id}`
- Progress chips on the catalog: `GET /api/v1/coding/progress`
- Topic chips are derived from that progress summary, not from a dedicated topics endpoint. Topics beyond that summary stay reachable from the topic field.

Run and submit never execute inside FastAPI. They call Judge0 over HTTP, poll, and store the verdict. Hidden test input and output are not sent back to the browser on submit. Redis only limits how often one user can run.

When Judge0 is disabled, `execution-status` is unavailable. The editor still loads. Run and Submit stay off. A save of a draft is not a pass.

Playground (`/practice/python` and `/practice/playground`):

- It is scratch Python, not a catalog problem.
- The only execution call is `POST /api/v1/coding/playground/run`.
- The same execution lock applies. The playground must not call the SQL run endpoint and must not unlock itself.

---

## 11. Learn and projects

Learn is courses. Projects are guided tasks. Both are the learn service, not the MCQ session engine and not Judge0.

Courses:

1. `/learn` calls `GET /api/v1/courses`.
2. `/learn/courses/:slug` calls `GET /api/v1/courses/{slug}`.
3. The lesson workspace calls `GET /api/v1/courses/{course}/modules/{module}/lessons/{lesson}`.
4. Start, complete, practice attempt, and feedback are `POST /api/v1/lessons/{id}/start`, `/complete`, `/attempt`, `/feedback`.
5. Continue learning is `GET /api/v1/learning/continue`.

A lesson practice attempt can store starter code and a note. If execution is unavailable, the attempt is saved as practice. It does not mark the solution passed.

Projects:

1. `/practice/projects` calls `GET /api/v1/projects`.
2. Detail is `GET /api/v1/projects/{slug}`.
3. A task page is `GET /api/v1/projects/{slug}/tasks/{taskId}`. The browser route is `/projects/:slug/tasks/:taskId`.
4. Start, checklist, and complete are posts and a patch on `/api/v1/projects/{id}/...`.
5. A project task that is wired to a coding or SQL problem can complete when that problem is passed. The task does not run the code itself.

Practice paths (`/practice/paths/:slug`) are ordered items over the same learn tables: `GET /api/v1/paths/{slug}`, then start and complete on `/api/v1/paths/{id}/...`.

---

## 12. Interviews

Two API prefixes on purpose.

- `/api/v1/interview/*` is the question bank and pack list.
- `/api/v1/interviews/*` is the hub, sessions, history, review, progress, and company prep.

Screens: `/interviews`, `/interviews/packs/:slug`, `/interviews/session/new`, `/interviews/sessions/:id`, results, history, review, progress, `/company-prep`.

A session is study, mock, or rapid review. Mock hides the expected answer until reveal. Scoring is self-review: key-point coverage, confidence, self-rating. There is no model scoring the answer.

Company prep is a curated pack of those same questions, not a scrape of the company.

---

## 13. AI, Cloud, DevOps, Cybersecurity

These are content homes plus one shared scenario engine. They are not calls out to OpenAI, AWS, Kubernetes, or a SIEM.

AI:

- Home and tracks: `GET /api/v1/ai/home`, `GET /api/v1/ai/progress`
- Prompt list and workspace: `GET /api/v1/ai/prompts` and `GET /api/v1/ai/prompts/{slug}`
- Test and submit: `POST .../test` and `POST .../submit`. A `PromptEvaluator` in the API checks the prompt against stored cases. No model provider.
- Submissions: `GET /api/v1/ai/prompt-submissions`

Cloud, DevOps, Cybersecurity:

- Home: `GET /api/v1/cloud`, `/devops`, or `/cybersecurity`
- Progress: `GET /api/v1/{domain}/progress`
- A scenario opens `/scenarios/:slug`, loads `GET /api/v1/scenarios/{slug}`, and submits `POST /api/v1/scenarios/{slug}/submit`
- The grade is a deterministic check against the scenario definition stored in Postgres

MCQs inside these homes use the session flow in section 8.

---

## 14. Admin desk

Same API, role `admin` or `trainer`. Not in the student top bar except a More item named Admin for those roles.

What it writes, and where students later read it:

| Desk | Writes | Students read it as |
|---|---|---|
| `/admin/questions`, taxonomy | Questions and topics | Aptitude, MCQ, and domain quizzes |
| `/admin/coding` | Problems and test cases | DSA / Coding |
| `/admin/sql` | Problems, schema, expected results | SQL workbench |
| `/admin/jobs` and CSV import | Published job rows | Jobs browse |
| `/admin/courses`, projects, practice paths | Learn content | Learn and Projects |
| `/admin/ai` | Prompt challenges | Prompt workspace |
| `/admin/scenarios` plus cloud / devops / cyber desks | Scenario definitions | Scenario workspace |
| `/admin/interviews` | Packs | Interview hub |
| `/admin/readiness` | Role skill requirements | Readiness roles |
| `/admin/content` batches | Approve or reject candidates | Only after approval do they become student content |

Content factory rule: a candidate is not visible to students until approve. Bulk approve is an explicit action.

---

## 15. What must not happen

- The frontend must not talk to the Jobs server, the SQL sandbox, Judge0, or Redis. Those credentials stay on the API host.
- The API must not write `validated_jobs` on the Jobs server.
- Student SQL must not run against the application database.
- Student code must not run inside the FastAPI container.
- Playground run must not be used as a SQL runner.
- A disabled executor must not return a fake pass.
- Readiness must not be shown as a job match percentage.
- Interview and prompt grades must not be described as AI scores. They are self-review and deterministic checks.

---

## 16. Request map in one place

| Student is here | Browser calls | Backend then |
|---|---|---|
| Login | `POST /auth/login` | Writes nothing secret to the Jobs server. Returns JWT. |
| Jobs browse | `GET /jobs`, `/family-counts`, `/summary` | Reads published jobs and the student's saves. |
| Job detail | `GET /jobs/{id}` then save or apply | Writes `saved_jobs` or `job_applications`. |
| Aptitude session | `POST /practice/sessions` then answer or autosave, then complete | Writes session, answers, mistakes. |
| SQL run | `POST /sql/problems/{id}/run` | Redis limit, then sandbox read. |
| SQL submit | `POST /sql/problems/{id}/submit` | Sandbox read, compare, write submission. |
| Coding run | `POST /coding/problems/{id}/run` | Redis limit, then Judge0 if enabled. |
| Playground | `POST /coding/playground/run` | Same lock as coding. No problem row. |
| Lesson | `GET /courses/.../lessons/...` then attempt | Writes lesson progress only. |
| Prompt submit | `POST /ai/prompts/{slug}/submit` | Deterministic evaluator. No LLM. |
| Scenario submit | `POST /scenarios/{slug}/submit` | Deterministic check. No cloud API. |
| Readiness | `GET /readiness` or `POST /readiness/refresh` | Recomputes from stored progress. |
| Admin approve | `POST /admin/content/candidates/{id}/approve` | Moves content into the student tables. |
