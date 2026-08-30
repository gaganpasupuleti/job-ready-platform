# CodeChef public screen map (Practice + Learn)

Internal UX inventory. Do **not** copy CodeChef visual design, icons, or content into production assets. Screenshots (if taken later) stay in an internal research folder, never `frontend/public` or `frontend/src`.

**Limitation:** No live browser/viewport session in this audit. Layout notes combine (a) pages whose HTML was server-rendered or indexed, (b) the starting lesson URL structure, (c) user-provided workspace description, (d) Job Ready’s own editor for contrast. Responsive behavior is **inferred** except where copy explicitly says “full-screen mode”.

---

## 1. Practice Hub

- **Purpose:** Browse all practice *paths* (not a flat problem dump).
- **Layout:** Top global nav (Practice / Compete / Compiler / Pro). Hero/title + motivational line. Vertical **section groups** with labeled categories. Grid of **path cards**. Search (catalog search is explicit on Learn; Practice hub search was not confirmed without JS).
- **Primary actions:** Click a card → path landing. Hash links (e.g. `#easy-projects`) scroll to a section.
- **Navigation:** Section list: Programming Languages, Projects, Beginner DSA, Data structures, Algorithms, Difficulty rating wise, Star wise paths, Interview Questions, Other Practice Paths.
- **Components:** Section heading, path card (icon, title, problem/lesson count, difficulty/level, learner count sometimes), Pro badge on some items.
- **Responsive:** Expect 3–4 cards/row desktop, 2 tablet, 1 mobile (standard card grid; **not measured**).

---

## 2. Practice path landing

- **Purpose:** One topic/language/company/project: intro + ordered modules/problems.
- **Layout:** Breadcrumb-like title. Short description. Metadata row: lessons, hours, problem count, learners, level, **Your Progress : N%**. Numbered module groups. Problem **table/list**: name, status, difficulty (label or rating number).
- **Primary actions:** Open a problem; resume via progress %; upgrade for Pro items.
- **Examples inspected via HTML:** Google Interview Questions (1 module, 11 problems, mix of Medium/Hard/numeric ratings, Pro locks); TCS CodeVita (year sections); Python Projects for Beginners (named project modules, 11 projects); Intermediate Java (5 projects, 17 problems, 10 hours); Binary Search (practice list + “Learn Binary Search” CTA); ICPC (contest-round groups).
- **Responsive:** List likely stacks; table columns hide on mobile (**unverified**).

---

## 3. Roadmap page (`/roadmap/{slug}`)

- **Purpose:** Ordered *courses* toward a goal (language+DSA, 5-star, MERN, etc.).
- **Layout (Java DSA HTML):** Levels (e.g. Level 2 Beginner DSA), duration estimates, links to Learn courses and Practice paths (`Practice Java`). FAQ at bottom.
- **Primary actions:** Enroll/continue a course; jump to practice set.
- **Components:** Level cards, course count, problem counts, “Reach 1*” type goals.

---

## 4. Learn catalog (`/learn`)

