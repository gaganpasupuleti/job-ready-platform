/**
 * Mock-only Phase 5 checks. These fixtures do not prove the real studio,
 * project, readiness, interview, or AI APIs.
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

function json(route: Route, status: number, body: unknown) {
  return route.fulfill({
    status,
    contentType: 'application/json',
    body: JSON.stringify(body),
  })
}

async function install(page: Page) {
  await page.addInitScript(() => localStorage.setItem('jrp_access_token', 'preview-token'))
  await page.route('**/*', async (route) => {
    const url = new URL(route.request().url())
    const local = url.hostname === '127.0.0.1' || url.hostname === 'localhost'
    const sharedApi = /railway\.app|jobready\.(dev|app|io)|amazonaws\.com/i.test(url.hostname)
    if (!local && (url.pathname.startsWith('/api/') || sharedApi)) {
      if (url.pathname.startsWith('/api/')) return json(route, 599, { detail: 'blocked' })
      await route.abort()
      return
    }
    if (!url.pathname.startsWith('/api/')) {
      await route.continue()
      return
    }
    const path = url.pathname
    if (path === '/api/v1/auth/me') return json(route, 200, USER)
    if (path === '/api/v1/studio/catalog') {
      return json(route, 200, {
        families: [{ id: 'sql', label: 'SQL', count: 1 }],
        skills: [],
        levels: [{ id: 'beginner', count: 1 }],
        kinds: [{ id: 'cheat_sheet', count: 1 }],
        materials: [
          {
            key: 'indexes',
            title: 'Index cheat sheet',
            kind: 'cheat_sheet',
            level: 'beginner',
            minutes: 8,
            families: ['sql'],
            skills: [],
            read: false,
            updated_at: null,
          },
        ],
        assignments: [
          {
            key: 'warehouse',
            title: 'Warehouse notes',
            mode: 'manual_review',
            families: ['sql'],
            in_progress: false,
            unavailable: true,
          },
        ],
        packs: [],
      })
    }
    if (path === '/api/v1/projects') {
      return json(route, 200, [
        {
          id: 'soon',
          slug: 'later',
          title: 'Later project',
          short_description: 'Not open.',
          difficulty: 'medium',
          technology: null,
          category_key: 'data_engineering',
          availability: 'coming_soon',
          estimated_minutes: 30,
          task_count: 2,
          progress_percent: 0,
          href: '/projects/later',
        },
        {
          id: 'open',
          slug: 'bookstore',
          title: 'Bookstore',
          short_description: 'A published build.',
          difficulty: 'easy',
          technology: 'SQL',
          category_key: 'sql',
          availability: 'available',
          estimated_minutes: 40,
          task_count: 3,
          progress_percent: 0,
          href: '/projects/bookstore',
        },
      ])
    }
    if (path === '/api/v1/readiness') {
      return json(route, 200, {
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
      })
    }
    if (path === '/api/v1/interviews/hub') {
      return json(route, 200, {
        progress: { questions_reviewed: 0, needs_review: 0, sessions_completed: 0 },
        needs_review_count: 0,
        continue_session: null,
        packs: [],
        recent_sessions: [],
      })
    }
    if (path === '/api/v1/ai/home') {
      return json(route, 200, {
        tracks: [
          { key: 'genai', label: 'Generative AI', href: '/practice/mcq?category=generative-ai' },
          { key: 'rag', label: 'RAG', href: '/practice/mcq?category=generative-ai' },
        ],
        continue_ai: '/ai',
        weak_topics: [],
        prompt_progress: { attempted: 0, mastered: 0 },
        topics: [],
        recommended: [],
        paths: [],
      })
    }
    if (path === '/api/v1/practice/bookmarks' || path === '/api/v1/ai/prompt-bookmarks') {
      return json(route, 200, [])
    }
    if (path === '/api/v1/coding/bookmarks' || path === '/api/v1/sql/bookmarks') {
      return json(route, 200, { items: [], total: 0 })
    }
    return json(route, 599, { detail: 'unmatched phase 5 mock' })
  })
}

test('materials use readable type labels and skip unread filler', async ({ page }) => {
  await install(page)
  await page.goto('/learn/materials')
  await expect(page.getByRole('link', { name: /Index cheat sheet/ })).toContainText('Cheat sheet · Beginner')
  await expect(page.getByText('Not marked read')).toHaveCount(0)
  await expect(page.getByText('cheat_sheet')).toHaveCount(0)
})

test('assignments without a useful family filter show a locked task', async ({ page }) => {
  await install(page)
  await page.goto('/learn/assignments')
  await expect(page.getByRole('link', { name: /Warehouse notes/ })).toContainText('Locked')
  await expect(page.getByLabel('Family')).toHaveCount(0)
})

test('available projects come before coming soon and are the only links', async ({ page }) => {
  await install(page)
  await page.goto('/practice/projects')
  const titles = page.locator('h3')
  await expect(titles.nth(0)).toHaveText('Bookstore')
  await expect(page.getByRole('link', { name: /Bookstore/ })).toBeVisible()
  await expect(page.getByRole('link', { name: /Later project/ })).toHaveCount(0)
  await expect(page.getByText('This project is not open yet.')).toBeVisible()
})

test('readiness without a target offers setup and does not invent a score', async ({ page }) => {
  await install(page)
  await page.goto('/readiness')
  await expect(page.getByRole('link', { name: 'Set a target role' })).toHaveAttribute('href', '/jobs/preferences')
  await expect(page.getByText('Not measured yet')).toBeVisible()
  await expect(page.getByText('0%')).toHaveCount(0)
})

test('a track home is not labeled Continue, and shared catalogs are explained', async ({ page }) => {
  await install(page)
  await page.goto('/ai')
  await expect(page.getByRole('link', { name: /Explore AI practice/ })).toBeVisible()
  await expect(page.getByRole('link', { name: /^Continue/ })).toHaveCount(0)
  await expect(page.getByText(/same catalog/).first()).toBeVisible()
})

test('bookmark empty state offers a real destination', async ({ page }) => {
  await install(page)
  await page.goto('/bookmarks')
  await expect(page.getByRole('link', { name: 'Browse technical MCQs' })).toHaveAttribute('href', '/practice/mcq')
})

test('interview hub does not show a zero-question progress bar', async ({ page }) => {
  await install(page)
  await page.goto('/interviews')
  await expect(page.getByText('No questions reviewed yet.')).toBeVisible()
  await expect(page.getByText('0%')).toHaveCount(0)
})

test('More menu moves focus inside and Escape returns it', async ({ page }) => {
  await install(page)
  await page.goto('/learn/materials')
  await page.getByRole('button', { name: 'More' }).click()
  await expect(page.getByRole('link', { name: 'SQL' }).first()).toBeFocused()
  await page.keyboard.press('Escape')
  await expect(page.getByRole('button', { name: 'More' })).toBeFocused()
})
