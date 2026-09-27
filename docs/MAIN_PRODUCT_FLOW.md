# JobReady main product flow

This is the live student product after the frontend merge. It shows where each primary screen goes. It does not list every admin form or every AI / Cloud / DevOps sub-track.

Open this file in a Mermaid preview. Start with the map below.

## 1. Product map

```mermaid
flowchart TB
  guest([Visitor]) --> login[Login]
  guest --> register[Register]
  login --> jobs
  register --> prefs[Job preferences]
  prefs --> jobs

  subgraph bar [Top navigation]
    jobs[Jobs]
    overview[Overview]
    practice[Practice]
    learn[Learn]
    play[Playground]
    assess[Assessments]
    review[Review]
    more[More]
  end

  jobs --> jobDetail[Job detail]
  jobDetail --> saved[Saved]
  jobDetail --> apps[Applications]
  jobDetail --> practice

  overview --> jobs
  overview --> practice
  overview --> ready[Job readiness]

  practice --> sql[SQL]
  practice --> dsa[DSA]
  practice --> coding[Coding]
  practice --> mcq[Technical MCQs]
  practice --> aptitude[Aptitude / CRT]
  practice --> projects[Projects]

  learn --> course[Course]
  course --> lesson[Lesson workspace]

  play --> python[Python playground]
  python -.->|execution stays locked| lock([No SQL or Judge0 run])

  assess --> aptitude
  assess --> mcq
  aptitude --> session[MCQ session]
  mcq --> session
  session --> results[Session results]
  results --> review

  review --> mistakes[Mistake book]
  mistakes --> session

  more --> sql
  more --> dsa
  more --> coding
  more --> mcq
  more --> aptitude
  more --> projects
  more --> ready
  more --> interviews[Interview prep]
  more --> marks[Bookmarks]
  more --> relevant[Relevant jobs]
  more --> apps
  more --> ai[AI home]
  more --> prompts[Prompt engineering]
  more --> cloud[Cloud]
  more --> devops[DevOps]
  more --> cyber[Cybersecurity]
```

## 2. How a student moves

The product is jobs-first. Practice, learn, and review exist to get the student ready for a role, then back to a job.

```mermaid
flowchart LR
  A[Sign in] --> B[Set preferences]
  B --> C[Browse jobs]
  C --> D[Save or mark applied]
  D --> E[See the skill gap]
  E --> F[Practice, learn, or review]
  F --> G[Check job readiness]
  G --> C
```

## 3. Jobs

Jobs is the home after login. The other job screens hang off one listing, not off the top bar.

```mermaid
flowchart TB
  jobs["/jobs Browse"] --> card[Listing card]
  card --> detail["/jobs/:id Job detail"]
  detail --> save["/jobs/saved"]
  detail --> apply["Mark applied"]
  apply --> apps["/jobs/applications"]
  apps --> appDetail["/jobs/applications/:id"]
  detail --> practice[Practice the missing skill]

  jobs --> relevant["/jobs/recommended Relevant"]
  jobs --> save
  jobs --> apps
  jobs --> prefs["/jobs/preferences"]

  relevant --> detail
  save --> detail
```

Filters on Browse (family, search, sort, pagination) stay on `/jobs`. They are not separate products.

## 4. Practice and assessments

Practice is the catalog. Assessments is the timed / scored path. SQL, DSA, and Coding are workbenches, not MCQ sessions.

```mermaid
flowchart TB
  hub["/practice Practice hub"] --> dest{Destination}

  dest --> sql["/practice/sql"]
  dest --> dsa["/practice/dsa"]
  dest --> coding["/practice/coding"]
  dest --> mcq["/practice/mcq"]
  dest --> apt["/practice/aptitude"]
  dest --> projects["/practice/projects"]

  sql --> sqlQ["/practice/sql/:slug"]
  sqlQ --> sqlRun[Run or submit in the SQL sandbox]
  sqlRun --> sqlHist["/sql/submissions"]

  dsa --> dsaQ["/practice/dsa/:id"]
  coding --> dsaQ
  dsaQ --> codeRun[Run or submit when Judge0 is on]
  codeRun --> codeHist["/submissions"]

  mcq --> setup[Pick topic, difficulty, count, mode]
  apt --> setup
  setup --> session["/practice/sessions/:id"]
  session --> done["/practice/sessions/:id/results"]
  done --> review["/mistakes"]

  projects --> project["/practice/projects/:slug"]
  project --> task["/projects/:slug/tasks/:id"]
```

Assessments in the top bar opens Aptitude. Technical MCQs uses the same session engine. Playground (`/practice/python`) is a separate scratch pad and does not start a session.

## 5. Learn, review, and readiness

```mermaid
flowchart LR
  learn["/learn"] --> course["/learn/courses/:slug"]
  course --> lesson["Lesson workspace"]
  lesson --> course

  review["/mistakes Review"] --> again[Retry the question]
  again --> session[MCQ session]

  ready["/readiness"] --> skills["/readiness/skills"]
  ready --> jobs["/jobs"]
  marks["/bookmarks"] --> item[Saved question, job, or lesson]
```

## 6. More menu

More is not a second product. It is the rest of the same map, grouped so it is not one long list.

```mermaid
flowchart TB
  more[More]

  more --> practice[Practice]
  more --> career[Career]
  more --> eng[AI and Engineering]

  practice --> sql[SQL]
  practice --> dsa[DSA]
  practice --> coding[Coding]
  practice --> mcq[Technical MCQs]
  practice --> apt[Aptitude / CRT]

  career --> projects[Projects]
  career --> ready[Job readiness]
  career --> interviews[Interview prep]
  career --> marks[Bookmarks]
  career --> relevant[Relevant jobs]
  career --> apps[Applications]

  eng --> ai[AI home]
  eng --> prompts[Prompt engineering]
  eng --> cloud[Cloud]
  eng --> devops[DevOps]
  eng --> cyber[Cybersecurity]

  interviews --> packs[Packs and sessions]
  packs --> selfReview[Self-review, not auto-scored]
  prompts --> challenge[Challenge workspace]
  cloud --> scenario[Scenario workspace]
  devops --> scenario
  cyber --> scenario
```

AI, Cloud, DevOps, and Cybersecurity each open a home, then a track, then a scenario or challenge. Those tracks are inside the home. They are not extra top-bar items.

## 7. Who can enter

```mermaid
flowchart TB
  visit[Any URL] --> signed{Signed in?}
  signed -->|no| login["/login"]
  signed -->|yes| app[Student app]
  login --> jobs["/jobs"]
  register["/register"] --> prefs["/jobs/preferences"]
  prefs --> jobs
  app --> admin{Admin or trainer?}
  admin -->|yes| tools["/admin content tools"]
  admin -->|no| app
```

Admin is a content desk behind the same login. It is not part of the student path.

## What this map leaves out

- Admin editors for questions, SQL, coding, jobs, courses, prompts, and scenarios.
- Every AI, Cloud, DevOps, and Cybersecurity sub-track. They live under that home.
- Placeholder routes that are not in the top bar or More menu.
