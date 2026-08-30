# CodeChef public route map (Practice + Learn)

Internal research only. No cookies, tokens, or account data.

**Collection method:** public URLs from starting pages, search-indexed HTML, and linked roadmaps. CodeChef’s Practice/Learn UI is a JavaScript SPA. Cursor had **no browser MCP** in this session, so many pages returned only a short tagline instead of the full layout. Routes below are **public patterns that exist**; live card counts can change.

Do not scrape behind login, Pro, or paywalls. `Pro` on a problem name indicates a premium lock observed in public HTML, not an invitation to bypass it.

---

## Global chrome (always present in public HTML)

| Pattern | Purpose |
|---------|---------|
| `/` | Marketing home; links into roadmaps |
| `/practice` | Practice hub |
| `/learn` | Course catalog + roadmaps |
| `/contests` | Compete (out of Practice/Learn scope) |
| `/ide` | Standalone compiler |
| `/pro` | Paid upgrade |
| `/roadmap/{slug}` | Multi-course guided path |
| `/privacy-policy`, `/terms` | Legal |

---

## Practice hub

| Pattern | Notes |
|---------|--------|
| `/practice` | Landing: sectioned path cards |
| `/practice#{section}` | In-page jump. Starting URL used `#easy-projects`. Other hashes are inferred as section anchors (languages, projects, beginner-dsa, data-structures, algorithms, difficulty, stars, interview, other). **Not all hashes were verified in a live browser.** |

---

## Practice path landing (topic / language / company / project)

Pattern: `/practice/{path-slug}`

Observed or search-confirmed slugs:

### Programming languages

- `/practice/python`
- `/practice/java`
- `/practice/c` (expected; C language roadmap exists)
- `/practice/cpp` (expected)
- `/practice/javascript` (expected)
- Related language DSA: `/practice/java?roadmapSlug=java-dsa`

### Projects

- `/practice/projects-python` — Python Projects for Beginners
- `/practice/intermediate-projects-java` — Intermediate Java projects
- `/practice/course/projects-python/{MODULE}/problems/{CODE}` — guided project tasks
- HTML/CSS projects nested under `/practice/course/html/...`

Likely siblings (advertised in product copy / user inventory; **landing HTML not fully rendered here**):

- `projects-java`, `projects-cpp`, `projects-c`, `intermediate-projects-python`, `projects-javascript`, `projects-machine-learning`, `projects-deep-learning`, `projects-mern`, `projects-html-css-js`, `projects-sql`, `projects-data-analysis`, `projects-spring-boot`, `projects-devops`

Treat those as **candidates to re-verify in a live browser** before implementation.

### Beginner DSA / data structures / algorithms (practice landings)

Confirmed:

- `/practice/strings`
- `/practice/arrays`
- `/practice/linked-lists`
- `/practice/binary-search`

Search/roadmap-linked (public, typical siblings):

- stacks / queues: often combined as `stacks-and-queues`
- `heaps`, `hashing`, `trees`, `graphs`
- `greedy-algorithms`, `recursion`, `dynamic-programming`, `two-pointers`, `bit-manipulation`, `number-theory`, `tries`, `dsu`

### Difficulty / star paths

- `/practice/course/1-star-difficulty-problems/DIFF1200/problems/{CODE}` — 1000–1400 rating band
- `/roadmap/become-5-star` — competitive star progression (courses, not a single list)

Older catalog: `/practice-old`, `/practice-old/tags` (difficulty slider 0–5000, topic tags)

### Interview / company / contest archives

- `/practice/google-interview-questions`
- `/practice/microsoft-interview-questions`
- `/practice/flipkart-interview-questions`
- `/practice/tcs-interview-questions` (CodeVita years)
- `/practice/amazon-interview-questions` (URL fetched; body was SPA-only in this session)
- `/practice/icpc` — past ICPC sets

---

## Practice problem workspace

```
/practice/course/{path-slug}/{MODULE_CODE}/problems/{PROBLEM_CODE}
/practice/course/{path-slug}/{MODULE_CODE}/problems/{PROBLEM_CODE}?tab={tab}
```

**Tabs observed in public HTML** (rating-band problem): `statement`, `submissions`, `solution`, `hints`, `ai help` (rendered as `StatementSubmissionsSolutionHintsAI Help` in extracted text).

Example modules:

| Path | Module code | Example problem |
|------|-------------|-----------------|
| 1-star difficulty | `DIFF1200` | `CHEFSTLT`, `ODDPAIRS`, `THREEFR` |
| stacks-and-queues | `STAQUEF` | `SUSSTR` |
| two-pointers | `POINTERF` | `PREP68`, `NAME2` |
| binary-search | `INTBINS01` | `BOOKALLOCATE` |
| flipkart-interview-questions | `FLIPKARTPREP` | `LLMID` |
| icpc | `ICPCTR28` | `USANBOLT` |
| projects-python | `MLDEVPRJ01` | `DEVMLPRJ0101` |

