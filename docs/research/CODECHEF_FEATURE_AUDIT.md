# CodeChef Practice + Learn — feature audit for Job Ready Platform

Research only. **No application code was changed.**

Do not copy CodeChef branding, assets, problem text, lesson text, or pixel layout. We want **feature / interaction / IA parity** with **our** UI, content, and schema.

---

## Method and limits

| Attempt | Result |
|---------|--------|
| Cursor browser MCP | **Not available** this session |
| Fetch `/practice`, `/learn/course/python`, many `/practice/{slug}` | SPA shell: “enable JavaScript” + a tagline |
| Fetch `/learn` catalog | **Full course + roadmap list** in HTML |
| Search-indexed pages | Path landings (Google/Microsoft/Flipkart/TCS interview, Python projects, Intermediate Java, Binary Search, ICPC), lesson pages (Python print/variables/MCQ), practice problems (tabs including Hints + AI Help), DSA roadmap copy |
| Project screenshots in repo | **None** |
| Auth / Pro / paywalls | **Not entered** |

Re-verify card grids, hover, exact mobile split, solution-unlock, and leftover project slugs in a real browser before building UI.

---

## 1. Practice sections discovered

Public Practice hub is a **sectioned catalog of paths**, not one infinite problem table (that lives partly on `/practice-old`).

| Section (labels from live product / this brief) | Purpose | Typical destination |
|-------------------------------------------------|---------|---------------------|
| Programming Languages | Language-first problem/course sets | `/practice/{lang}`, roadmaps `*-dsa` |
| Projects | Guided multi-task builds | `/practice/projects-*`, `/practice/intermediate-projects-*` |
| Beginner DSA | Strings, Arrays, Basic Math, Sorting, logic-building | `/practice/strings`, `/practice/arrays`, language “Level 2” courses |
| Data structures | LL, stacks/queues, matrices, heaps, hashing, trees, graphs, … | `/practice/linked-lists`, Learn `*-new` courses |
| Algorithms | Search/sort, recursion, greedy, binary search, two pointers, sliding window, DP, graphs, strings, … | `/practice/binary-search`, `/practice/course/two-pointers/...` |
| Difficulty rating wise | Bands such as 0–500, 500–1000, 1000–1400 | `/practice/course/1-star-difficulty-problems/DIFF1200/...` |
| Star wise paths | 1★→5★ contest skill | `/roadmap/become-5-star` |
| Interview Questions | Company OA/interview coding lists | `/practice/{company}-interview-questions` |
| Other | ICPC archives, misc | `/practice/icpc` |
| Compete / Compiler | Adjacent, not Practice pedagogy | `/contests`, `/ide` |

Landing interaction: **cards in a section grid → path page → problem/lesson**. Hash `#easy-projects` is an in-page section jump.

**Card metadata (from catalog + path pages):** icon, title, short pitch, problem/lesson count, hours, learners, level (Beginner/…), rating stars on Learn cards, progress % when logged in, Pro lock on items.

---

## 2. Learn sections discovered

`/learn` splits:

- **Topics chips:** Python, C, Java, C++, DSA, Data analytics, Web development, C#, Kotlin, Rust, Go, PHP, Machine Learning, Development fundamentals
- **All Courses:** 70+ beginner-friendly courses (see route map)
- **All Roadmaps:** 21 roadmaps (language+DSA, SQL, frontend, 5-star, DSA, backend careers, data analysis, React, MERN, ML)
- **Skill Tests:** listed as a catalog mode; **not opened** (may be gated)

Learn workspace URL pattern:

`/learn/course/{course}/{MODULE}/problems/{CODE}?tab=statement`

Python course mixes **IDE lessons, MCQs, and review lessons** in one module progress bar.

---

## 3. Project categories discovered

**Confirmed public:**

