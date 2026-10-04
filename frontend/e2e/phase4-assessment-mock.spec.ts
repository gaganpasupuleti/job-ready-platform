/**
 * Mock-only assessment, review, and progress checks.
 * Fixture scores and restored answers do not prove the real assessment API.
 * Every /api request is fulfilled here. Unmatched API calls return 599.
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

const catalog = {
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
}

const history = {
  sessions: [
    {
      id: 's-active',
      mode: 'exam',
      status: 'active',
      question_count: 2,
      score: 0,
      correct_count: 0,
      incorrect_count: 0,
      started_at: '2026-09-28T00:00:00Z',
      category_name: 'Databases',
      topic_name: 'Indexes',
    },
    {
      id: 's-done',
      mode: 'practice',
      status: 'completed',
      question_count: 2,
      score: 1,
      correct_count: 1,
      incorrect_count: 1,
      started_at: '2026-09-27T00:00:00Z',
      category_name: 'Aptitude',
      topic_name: 'Probability',
    },
  ],
}

function question(selected: string[]) {
  return {
    question_number: 1,
    total_questions: 2,
    answered: false,
    bookmarked: false,
    marked_for_review: false,
    selected_option_ids: selected,
    question: {
      id: 'q1',
      question_type: 'multiple_choice',
      title: null,
      question_text: 'Which plans can use an index?',
      difficulty: 'medium',
      marks: 1,
      negative_marks: 0,
      estimated_time_seconds: 60,
      topic_name: 'Indexes',
      skills: [],
      options: [
        { id: 'a', option_text: 'Index seek', sort_order: 1 },
        { id: 'b', option_text: 'Covering index', sort_order: 2 },
        { id: 'c', option_text: 'Full scan', sort_order: 3 },
      ],
    },
  }
}

function session(id: string, remaining: number) {
  return {
    id,
    mode: 'exam',
    status: 'active',
    question_count: 2,
    score: 0,
    correct_count: 0,
    incorrect_count: 0,
    unanswered_count: 2,
    started_at: '2026-09-28T00:00:00Z',
    answered_count: 1,
    expires_at: new Date(Date.now() + remaining * 1000).toISOString(),
    remaining_seconds: remaining,
    category_id: 'databases',
    topic_id: 'indexes',
  }
}

const results = {
  session: {
    id: 's-done',
    mode: 'practice',
    status: 'completed',
    question_count: 2,
    score: 1,
    correct_count: 1,
    incorrect_count: 1,
    unanswered_count: 0,
    started_at: '2026-09-27T00:00:00Z',
  },
  accuracy: 50,
  time_taken_seconds: 90,
  topic_performance: [{ topic_name: 'Indexes', accuracy: 50, total: 2, correct: 1 }],
  questions: [
    {
      question_number: 1,
      question_text: 'Which plans can use an index?',
      selected_option_ids: ['a'],
      correct_option_ids: ['a', 'b'],
      selected_option_texts: ['Index seek'],
      correct_option_texts: ['Index seek', 'Covering index'],
      explanation: 'A covering index and an index seek both avoid reading the whole table.',
      is_correct: false,
      marks_awarded: 0,
    },
  ],
}

function json(route: Route, status: number, body: unknown) {
  return route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) })
}

async function installMock(page: Page, fail: { catalog?: boolean; path?: boolean } = {}) {
  await page.addInitScript(() => localStorage.setItem('jrp_access_token', 'preview-token'))
  await page.route('**/*', async (route) => {
    const url = new URL(route.request().url())
    const local = url.hostname === '127.0.0.1' || url.hostname === 'localhost'
    const sharedApi = /railway\.app|jobready\.(dev|app|io)|amazonaws\.com/i.test(url.hostname)
    if (!local && (url.pathname.startsWith('/api/') || sharedApi)) {
      if (url.pathname.startsWith('/api/')) {
        return json(route, 599, { detail: 'blocked: assessment mock does not call the shared API' })
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
    if (path === '/api/v1/practice/catalog') {
      return fail.catalog ? json(route, 500, { detail: 'catalog down' }) : json(route, 200, catalog)
    }
    if (path === '/api/v1/practice/history') return json(route, 200, history)
    if (path === '/api/v1/practice/sessions/s-active') return json(route, 200, session('s-active', 600))
    if (path === '/api/v1/practice/sessions/s-expire') return json(route, 200, session('s-expire', 1))
    if (path === '/api/v1/practice/sessions/s-active/navigator' || path === '/api/v1/practice/sessions/s-expire/navigator') {
      return json(route, 200, {
        items: [
          { question_number: 1, answered: true, marked_for_review: false },
          { question_number: 2, answered: false, marked_for_review: false },
        ],
      })
    }
    if (path.endsWith('/questions/1')) return json(route, 200, question(['b']))
    if (path.endsWith('/autosave') || path.endsWith('/complete') || path.endsWith('/bookmark')) {
      return json(route, 200, { ok: true })
    }
    if (path === '/api/v1/practice/sessions/s-done/results') return json(route, 200, results)
    if (path === '/api/v1/mistakes/summary') {
      return json(route, 200, {
        open_count: 2,
        top_weak_topics: [{ title: 'Probability', count: 4 }],
      })
    }
    if (path === '/api/v1/mistakes') {
      return json(route, 200, [
        {
          id: 'm1',
          source_type: 'mcq',
          source_id: 'q1',
          title: 'Which plans can use an index when the table holds a million orders and the predicate is selective?',
          summary: null,
          mistake_type: 'incorrect',
          occurrence_count: 2,
          status: 'open',
          first_seen_at: '2026-09-20T00:00:00Z',
          last_seen_at: '2026-09-28T00:00:00Z',
          retry_href: '/practice/sessions/s-done/results',
          context: { topic_name: 'Indexes' },
        },
      ])
    }
    if (path === '/api/v1/paths/python-foundations') {
      return fail.path ? json(route, 500, { detail: 'path down' }) : json(route, 200, {
        id: 'path-1',
        slug: 'python-foundations',
        title: 'Python foundations',
        short_description: 'A checklist, not an exam.',
        path_type: 'course',
        difficulty: 'easy',
        availability: 'available',
        progress_percent: 0,
        sections: [
          {
            id: 's1',
            title: 'Start',
            items: [{ id: 'i1', title: 'Read the notes', item_type: 'checklist', completed: false, href: null }],
          },
        ],
      })
    }
    return json(route, 599, { detail: 'blocked: assessment mock does not call the shared API' })
  })
}