Query: `?roadmapSlug={roadmap}` appears on some practice links to keep the user in a roadmap context.

---

## Learn catalog and courses

| Pattern | Purpose |
|---------|---------|
| `/learn` | Catalog: All Courses / All Roadmaps / Skill Tests / Topics |
| `/learn#header` | Jump to catalog |
| `/learn/course/{course-slug}` | Course outline |
| `/learn/course/{course-slug}/{MODULE}/problems/{LESSON_CODE}` | Interactive lesson |
| `/learn/course/{course-slug}/{MODULE}/problems/{LESSON_CODE}?tab=statement` | Statement tab (starting URL) |

### Course slug inventory (from `/learn` catalog HTML)

Languages: `python`, `java`, `c`, `cpp`, `sql`, `javascript`, `c-sharp`, `go`, `kotlin`, `rust`, `php`, `r`, `html`, `css`

Language problem-solving / beginner DSA: `python-beginner-v2-p1`, `python-beginner-v2-p2`, `java-beginner-v2-p1`, `java-beginner-v2-p2`, `cpp-beginner-v2-p1`, `cpp-beginner-v2-p2`, `c-beginner-v2-p1`, `c-beginner-v2-p2`, `c-sharp-beginner-part-1`, `c-sharp-beginner-part-2`, `kotlin-beginner-part-1`, `kotlin-beginner-part-2`

DSA topics: `linked-lists-new`, `stacks-and-queues-new`, `arrays`, `trees-new`, `graphs-new`, `graphs-advanced`, `heaps`, `hashing`, `tries`, `dsu`, `recursion-new`, `searching-sorting-new`, `sorting-intermediate`, `binary-search-new`, `greedy-algorithms`, `dynamic-programming-new`, `dynamic-programming-advanced`, `time-complexity`, `number-theory`, `bit-manipulation`, `combinatorics`

Web / backend: `java-development`, `cpp-development`, `react-js`, `web-dev-js`, `nodejs`, `django`, `flask`, `springboot`, `git-github`, `ux`, `advanced-javascript`

Data / ML: `sql-intermediate`, `sql-at-work`, `pl-sql`, `numpy`, `pandas`, `matplotlib`, `machine-learning`, `deep-learning-ai`, `advanced-python`

College / OOP: `college-oops-java`, `college-oops-cpp`, `oops-concepts-in-python`, `oops-java`, `college-programming-c`, `college-programming-cpp`, `operating-system`

Python lesson example: `/learn/course/python/LTCPY01/problems/PYTH02?tab=statement`  
Siblings observed: `PYTH01`, `PYTH03`, `PYTH07`, `PYTH08`, `PYTH09`, `PYTH20`, `PYTH198`, `PYTHMCQ03`, `PYTHMCQ04`, `LCPPCL115B` under later modules (`LTCPY02`, `LTCPY05`, `LTCPY17`).

---

## Roadmaps (`/roadmap/{slug}`)

From catalog “Roadmaps (21)”:

| Slug | Public title |
|------|----------------|
| `python-dsa` | Python with Beginner DSA |
| `cpp-dsa` | C++ with Beginner DSA |
| `java-dsa` | Java with Beginner DSA |
| `c-dsa` | C language with Beginner DSA |
| `javascript-dsa` | JavaScript with Beginner DSA |
| `c-sharp-dsa` | C# with Beginner DSA |
| `rust-dsa` | Rust with Problem Solving |
| `go-dsa` | Go with Problem Solving |
| `php-dsa` | PHP with Problem Solving |
| `sql` | SQL Roadmap for Data Analysis |
| `html` | Frontend Roadmap using HTML / CSS / JS |
| `become-5-star` | Competitive Programming — Become 5 star |
| `data-structures-and-algorithms-old` | DSA roadmap (legacy, 24 courses) |
| `data-structures-and-algorithms` | DSA (current, 29 courses) |
| `python-development` | Python Backend Developer |
| `cpp-development` | C++ Developer |
| `java-development` | Java Backend Developer |
| `data-analysis-using-python` | Data analysis using Python |
| `react-developer` | React Developer |
| `full-stack-development` | Full Stack Development using MERN |
| `machine-learning-using-python` | Machine Learning using Python |

---

## Job Ready proposed equivalents (not implemented)

See `INTERACTIVE_PRACTICE_SCHEMA_PROPOSAL.md`. Suggested public routes (ours, not CodeChef):

- `/practice` — Practice Hub
- `/practice/paths/:slug`
- `/learn/courses/:slug`
- `/learn/courses/:slug/lessons/:lessonSlug`
- `/projects/:slug`
- `/projects/:slug/tasks/:taskSlug`