- **Purpose:** All courses + all roadmaps + topic chips + skill tests.
- **Layout:** Tabs/filters: All Courses, All Roadmaps, Skill Tests, Topics. Search copy. Course cards: icon, title, Beginner/Intermediate/Advanced, rating + review count, learner count, lesson count.
- **Primary actions:** Open course or roadmap; filter by topic (Python, C, Java, DSA, Data analytics, Web, C#, Kotlin, Rust, Go, PHP, ML, Development fundamentals).
- **Responsive:** Card grid; topic chips wrap.

---

## 5. Learn course outline (`/learn/course/{slug}`)

- **Purpose:** Module list before entering the IDE.
- **Layout:** Not fully rendered without JS. Inferred: module accordion, lesson list, continue CTA, certificate note for premium.
- **Limitation:** `/learn/course/python` returned SPA tagline only.

---

## 6. Interactive lesson / problem workspace (Learn **and** Practice)

This is the core interaction model.

### Desktop (target parity)

- **Top bar:** Course/path title. **Prev**. **Progress segments** (one block per lesson in the module; current highlighted). **Next**.
- **Left pane (~50%):** Tabs: **Statement** | **Submissions** | **Solution** | **Hints** (practice) | **AI Help**. Statement: title, instructional prose, examples, expected output, inline code, optional video. **Common doubts** accordion at bottom of statement (Learn Python). Optional like/helpful/report (not confirmed live).
- **Right pane:** Language selector. Code editor (line numbers, syntax highlight, starter code). Settings / expand. Output/console under editor or as a stacked panel.
- **Bottom of editor:** **Submit**. After success, **Next** is the main continue action. Copy on PYTH02: submit first, then Next.

### Mobile / tablet (proposed for Job Ready; CodeChef not measured)

- Stacked: statement first, then editor; or **tabs** “Lesson | Code”. Submit sticky at bottom.
- HTML/CSS projects explicitly ask for full-screen to preview the page.

### Learn-specific extras (from lesson HTML)

- Mix of **coding tasks** and **MCQ lessons** in the same module (e.g. `PYTHMCQ04`).
- Review/reflect lessons without a heavy coding task (`PYTH198`).
- “Some code has been populated in the IDE” — starter always present for early lessons.

### Practice-specific extras (from rating problems)

- Classic CP statement: Input Format, Output Format, Constraints, Sample, Explanation, **Subtasks**.
- Difficulty shown as **star-band name** and/or **numeric rating** (e.g. 1000, 1285, 1800).
- Hints tab separate from AI Help.

---

## 7. Submissions tab

- **Purpose:** Attempt history for this lesson/problem.
- **Observed:** Tab exists. Detailed columns (time, language, verdict, runtime) **not visible** without JS/login.
- **Job Ready today:** `/practice/dsa/:id` has Problem | Submissions; list via `GET /api/v1/coding/submissions`.

---

## 8. Solution tab

- **Purpose:** Official explanation + code after policy gate.
- **Observed:** Tab exists on practice problems. Unlock rules (solve first vs Pro vs always) **not confirmed** without an authenticated session. Interview lists mark many items Pro.
- **Learn MCQ:** correct answer + short explanation shown in indexed HTML for at least one quiz.

---

## 9. Hints / Common doubts / AI Help

| Surface | Behavior |
|---------|----------|
| Common doubts | Lesson-specific FAQ questions under statement (Learn). Accordion, not a live forum. |
| Hints tab | Present on practice workspace. Content gated or empty without login (**unverified**). |
| AI Help | Tab + marketing “AI Mentor” / Pro “real-time AI doubt resolution”. Public page also: “Tap into AI Help”. Do **not** clone LLM; map to static hints/FAQ. |

---

## 10. Project task screen

- **Purpose:** One step of a multi-part project.
- **Layout:** Same IDE shell. Statement describes **Part N of M**. Checklists of operations (e.g. load CSV, describe, missing values). **Helpful Resources** links to generic docs (Python/Pandas) — we should use our own resource table, not their links.
- **Progression:** Sequential parts (`DEVMLPRJ0101` → `0102` → …). Sidebar lists sibling projects (Number Guessing, Hangman, URL Shortener, …).

---

## 11. Standalone compiler (`/ide`)

- Out of Practice hub but linked globally. Job Ready has no public IDE-only page; editor is always bound to a problem.

---

## 12. Certificate / Pro upsell (public copy only)

- Interview paths: “Certification available Included in premium”.
- Do not implement CodeChef certificates; Job Ready can later add **our** completion certificates.

---

## Job Ready current screens (for gap)

| Screen | Route | vs CodeChef |
|--------|-------|-------------|
| DSA list | `/practice/dsa` | Flat filterable bank, not path hub |
| Coding list | `/practice/coding` | Language chips → same problem bank |
| Coding workspace | `/practice/dsa/:problemId` | Split-ish column layout, Monaco, Run+Submit, Problem/Submissions — **no** Next/Prev module, no Statement pedagogy, no doubts, no Solution tab, no Hints tab |
| SQL workspace | `/practice/sql/:slug` | Analogous for SQL, not language courses |
| Interview Q&A | `/interviews` | Text Q&A factory, **not** coding interview paths |
| MCQ session | `/practice/sessions/:id` | Exam/practice MCQ, not mixed into a coding course |
| Placeholders | `/ai/*`, `/cloud`, `/devops`, `/company-prep`, `/contests` | Empty modules |
