/**
 * Opt-in fixture API for local frontend preview. Not imported by the app.
 * Default port 8099 so it does not take the normal backend port.
 *
 * Start: npm run dev:mock
 *        $env:MOCK_PORT=8099; npm run dev:mock
 * Stop:  end the process that is running scripts/dev-mock.mjs
 *
 * Point the dev server at it without changing the committed default:
 *   $env:DEV_API_PROXY='http://127.0.0.1:8099'
 *   npm run dev -- --host 127.0.0.1 --port 5193
 */
import http from 'node:http'

const port = Number(process.env.MOCK_PORT || 8099)

const user = {
  id: 'student-1',
  email: 'student@example.com',
  username: 'student',
  full_name: 'Preview Student',
  role: 'student',
  is_active: true,
  created_at: '2026-09-01T00:00:00Z',
}

const lessonBody = `# Prompt Engineering

## Learning objectives

- Write a precise prompt
- Check the result

The learning objectives stay useful when they appear later in the article.

## Worked example

This paragraph is long enough to show the reading column. It explains how a prompt names the audience, the output format, and the constraint that the model must not invent facts. The page chrome already shows the title and the structured objectives, so this article should not repeat that heading or that list.

## Another section

Keep this heading. It is not owned by the page chrome.
`

const routes = {
  'GET /api/v1/health': { ok: true },
  'GET /api/v1/auth/me': user,
  'GET /api/v1/learning/continue': [
    {
      kind: 'course',
      title: 'Python for analysts',
      subtitle: 'Shared course track',
      progress_percent: 20,
      href: '/learn/courses/python',
      last_activity_at: '2026-09-20T00:00:00Z',
    },
    {
      kind: 'lesson',
      title: 'Variables and types',
      subtitle: 'Intro · Variables',
      progress_percent: 40,
      href: '/learn/courses/python/intro/variables',
      last_activity_at: '2026-09-19T00:00:00Z',
    },
  ],
  'GET /api/v1/coding/progress': { solved_count: 1, attempted_count: 2, total_problems: 12 },
  'GET /api/v1/sql/progress': { solved_count: 2, attempted_count: 4, total_problems: 18 },
  'GET /api/v1/readiness': {
    target_role: null,
    score: 0,
    has_minimum_evidence: false,
    evidence_strength: 'none',
    core_coverage: { covered: 0, total: 0 },
    skills: [],
    strong_skills: [],
    developing_skills: [],
    missing_skills: [],
    why_breakdown: [],
    trend: [],
    recommended_actions: [],
    message: 'Choose a target role to measure readiness.',
    overall_score_ready: false,
    is_hiring_probability: false,
  },
  'GET /api/v1/mistakes/summary': { open_count: 3, top_weak_topics: [{ title: 'Probability', count: 4 }] },
  'GET /api/v1/jobs/preferences': {
    completed: true,
    target_role_slug: 'data-analyst',
    target_role_name: 'Data Analyst',
    preferred_locations: ['Hyderabad'],
    remote_preference: 'hybrid',
    roles: [
      { slug: 'data-analyst', name: 'Data Analyst' },
      { slug: 'sql-developer', name: 'SQL Developer' },
    ],
  },
  'GET /api/v1/jobs/recommended': {
    items: [
      {
        id: 'job-1',
        slug: 'data-analyst-sample',
        title: 'Data Analyst',
        company_name: 'Northwind',
        company_slug: 'northwind',
        location_text: 'Hyderabad',
        work_mode: 'hybrid',
        employment_type: 'full_time',
        experience_min_years: 0,
        experience_max_years: 2,
        posted_at: '2026-09-20T00:00:00Z',
        status: 'active',
        is_remote: false,
        top_skills: ['SQL', 'Excel'],
        is_saved: false,
        requirement_coverage: null,
      },
    ],
    total: 1,
    page: 1,
    limit: 20,
  },
  'GET /api/v1/practice/catalog': {
    domains: [
      {
        id: 'technical',
        name: 'Technical',
        slug: 'technical',
        categories: [
          {
            id: 'databases',
            name: 'Databases',
            slug: 'databases',
            topics: [{ id: 'indexes', name: 'Indexes', slug: 'indexes', subtopics: [] }],
          },
        ],
      },
      {
        id: 'placement',
        name: 'Placement',
        slug: 'placement',
        categories: [
          {
            id: 'aptitude',
            name: 'Aptitude',
            slug: 'aptitude',
            topics: [{ id: 'probability', name: 'Probability', slug: 'probability', subtopics: [] }],
          },
        ],
      },
    ],
  },
  'GET /api/v1/practice/history': { sessions: [] },
}

