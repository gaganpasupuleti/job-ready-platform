/**
 * Mock-only Phase 4 checks.
 * A Java or SQL "available" fixture here does not prove the real runtime works.
 * Every /api request is fulfilled in this file. Unmatched API calls return 599
 * and never continue to the shared API. Non-local hosts are aborted.
 */
import { expect, test, type Page, type Route } from '@playwright/test'

const USER = {
  id: 'student-1',
  email: 'student@example.com',
  username: 'preview',
  full_name: 'Preview Student',
  role: 'student',
  is_active: true,
  created_at: '2026-01-01T00:00:00Z',
}

type RuntimeMode = 'pending' | 'failed' | 'unavailable' | 'ready'

const runtime: { coding: RuntimeMode; sql: RuntimeMode } = {
  coding: 'unavailable',
  sql: 'unavailable',
}

function json(route: Route, status: number, body: unknown) {
  return route.fulfill({
    status,
    contentType: 'application/json',
    body: JSON.stringify(body),
  })
}

const codingProblem = {
  id: 'echo',
  slug: 'echo',
  title: 'Echo Input',
  description: 'Read one line and print it back.',
  difficulty: 'easy',
  constraints: null,
  input_format: 'One line',
  output_format: 'The same line',
  tags: ['strings'],
  time_limit_ms: 1000,
  memory_limit_kb: 65536,
  starter_code: { '62': 'class Main {}', '71': 'print(input())' },
  sample_test_cases: [],
  supported_languages: [
    { id: 62, name: 'Java', available: true },
    { id: 71, name: 'Python', available: false },
  ],
  progress_status: 'unsolved',
  bookmarked: false,
  execution_available: true,
  hints: [],
  solution_unlocked: false,
}

const sqlProblem = {
  id: 'sql-1',
  slug: 'bookstore-joins',
  title: 'Bookstore joins',
  description: 'List each order with its customer name.',
  difficulty: 'medium',
  database_dialect: 'sqlite',
  topic_id: 'joins',
  topic_name: 'Joins',
  topic_slug: 'joins',
  tags: [],
  role_tags: ['analyst'],
  scenario: 'A campus bookstore tracks orders.',
  task_description: 'Return customer_name and order_id.',
  expected_columns: ['customer_name', 'order_id'],
  sample_expected_rows: [],
  hints: [],
  estimated_time_seconds: 600,
  order_sensitive: false,
  schema_tables: [
    {
      table_name: 'customers',
      columns: [
        { column_name: 'id', data_type: 'int', is_nullable: false, sort_order: 1 },
        { column_name: 'name', data_type: 'text', is_nullable: false, sort_order: 2 },
      ],
    },
  ],
  progress_status: 'unsolved',
  bookmarked: false,
  solution_unlocked: false,
  execution_available: true,
  starter_query: 'SELECT 1',
}

function lesson(type: string) {
  return {
    id: 'lesson-1',
    slug: 'variables',
    title: 'Variables',
    lesson_type: type,
    statement_json: { blocks: [{ type: 'markdown', value: 'A variable stores a value.' }] },
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
      {
        id: 'b1',
        slug: 'variables',
        title: 'Variables',
        lesson_type: type,
        sort_order: 1,
        status: 'in_progress',
        module_slug: 'intro',
        module_title: 'Intro',
      },
      {
        id: 'b2',
        slug: 'loops',
        title: 'Loops',
        lesson_type: 'article',
        sort_order: 2,
        status: 'locked',
        module_slug: 'intro',
        module_title: 'Intro',
      },
    ],
    prev_href: null,
    next_href: '/learn/courses/python/intro/loops',
    course_slug: 'python',
    module_slug: 'intro',
    completion_requires_submit: false,
    can_mark_complete: true,
  }
}