| Title | Slug / pattern | Shape |
|-------|----------------|--------|
| Python Projects for Beginners | `/practice/projects-python` | **11 named projects**, guided, CLI/data-oriented (calculator, games, URL shortener, CSV/JSON, plus a **3-part loan-approval** pipeline) |
| Intermediate-level projects using Java | `/practice/intermediate-projects-java` | **5 projects**, 17 problems, ~10h (scheduler, games, weather, sudoku — copy mixed Python/Java in indexer; treat as **our original** Java projects later) |
| HTML/CSS projects | `/practice/course/html/...` | Multi-page **build your project** checkpoints + quizzes |

**Advertised / expected (re-verify in browser):** Java/C/C++ beginner projects, intermediate Python, JavaScript, ML, Deep Learning/AI, MERN/full stack, SQL, data analysis & viz, Spring Boot, DevOps.

**Model:** Not independent LeetCode-style problems. **Guided multi-step projects** with sequential tasks, starter IDE, expected output/checklists, optional dataset files, “helpful resources”. Checkpoints = task completion via tests.

---

## 4. DSA / DS / algorithm paths

**Beginner DSA (language roadmaps, e.g. Python Level 2):** Logic building; 500–1000 rating set; Basic Math; Arrays; Strings; Sorting. Order is **curriculum**, not random tags.

**Data structures (roadmap + Learn courses):** Linked lists, stacks & queues, 2D arrays/matrices, heaps, hashing, trees/binary trees, graphs (+ advanced), tries, DSU.

**Algorithms:** Searching & sorting (+ intermediate), recursion, binary search, greedy, two pointers + sliding window (shared practice course), DP (+ advanced), graph algorithms, bit manipulation, number theory, combinatorics, time complexity, prefix sums (mentioned on DSA roadmap).

**Difficulty UX:** Numeric **difficulty rating** on problems (e.g. 1000, 1285, 1800) **and** Easy/Medium/Hard **and** star bands. Progress = % of path + solved status column. We should use **our** easy/medium/hard + optional numeric *internal* rank, not CodeChef stars.

---

## 5. Interactive lesson functionality

From Python Learn HTML + user workspace model + practice problem tabs:

- Split **statement | editor**
- Module **progress blocks** + Prev/Next
- Submit then Next
- Starter code in IDE
- Instructional examples before the task
- MCQ lessons in the same rail
- Common doubts under the statement
- Optional video (“Learn more from this short video”)
- Practice problems add Input/Output/Constraints/Samples/Subtasks

**Failed submit:** stay on lesson; no auto-advance (inferred from “click Submit… then Next”).
**Success:** user clicks Next (not fully auto in beginner copy).
**Locked lessons:** `unlock_mode` likely sequential; **not verified** logged-out.

---

## 6. Editor functionality

CodeChef: in-browser IDE, language select, run/submit, output panel, settings/expand (described; **library not confirmed** — could be Monaco/CodeMirror/custom).

Job Ready already: **Monaco**, language filter, starter JSON, local draft hook, Run (public tests), Submit (hidden tests), execution health, Judge0 abstraction.

**UX gaps around Monaco:** resizable split; fullscreen; editor settings (tab size, font, vim — optional); reset to starter (we have reset); sticky Submit/Next; console height; language locked to course vs multi-language DSA.

---

## 7. Progress / completion

Observed: path **Your Progress : 0%**; roadmap levels; problem STATUS column; solved states in lists when logged in (not visible logged out). Certificates mentioned for premium.

Job Ready: `coding_problem_progress` unsolved/attempted/solved + attempts; SQL progress; **no** course/path/project percent, no continue-learning, no lesson lock.

---

## 8. Common doubts / help

Learn: **per-lesson FAQ** (“How to print text?”, “Can I print multiple values?”) — static, content-authored.

Practice: **Hints** tab + **AI Help** tab + global “Tap into AI Help”. Pro marketing: real-time AI doubts.

**Our mapping:** `lesson_doubts` + `lesson_hints` + optional “Explain this error” **templates** (no LLM API). Interview Content Factory pattern for authoring.

---

## 9. Media

Video mentioned on a variables lesson. HTML projects mention viewing the webpage full-screen. Images/icons on cards (CDN — do not copy). Audio **not confirmed**.