const hub = {
  sections: [
    {
      key: 'data',
      label: 'Data',
      paths: [
        {
          id: 'sql-path',
          slug: 'sql-practice',
          title: 'SQL practice',
          short_description: 'Filters, joins, and aggregates from the SQL catalog.',
          path_type: 'sql',
          difficulty: 'easy',
          language: 'SQL',
          estimated_minutes: 40,
          availability: 'coming_soon',
          is_featured: true,
          external_route: '/practice/sql',
          item_count: 0,
          progress_percent: 0,
        },
        {
          id: 'soon-path',
          slug: 'graph-lab',
          title: 'Graph lab',
          short_description: 'This path has no published items.',
          path_type: 'dsa',
          difficulty: 'hard',
          language: null,
          estimated_minutes: null,
          availability: 'coming_soon',
          is_featured: false,
          external_route: null,
          item_count: 0,
          progress_percent: 0,
        },
      ],
    },
  ],
  continue_learning: [
    {
      kind: 'course',
      title: 'Python for analysts',
      subtitle: 'Shared course track',
      progress_percent: 20,
      href: '/learn/courses/python',
      last_activity_at: '2026-09-20T00:00:00Z',
    },
  ],
  recently_practiced: [],
  recommended: [],
}

routes['GET /api/v1/practice-hub'] = hub
hub.recommended = [hub.sections[0].paths[0]]

routes['GET /api/v1/studio/syllabus/prompt-engineering'] = {
  key: 'prompt-engineering',
  title: 'Prompt Engineering',
  track: 'ai',
  track_title: 'AI',
  unit: 'prompts',
  unit_title: 'Prompts',
  position: 1,
  status: 'published',
  minutes: 20,
  prerequisites: ['Read a short article'],
  material_key: 'prompt-engineering',
  video: null,
  syllabus_position: 1,
  syllabus_total: 4,
  previous: null,
  next: { key: 'next-lesson', title: 'Next lesson title that is deliberately long so the footer can wrap on a narrow screen', status: 'published', material_key: 'next', href: '/learn/syllabus/next-lesson' },
  material: {
    key: 'prompt-engineering',
    title: 'Prompt Engineering',
    summary: 'Name the audience, the format, and the constraint.',
    kind: 'article',
    level: 'foundation',
    audience: null,
    minutes: 20,
    objectives: ['Write a precise prompt', 'Check the result'],
    prerequisites: [],
    body_md: lessonBody,
    examples: [],
    exercises: [],
    summary_md: 'A useful prompt states the audience and the output format.',
    sources: [],
    families: [],
    skills: [],
    version: 1,
    updated_at: '2026-09-20T00:00:00Z',
    has_download: false,
    read: false,
    related_pack: null,
  },
  practice: [],
}

const problem = {
  id: 'echo',
  slug: 'echo',
  title: 'Echo Input',
  description: 'Read a line and print it back. This statement is the problem, not a second page title.',
  difficulty: 'easy',
  constraints: 'One line of input.',
  input_format: 'A single line.',
  output_format: 'The same line.',
  tags: ['implementation'],
  time_limit_ms: 1000,
  memory_limit_kb: 65536,
  starter_code: { 62: 'public class Main {}', 71: 'print(input())' },
  sample_test_cases: [],
  supported_languages: [
    { id: 71, name: 'Python (3.8.1)', available: false },
    { id: 62, name: 'Java (OpenJDK 13.0.1)', available: true },
    { id: 54, name: 'C++ (GCC 9.2.0)', available: true },
    { id: 63, name: 'JavaScript (Node.js 12.14.0)', available: true },
  ],
  progress_status: 'unsolved',
  bookmarked: false,
  execution_available: true,
  hints: [],
  solution_unlocked: false,
}