async function installMock(page: Page) {
  await page.addInitScript(() => {
    localStorage.setItem('jrp_access_token', 'preview-token')
  })
  await page.route('**/*', async (route) => {
    const url = new URL(route.request().url())
    const local = url.hostname === '127.0.0.1' || url.hostname === 'localhost'
    const sharedApi = /railway\.app|jobready\.(dev|app|io)|amazonaws\.com/i.test(url.hostname)
    if (!local && (url.pathname.startsWith('/api/') || sharedApi)) {
      if (url.pathname.startsWith('/api/')) {
        return json(route, 599, { detail: 'blocked: phase4 mock does not call the shared API' })
      }
      await route.abort()
      return
    }
    if (!url.pathname.startsWith('/api/')) {
      await route.continue()
      return
    }
    const path = url.pathname
    if (path === '/api/v1/auth/me') return json(route, 200, USER)
    if (path === '/api/v1/coding/execution-status') {
      if (runtime.coding === 'pending') {
        await new Promise((resolve) => setTimeout(resolve, 4000))
        return json(route, 200, { available: false, languages: [] })
      }
      if (runtime.coding === 'failed') return json(route, 500, { detail: 'capability check failed' })
      if (runtime.coding === 'unavailable') return json(route, 200, { available: false, languages: [] })
      return json(route, 200, {
        available: true,
        languages: [
          { id: 62, name: 'Java', available: true },
          { id: 71, name: 'Python', available: false },
        ],
      })
    }
    if (path === '/api/v1/sql/execution-status') {
      if (runtime.sql === 'pending') {
        await new Promise((resolve) => setTimeout(resolve, 4000))
        return json(route, 200, { available: false, status: 'checking', message: '' })
      }
      if (runtime.sql === 'failed') return json(route, 500, { detail: 'capability check failed' })
      if (runtime.sql === 'unavailable') {
        return json(route, 200, { available: false, status: 'sandbox_unavailable', message: '' })
      }
      return json(route, 200, { available: true, status: 'ready', message: '' })
    }
    if (path === '/api/v1/coding/problems' && route.request().method() === 'GET') {
      return json(route, 200, {
        total: 1,
        items: [
          {
            id: 'echo',
            slug: 'echo',
            title: 'Echo Input',
            difficulty: 'easy',
            domain_id: 'd',
            category_id: 'c',
            topic_id: 't',
            topic_name: 'Strings',
            tags: ['warmup', 'io'],
            attempts: null,
            acceptance_rate: null,
            progress_status: 'unsolved',
          },
        ],
      })
    }
    if (path === '/api/v1/coding/progress') {
      return json(route, 200, {
        total_problems: 12,
        solved_count: 1,
        attempted_count: 2,
        easy: { solved: 1, total: 4, attempted: 2 },
        medium: { solved: 0, total: 5, attempted: 0 },
        hard: { solved: 0, total: 3, attempted: 0 },
        topics: [],
        items: [],
      })
    }
    if (path === '/api/v1/coding/languages') {
      return json(route, 200, [
        { id: 62, name: 'Java', available: true },
        { id: 71, name: 'Python', available: false },
      ])
    }
    if (path === '/api/v1/coding/problems/echo/navigation') {
      return json(route, 200, { previous: null, next: null, position: 1, total: 1, items: [] })
    }
    if (path === '/api/v1/coding/problems/echo') return json(route, 200, codingProblem)
    if (path.startsWith('/api/v1/coding/submissions')) return json(route, 200, { items: [], total: 0 })
    if (path === '/api/v1/sql/problems') {
      return json(route, 200, {
        total: 1,
        items: [
          {
            id: 'sql-1',
            slug: 'bookstore-joins',
            title: 'Bookstore joins',
            difficulty: 'medium',
            topic_name: 'Joins',
            role_tags: ['analyst'],
            attempt_count: null,
            acceptance_rate: null,
            progress_status: 'unsolved',
          },
        ],
      })
    }
    if (path === '/api/v1/sql/progress') {
      return json(route, 200, {
        total_problems: 8,
        solved_count: 0,
        attempted_count: 1,
        easy: { solved: 0, total: 3, attempted: 1 },
      })
    }
    if (path === '/api/v1/sql/problems/bookstore-joins/navigation') {
      return json(route, 200, { previous: null, next: null, position: 1, total: 1, items: [] })
    }
    if (path === '/api/v1/sql/problems/bookstore-joins/submissions') return json(route, 200, { items: [], total: 0 })
    if (path === '/api/v1/sql/problems/bookstore-joins') return json(route, 200, sqlProblem)
    if (path === '/api/v1/mistakes') return json(route, 200, [])
    if (path === '/api/v1/sql/playground') {
      return json(route, 200, {
        language: 'sqlite',
        assessed: false,
        row_limit: 50,
        timeout_ms: 1000,
        note: 'Exploration only',
        datasets: [{ id: 'campus-bookstore', title: 'Campus bookstore', summary: 'Orders', tables: ['customers'] }],
      })
    }
    if (path === '/api/v1/sql/playground/datasets/campus-bookstore') {
      return json(route, 200, {
        id: 'campus-bookstore',
        title: 'Campus bookstore',
        summary: 'Orders',
        documentation: 'customers(id, name)',
        starter_query: 'SELECT id FROM customers',
        assessed: false,
        row_limit: 50,
        timeout_ms: 1000,
        tables: [
          {
            table_name: 'customers',
            columns: [{ column_name: 'id', data_type: 'int', is_nullable: false, sort_order: 1 }],
            sample_columns: ['id'],
            sample_rows: [[1]],
            sample_row_count: 1,
            sample_truncated: false,
          },
        ],
      })
    }
    if (path === '/api/v1/courses/python/modules/intro/lessons/variables') return json(route, 200, lesson('article'))
    if (path === '/api/v1/lessons/lesson-1/start') return json(route, 200, { status: 'started' })
    return json(route, 599, { detail: 'blocked: phase4 mock does not call the shared API' })
  })
}