Schema: `lesson_resources` for audio/video/image/file URLs we host.

---

## 10. Submissions / solutions

Tabs on practice: Statement, Submissions, Solution, Hints, AI Help.

Submissions: history exists as a tab; columns unverified.

Solutions: tab exists; many interview problems labeled **Pro**. MCQ lessons can show the correct option + explanation in public HTML.

Job Ready: submissions list + detail; **no** editorial/solution tab; **no** hint tab.

---

## 11. Interview-practice functionality

**Coding interview paths (CodeChef Practice):** grouped by **company** (Google, Microsoft, Flipkart, TCS CodeVita years; Amazon URL exists). List: problem name, Pro, difficulty label or rating. Not primarily grouped by role/experience/round in the HTML we saw (DSA topic appears **in the title**, e.g. “Graphs - Word Ladder”).

**Job Ready `/interviews`:** verbal Q&A (Content Factory), multi-skill/role tags — **complementary**, not a substitute for OA-style coding lists.

Company Prep module is still a **placeholder**.

---

## 12. Existing Job Ready equivalents

| Area | Status |
|------|--------|
| Auth | Yes |
| MCQ + exam mode | Yes (`/practice/mcq`, sessions) |
| DSA problem bank | Yes, topic/difficulty/tag/status filters |
| Monaco workspace | Yes, Problem + Submissions |
| Coding submissions + progress | Yes |
| Bookmarks | Yes (coding + MCQ) |
| SQL Practice | Yes (sandbox, not CodeChef SQL course) |
| Interview Q&A factory | Yes (text, not coding OA) |
| Admin coding/SQL/content | Yes |
| Code execution abstraction / Judge0 | Yes |
| Language-filtered coding page | Thin (`/practice/coding`) |
| Practice Hub / paths / courses / projects | **No** |
| Learn split pedagogy | **No** |
| Common doubts / hints / editorials | **No** |
| Certificates / skill tests | **No** |
| Contests / leaderboard product | Placeholder / not CodeChef-like |

---

## 13. Missing Job Ready functionality (priority)

See table in § Feature inventory. Highest leverage:

1. Practice Hub IA + `practice_paths`
2. Path landing + item list + % progress
3. Learn lesson workspace (split, Prev/Next, doubts, hints)
4. Course/module model wrapping existing coding problems
5. Projects as ordered lessons
6. Company coding paths (original problems)
7. Continue learning + search
8. Editorials after solve
9. Media resources
10. Feedback votes
11. Certificates (later)

---

## 14. Proposed database additions

See `INTERACTIVE_PRACTICE_SCHEMA_PROPOSAL.md`. Short list: `practice_paths`, sections, items, `courses`, modules, lessons, hints, doubts, resources, projects/tasks, user_*_progress, `lesson_feedback`. Reuse coding/SQL/skills/companies.

---

## 15. Proposed API additions

Hub, path, course, lesson payload, next/prev, continue, project, feedback, admin CRUD. **Keep** `/api/v1/coding/*` for execution.

---

## 16. Proposed frontend routes

`/practice` hub, `/practice/paths/:slug`, `/learn`, `/learn/courses/:slug/lessons/:lessonSlug`, `/projects/:slug/tasks/:taskSlug`. Same design tokens as AppLayout.

---

## 17. Proposed build phases

| Phase | Scope | Depends on |
|-------|--------|------------|
| **A — Hub + paths** | Catalog UI, path landing, items linking to **existing** `/practice/dsa/:id` | Schema paths/items |
| **B — Courses + lesson shell** | Split workspace, statement MD, Prev/Next, progress blocks, lock | Lessons + progress |
| **C — Pedagogy** | Doubts, hints, MCQ lesson type, editorial tab | Content Factory extension |
| **D — Projects** | Project landing + task sequence + resources | B |
| **E — Interview coding paths** | Company/topic lists, original problems | A + coding bank |
| **F — Discovery** | Search, continue learning, recommendations | Progress data |
| **G — Polish** | Media, feedback, certificates, mobile tab layout | C–F |