routes['GET /api/v1/coding/problems/echo'] = problem
routes['GET /api/v1/coding/languages'] = problem.supported_languages
routes['GET /api/v1/coding/execution-status'] = {
  available: true,
  enabled: true,
  provider: 'mock',
  message: null,
  languages: problem.supported_languages,
}
routes['GET /api/v1/coding/problems/echo/navigation'] = { items: [], previous: null, next: null }

function send(res, status, body) {
  const payload = JSON.stringify(body)
  res.writeHead(status, {
    'content-type': 'application/json',
    'access-control-allow-origin': '*',
    'access-control-allow-headers': 'authorization,content-type',
  })
  res.end(payload)
}

routes['GET /api/v1/coding/problems'] = {
  items: [
    {
      id: 'echo',
      slug: 'echo',
      title: 'Echo Input',
      difficulty: 'easy',
      domain_id: 'd',
      category_id: 'c',
      topic_id: 't',
      topic_name: 'Implementation',
      topic_slug: 'implementation',
      tags: ['strings', 'io'],
      attempts: null,
      acceptance_rate: 0.82,
      progress_status: 'unsolved',
    },
  ],
  total: 1,
}
routes['GET /api/v1/coding/progress'] = {
  total_problems: 12,
  solved_count: 1,
  attempted_count: 2,
  easy: { solved: 1, total: 4, attempted: 2 },
  medium: { solved: 0, total: 5, attempted: 0 },
  hard: { solved: 0, total: 3, attempted: 0 },
  topics: [{ topic_slug: 'implementation', topic_name: 'Implementation', solved: 1, total: 4 }],
  items: [],
}
routes['GET /api/v1/sql/problems'] = {
  items: [
    {
      id: 'joins',
      slug: 'joins',
      title: 'Bookstore joins',
      difficulty: 'medium',
      topic_id: 't',
      topic_name: 'Joins',
      topic_slug: 'joins',
      tags: ['join'],
      progress_status: 'unsolved',
      acceptance_rate: 0.4,
      attempt_count: null,
    },
  ],
  total: 1,
}
routes['GET /api/v1/sql/progress'] = {
  total_problems: 18,
  solved_count: 2,
  attempted_count: 4,
  easy: { solved: 2, total: 6, attempted: 3 },
  medium: { solved: 0, total: 8, attempted: 1 },
  hard: { solved: 0, total: 4, attempted: 0 },
}
routes['GET /api/v1/sql/problems/joins'] = {
  id: 'joins',
  slug: 'joins',
  title: 'Bookstore joins',
  description: 'List each order with the customer who placed it. The statement stays in this pane.',
  difficulty: 'medium',
  database_dialect: 'postgresql',
  topic_id: 't',
  topic_name: 'Joins',
  topic_slug: 'joins',
  tags: ['join'],
  role_tags: ['analyst'],
  scenario: 'A campus bookstore records customers and orders.',
  task_description: 'Return customer_name and order_id.',
  expected_columns: ['customer_name', 'order_id'],
  sample_expected_rows: [],
  hints: ['Start from orders and join customers.'],
  estimated_time_seconds: 600,
  order_sensitive: false,
  schema_tables: [
    {
      table_name: 'customers',
      display_name: 'customers',
      columns: [
        { column_name: 'id', data_type: 'int', is_nullable: false, sort_order: 1 },
        { column_name: 'name', data_type: 'text', is_nullable: false, sort_order: 2 },
      ],
    },
  ],
  progress_status: 'unsolved',
  bookmarked: false,
  solution_unlocked: false,
  execution_available: false,
  starter_query: 'SELECT name FROM customers',
}
routes['GET /api/v1/sql/problems/joins/navigation'] = { previous: null, next: null, position: 1, total: 1, items: [] }
routes['GET /api/v1/sql/problems/joins/submissions'] = { items: [], total: 0 }
routes['GET /api/v1/sql/execution-status'] = {
  available: false,
  status: 'sandbox_unavailable',
  dialect: 'postgresql',
  message: 'SQL sandbox is off.',
}
routes['GET /api/v1/mistakes'] = []
routes['GET /api/v1/sql/playground'] = {
  language: 'sql',
  assessed: false,
  row_limit: 50,
  timeout_ms: 1000,
  note: 'Not graded.',
  datasets: [{ id: 'campus-bookstore', title: 'Campus bookstore', summary: 'Sample', tables: ['books'] }],
}
routes['GET /api/v1/sql/playground/datasets/campus-bookstore'] = {
  id: 'campus-bookstore',
  title: 'Campus bookstore',
  summary: 'Sample',
  documentation: 'Books and authors. This dataset is for exploration only.',
  starter_query: 'select * from books',
  assessed: false,
  row_limit: 50,
  timeout_ms: 1000,
  tables: [
    {
      table_name: 'books',
      display_name: 'books',
      columns: [{ column_name: 'title', data_type: 'text' }],
      sample_columns: ['title'],
      sample_rows: [['Dune']],
      sample_row_count: 1,
      sample_truncated: false,
    },
  ],
}
routes['GET /api/v1/learn/courses/python/intro/variables'] = {
  id: 'lesson-1',
  slug: 'variables',
  title: 'Variables and types',
  lesson_type: 'reading',
  statement_json: { blocks: [{ type: 'markdown', value: 'A variable names a value. This paragraph is the article, not a second title.' }] },
  starter_code: {},
  coding_problem_id: null,
  coding_problem_slug: null,
  status: 'in_progress',
  attempts: 0,
  solution_unlocked: false,
  solution_json: null,
  hints: [],
  doubts: [],
  resources: [],
  steps: [],
  progress_blocks: [
    { id: 'a', slug: 'variables', title: 'Variables and types', lesson_type: 'reading', sort_order: 1, status: 'in_progress', module_slug: 'intro', module_title: 'Intro' },
    { id: 'b', slug: 'loops', title: 'Loops', lesson_type: 'reading', sort_order: 2, status: 'locked', module_slug: 'intro', module_title: 'Intro' },
  ],
  prev_href: null,
  next_href: '/learn/courses/python/intro/loops',
  course_slug: 'python',
  course_title: 'Python for analysts',
  module_slug: 'intro',
  module_title: 'Intro',
  course_percent: 20,
  lesson_index: 1,
  lesson_total: 2,
  completion_requires_submit: false,
  can_mark_complete: true,
}
routes['GET /api/v1/courses/python/modules/intro/lessons/variables'] =
  routes['GET /api/v1/learn/courses/python/intro/variables']