test.describe('phase 4 mock runtime and navigation', () => {
  test.beforeEach(async ({ page }) => {
    runtime.coding = 'unavailable'
    runtime.sql = 'unavailable'
    await installMock(page)
  })

  test('catalog distinguishes unavailable, failed, and ready code checks', async ({ page }) => {
    await page.goto('/practice/dsa')
    await expect(page.getByRole('status')).toContainText('Code execution is coming soon. You can write code and save drafts.')
    await expect(page.getByRole('heading', { name: 'Programming & DSA' })).toBeVisible()
    await expect(page.getByRole('link', { name: /Echo Input/ })).toBeVisible()
    await expect(page.getByText('warmup, io')).toBeVisible()

    runtime.coding = 'failed'
    await page.reload()
    await expect(page.getByRole('status')).toContainText('Could not check whether code can run.')

    runtime.coding = 'ready'
    await page.reload()
    await expect(page.getByRole('status')).toContainText('Run and Submit are available for Java.')
    await expect(page.getByRole('status')).toContainText('Not available: Python.')
  })

  test('shows a pending capability check before the result arrives', async ({ page }) => {
    runtime.coding = 'pending'
    await page.goto('/practice/dsa')
    await expect(page.getByRole('status')).toContainText('Checking whether code can run.')
  })

  test('sql catalog reports an unavailable sandbox before a problem opens', async ({ page }) => {
    await page.goto('/practice/sql')
    await expect(page.getByRole('status')).toContainText('SQL execution is unavailable. You can still open a problem and edit a draft.')
    await expect(page.getByRole('link', { name: /Bookstore joins/ })).toBeVisible()
  })

  test('keeps a coding language choice across pane switches', async ({ page }) => {
    runtime.coding = 'ready'
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto('/practice/dsa/echo')
    const language = page.getByRole('combobox')
    await expect(language).toBeVisible()
    await language.selectOption({ label: 'Java' })
    await page.getByRole('tablist', { name: 'Workspace' }).getByRole('button', { name: 'Code', exact: true }).click()
    await page.getByRole('tablist', { name: 'Workspace' }).getByRole('button', { name: 'Problem', exact: true }).click()
    await expect(language).toHaveValue('62')
    await expect(page.getByRole('button', { name: 'Run' })).toBeEnabled()
    await expect(page.getByRole('button', { name: 'Submit' })).toBeEnabled()
  })

  test('keeps an sql draft when switching schema and editor', async ({ page }) => {
    runtime.sql = 'unavailable'
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto('/practice/sql/bookstore-joins')
    await expect(page.getByRole('status').first()).toContainText('SQL execution is unavailable')
    await page.getByRole('tab', { name: 'Editor' }).click()
    await expect(page.locator('.monaco-editor, textarea').first()).toBeVisible()
    const wrote = await page.evaluate(() => {
      const editor = (window as unknown as { __jobReadyMonaco?: { setValue: (value: string) => void; getValue: () => string } }).__jobReadyMonaco
      if (!editor) return false
      editor.setValue('SELECT draft_marker')
      return editor.getValue().includes('draft_marker')
    })
    if (!wrote) {
      const fallback = page.locator('textarea:not([aria-hidden="true"])').last()
      await fallback.fill('SELECT draft_marker')
    }
    await page.getByRole('tab', { name: 'Schema' }).click()
    await expect(page.getByText('customers')).toBeVisible()
    await page.getByRole('tab', { name: 'Editor' }).click()
    await expect(page.getByText('draft_marker')).toBeVisible()
  })

  test('playgrounds omit submit and keep python locked', async ({ page }) => {
    await page.goto('/practice/playground/sql')
    await expect(page.getByText('there is no Submit action')).toBeVisible()
    await expect(page.getByText(/Submit: Ctrl/)).toHaveCount(0)
    await expect(page.getByRole('button', { name: 'Run query' })).toBeVisible()
    await page.goto('/practice/python')
    await expect(page.getByText('no Run or Submit action')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Run' })).toHaveCount(0)
    await expect(page.getByRole('button', { name: 'Submit' })).toHaveCount(0)
  })

  test('lesson next stays closed when the next lesson is locked', async ({ page }) => {
    await page.goto('/learn/courses/python/intro/variables')
    await expect(page.getByRole('status').filter({ hasText: 'Next is locked' })).toBeVisible()
    await expect(page.getByRole('link', { name: 'Next' })).toHaveCount(0)
    await expect(page.getByRole('button', { name: 'Solution' })).toHaveCount(0)
    await expect(page.getByRole('button', { name: 'Hints' })).toHaveCount(0)
    await expect(page.getByRole('button', { name: 'Mark complete' })).toBeVisible()
  })
})