Do not start CodeChef contests clone. Do not add LLM APIs.

---

## 18. Pages that could not be inspected

- Full **Practice hub** visual (JS-only)
- Exact **mobile/tablet** split
- Logged-in **solved ticks**, resume, streak UI
- **Solution unlock** and **AI Help** internals (Pro)
- **Skill Tests** tab
- Amazon interview landing body
- Most **project collection** landings except Python beginners + Intermediate Java + HTML snippets
- `/learn/course/python` outline
- Editor **settings/shortcuts** and whether they use Monaco
- Hover/lazy-load/pagination on hub
- Like/dislike/comment **implementation** (not found in public HTML)

---

# Feature inventory

| Feature | CodeChef location | Observed behavior | Priority for Job Ready | Existing in our platform? | What we need to build | Notes |
|---------|-------------------|-------------------|------------------------|---------------------------|------------------------|-------|
| Practice Hub | `/practice` | Sectioned path cards | P0 | No (DSA list is not a hub) | Hub page + nav | Keep `/practice/dsa` |
| Path cards | Hub / Learn catalog | Icon, counts, level, learners | P0 | Partial Card/Badge | Path card component | Our icons only |
| Path landing | `/practice/{slug}` | Modules, % progress, list | P0 | No | Path + items API/UI | |
| Language paths | `*-dsa` roadmaps + `/practice/{lang}` | Course then practice sets | P0 | Thin language chips | Paths wrapping problems | Python/Java/C/C++/JS first |
| Search | Learn catalog copy | Topic/course search | P1 | DSA search only | Hub + learn search | |
| Beginner DSA paths | Practice + Level 2 courses | Ordered topics | P0 | Topic filter on flat bank | Curated path items | Original problems |
| DS paths | Learn + `/practice/linked-lists` etc. | Topic courses + practice | P1 | Tags/topics | More taxonomy + paths | |
| Algorithm paths | e.g. binary-search, two-pointers | Curated sets + learn course | P1 | Partial tags | Paths | |
| Rating/star paths | DIFF1200, become-5-star | Bands / contest stars | P2 | easy/medium/hard only | Optional “level paths” | Do not copy stars |
| Company coding interview | `/practice/*-interview-questions` | Company list, Pro items | P1 | Interview **Q&A** only | Coding paths + original items | |
| Verbal interview Q&A | (CodeChef weaker here) | — | — | **Yes** Content Factory | Keep | Complementary |
| Projects hub | `#easy-projects`, project slugs | Multi-project collections | P1 | No | Projects + tasks | |
| Guided project tasks | `projects-python` parts | Sequential parts + tests | P1 | No | Tasks = lessons | |
| Learn catalog | `/learn` | Courses + roadmaps | P0 | Placeholders `/ai/*` | `/learn` real catalog | |
| Roadmaps | `/roadmap/{slug}` | Ordered courses | P2 | No | Path kind or `roadmap` | Can wait; paths may suffice |
| Interactive lesson | `/learn/course/.../problems/` | Split IDE + pedagogy | P0 | DSA workspace only | Lesson shell | |
| Statement tab | `?tab=statement` | Lesson or CP statement | P0 | Problem description | MD + examples component | Our content |
| Submissions tab | Workspace | History | P0 | **Yes** | Wire into lesson page | Reuse API |
| Solution / editorial | Workspace | Gated / Pro | P1 | No | Unlock after solve | Our editorials |
| Hints | Practice tabs | Separate tab | P1 | No | `lesson_hints` | Static |
| Common doubts | Learn statement | Accordion FAQ | P0 | No | `lesson_doubts` | High value |
| AI Help | Tab + Pro | LLM mentor | P3 | No | **Do not** add LLM | Map to doubts/hints |
| MCQ-in-course | `PYTHMCQ*` | Same progress rail | P1 | MCQ **sessions** separate | Lesson kind=mcq | Reuse questions or local |
| Prev/Next + blocks | Lesson top | Module rail | P0 | Back to list only | Lesson navigator | |
| Auto-advance | Beginner copy | Submit then Next | P0 | No | Manual Next after AC | |
| Lesson lock | Inferred | Sequential | P1 | No | `unlock_mode` | |
| Continue learning | Home marketing | Personalized | P1 | No | `/learn/continue` | |
| Recommendations | Home | Roadmap CTAs | P2 | No | Rule-based | No embeddings required |
| Monaco-style editor | IDE pane | Highlight, lines | P0 | **Yes** | Improve shell | Split/resize/fullscreen |
| Language selector | IDE | Per problem | P0 | **Yes** | Course default lang | |
| Starter + reset | IDE | Populated starter | P0 | **Yes** | — | |
| Run public tests | IDE | Compile/run | P0 | **Yes** (Judge0) | Keep abstraction | |
| Submit hidden tests | IDE | Verdict | P0 | **Yes** | — | |
| Output panel | IDE | Below/aside editor | P0 | ExecutionResults | Layout polish | |
| Editor settings | IDE | Unverified | P2 | No | Font/tab optional | |
| Media | Some lessons | Video | P2 | No | `lesson_resources` | Our files |
| Feedback | Unknown | Not confirmed | P2 | No | `lesson_feedback` | |
| Certificates | Premium copy | Course complete | P3 | No | Later | Our branding |
| Skill tests | Learn tab | Uninspected | P3 | Assessments placeholder | Skip until inspected | |
| Bookmarks | Unknown on Learn | — | P1 | **Yes** | Bookmark lessons | |
| SQL course | Learn SQL + roadmap | Interactive SQL | P1 | **SQL Practice** | Optional Learn wrapper | Reuse sandbox |
| Contests | `/contests` | Out of scope | — | Placeholder | Do not clone | |
| Streak / XP / weekly LB | Taglines | Gamification | P3 | Leaderboard placeholder | Optional later | |
| Content pipeline | Their CMS | — | P0 | Content Factory (interview) | Extend types | Cursor JSON, no LLM API |