test.describe('phase 4 assessment mock', () => {
  test('groups technical subjects and keeps history inside that subject', async ({ page }) => {
    await installMock(page)
    await page.goto('/practice/mcq')
    await expect(page.getByRole('heading', { name: 'Technical MCQs' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Databases' })).toBeVisible()
    await expect(page.getByText('Probability')).toHaveCount(0)
    await expect(page.getByRole('link', { name: 'Resume' })).toBeVisible()
    await expect(page.getByRole('link', { name: 'View results' })).toHaveCount(0)
    await page.keyboard.press('Tab')
    await expect(page.locator(':focus')).toBeVisible()
  })

  test('restores a saved multi-select and keeps keyboard focus on the choices', async ({ page }) => {
    await installMock(page)
    await page.goto('/practice/sessions/s-active')
    const restored = page.getByRole('button', { name: 'Covering index' })
    await expect(restored).toHaveAttribute('aria-pressed', 'true')
    const seek = page.getByRole('button', { name: 'Index seek' })
    await seek.focus()
    await page.keyboard.press('Enter')
    await expect(seek).toHaveAttribute('aria-pressed', 'true')
    await expect(restored).toHaveAttribute('aria-pressed', 'true')
    await page.keyboard.press('Tab')
    await expect(restored).toBeFocused()
  })

  test('resumes an in-progress exam from subject history', async ({ page }) => {
    await installMock(page)
    await page.goto('/practice/mcq')
    await page.getByRole('link', { name: 'Resume' }).click()
    await expect(page).toHaveURL(/\/practice\/sessions\/s-active$/)
    await expect(page.getByText('Timed exam')).toBeVisible()
  })

  test('submits when the exam timer expires', async ({ page }) => {
    await installMock(page)
    await page.goto('/practice/sessions/s-expire')
    await expect(page).toHaveURL(/\/practice\/sessions\/s-expire\/results$/, { timeout: 15_000 })
  })

  test('shows a catalog failure without starting a session', async ({ page }) => {
    await installMock(page, { catalog: true })
    await page.goto('/practice/mcq')
    await expect(page.getByRole('alert')).toContainText('Could not load this catalog')
    await expect(page.getByRole('button', { name: 'Start Session' })).toHaveCount(0)
  })

  test('does not invent path progress when the request fails', async ({ page }) => {
    await installMock(page, { path: true })
    await page.goto('/practice/paths/python-foundations')
    await expect(page.getByRole('alert')).toContainText('Could not load this path')
    await expect(page.getByText('0%')).toHaveCount(0)
  })

  test('opens saved results from a topic label and does not offer a new retry', async ({ page }) => {
    await installMock(page)
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto('/mistakes')
    await expect(page.getByText('Indexes')).toBeVisible()
    await expect(page.getByText('Across all subjects')).toBeVisible()
    await page.getByRole('button', { name: 'MCQ' }).click()
    await expect(page.getByText('Across all subjects')).toHaveCount(0)
    await page.getByRole('link', { name: 'View results' }).click()
    await expect(page.getByText('A new retry session is not available')).toBeVisible()
    await expect(page.getByText('A covering index and an index seek both avoid reading the whole table.')).toBeVisible()
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    )
    expect(overflow).toBe(0)
  })
})