const jobCard = {
  id: 'job-1',
  slug: 'data-analyst-sample',
  title: 'Data Analyst',
  company_name: 'Northwind',
  company_slug: 'northwind',
  location_text: 'Hyderabad',
  work_mode: 'hybrid',
  employment_type: 'full_time',
  experience_min_years: 0,
  experience_max_years: 2,
  posted_at: '2026-09-20T00:00:00Z',
  status: 'active',
  is_remote: false,
  top_skills: ['SQL', 'Excel'],
  is_saved: true,
  role_family: 'Data Analyst',
  experience_bucket: '0-2',
}

routes['GET /api/v1/jobs'] = { items: [jobCard], total: 1, page: 1, limit: 20 }
routes['GET /api/v1/jobs/family-counts'] = {
  all: 1,
  families: [{ id: 'data-analyst', label: 'Data Analyst', role_id: 'role-da', count: 1 }],
}
routes['GET /api/v1/jobs/filter-options'] = {
  locations: ['Hyderabad'],
  companies: ['Northwind'],
  experience_buckets: ['0-2'],
}
routes['GET /api/v1/jobs/summary'] = {
  saved_count: 1,
  applications_total: 1,
  applied_count: 0,
  interview_count: 0,
  offer_count: 0,
  rejected_count: 0,
  follow_ups_due: 0,
  follow_ups_today: 0,
  follow_ups_overdue: 0,
}
routes['GET /api/v1/jobs/saved'] = [
  { id: 'saved-1', job_id: 'job-1', saved_at: '2026-09-21T00:00:00Z', job: jobCard },
]
routes['GET /api/v1/applications'] = [
  {
    id: 'app-1',
    job_id: 'job-1',
    job_title: 'Data Analyst',
    company_name: 'Northwind',
    status: 'preparing',
    applied_at: null,
    next_follow_up_at: null,
    priority: 'medium',
    job_status: 'active',
  },
]
routes['GET /api/v1/courses'] = [
  {
    id: 'course-python',
    slug: 'python',
    title: 'Python for analysts',
    summary: 'Variables, tables, and a first query.',
    level: 'beginner',
    primary_language_key: 'python',
    lesson_count: 2,
    progress_percent: 20,
    is_featured: true,
  },
]
routes['GET /api/v1/interviews/hub'] = {
  continue_session: null,
  packs: [
    {
      id: 'pack-1',
      slug: 'sql-screen',
      title: 'SQL screen',
      description: 'Joins and aggregates for a first-round screen.',
      experience_level: 'fresher',
      question_count: 4,
    },
  ],
  progress: {
    questions_reviewed: 1,
    sessions_completed: 0,
    needs_review: 1,
    high_confidence_percent: null,
    average_key_point_coverage: null,
    by_role: {},
    by_skill: {},
    by_type: {},
    by_experience: {},
  },
  needs_review_count: 1,
  recent_sessions: [],
}
routes['GET /api/v1/ai/home'] = {
  tracks: [
    { key: 'genai', label: 'Generative AI', href: '/ai/genai' },
    { key: 'rag', label: 'RAG', href: '/ai/rag' },
  ],
  continue_ai: null,
  weak_topics: ['Retrieval'],
  prompt_progress: { attempted: 1, mastered: 0 },
  topics: [
    {
      key: 'rag',
      label: 'RAG',
      mcq_attempts: 2,
      mcq_accuracy: 50,
      prompt_attempts: 1,
      prompt_mastered: 0,
      best_prompt_score: 0,
    },
  ],
  recommended: ['Retrieval'],
  paths: [{ slug: 'sql-practice', title: 'SQL practice', href: '/practice/sql' }],
}
routes['GET /api/v1/practice/bookmarks'] = [
  {
    id: 'bm-mcq-1',
    title: 'Index choice',
    question_text: 'Which index helps a selective filter?',
    difficulty: 'easy',
    topic_name: 'Indexes',
  },
]
routes['GET /api/v1/coding/bookmarks'] = [
  {
    id: 'echo',
    slug: 'echo',
    title: 'Echo Input',
    difficulty: 'easy',
    domain_id: 'd',
    category_id: 'c',
    topic_id: 't',
    topic_name: 'Implementation',
    tags: ['strings'],
    progress_status: 'unsolved',
  },
]
routes['GET /api/v1/sql/bookmarks'] = [
  {
    id: 'joins',
    slug: 'joins',
    title: 'Bookstore joins',
    difficulty: 'medium',
    topic_id: 't',
    topic_name: 'Joins',
    tags: ['join'],
    progress_status: 'unsolved',
  },
]
routes['GET /api/v1/ai/prompt-bookmarks'] = [
  {
    id: 'prompt-1',
    slug: 'audience',
    title: 'Name the audience',
    difficulty: 'easy',
    task_type: 'rewrite',
  },
]

const server = http.createServer((req, res) => {
  const url = new URL(req.url, 'http://127.0.0.1')
  const key = `${req.method} ${url.pathname}`
  if (req.method === 'OPTIONS') {
    res.writeHead(204, {
      'access-control-allow-origin': '*',
      'access-control-allow-headers': 'authorization,content-type',
      'access-control-allow-methods': 'GET,POST,OPTIONS',
    })
    res.end()
    return
  }
  if (key === 'POST /api/v1/auth/login') {
    send(res, 200, { user, access_token: 'preview-token', token_type: 'bearer' })
    return
  }
  if (key === 'POST /api/v1/auth/logout') {
    send(res, 200, { ok: true })
    return
  }
  if (routes[key]) {
    send(res, 200, routes[key])
    return
  }
  if (req.method === 'GET' && url.pathname.startsWith('/api/v1/practice/search')) {
    send(res, 200, { items: [] })
    return
  }
  send(res, 404, { detail: `mock has no ${key}` })
})

server.listen(port, '127.0.0.1', () => {
  console.log(`mock api http://127.0.0.1:${port}`)
})