---

# Content strategy (original only)

Generate with **Cursor at dev time** → validated JSON → staging → admin approve (same as interview factory).

Tracks to author (priority order):

1. Python Learn (print → variables → control flow) — our lessons, our examples  
2. Beginner DSA path (math, arrays, strings, sorting) using **our** coding_problems  
3. One project (e.g. CLI toolkit) as 5–8 tasks  
4. Java / C++ / JS language intros  
5. DS + algorithm paths as curated lists  
6. SQL Learn wrapping existing SQL problems  
7. Company-agnostic “OA patterns” path (not scraped CodeChef/Google sets)  
8. Later: ML/AI/MERN/DevOps/Cloud/Cyber/GenAI as **paths of original tasks**, aligning with placeholder sidebar modules  

Never paste CodeChef statements, project briefs, or doubt text.

---

# Design strategy (Job Ready identity)

- **Layout:** existing `AppLayout`, sidebar groups (Practice / AI / Cloud / Interview). Add Practice Hub as first Practice item; Learn can live under Practice or its own group.
- **Tokens:** `--color-text`, `--color-surface`, `--color-accent`, existing Card/Badge/Button. Dark-friendly Monaco `vs-dark` already matches.
- **Cards:** 1 col mobile, 2 tablet, 3 desktop; metadata as text, not CodeChef icon set.
- **Lesson:** CSS grid `minmax(0,1fr) minmax(0,1fr)` desktop; `tabs` on small screens; optional drag splitter later.
- **Progress:** our Badge + a simple segment control (completed / current / locked), not their art.
- **Typography:** existing page `text-lg` titles + `text-sm` muted; statement as markdown in Card.

Pixel-perfect clone is **out of scope**.

---

# Companion docs

- `CODECHEF_ROUTE_MAP.md`
- `CODECHEF_SCREEN_MAP.md`
- `INTERACTIVE_PRACTICE_SCHEMA_PROPOSAL.md`
