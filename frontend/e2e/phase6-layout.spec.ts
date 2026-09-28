/**
 * Mock-only layout checks for Phase 6. Unmatched API calls return 599.
 * These results are not real-API verification.
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

const job = {
  id: 'job-1',
  slug: 'data-analyst-sample',
  title: 'Data Analyst with a deliberately long title for the Northwind analytics residency',
  company_name: 'Northwind Analytics Collective International',
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
}

function json(route: Route, status: number, body: unknown) {
  return route.fulfill({
    status,
    contentType: 'application/json',
    body: JSON.stringify(body),
  })
}

async function install(page: Page) {
  const errors: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))
  await page.addInitScript(() => localStorage.setItem('jrp_access_token', 'preview-token'))
  await page.route('**/*', async (route) => {
    const url = new URL(route.request().url())
    const local = url.hostname === '127.0.0.1' || url.hostname === 'localhost'
    if (!local || !url.pathname.startsWith('/api/')) {
      if (url.pathname.startsWith('/api/')) return json(route, 599, { detail: 'blocked' })
      if (!local) return route.abort()
      return route.continue()
    }
    const path = url.pathname
    if (path === '/api/v1/auth/me') return json(route, 200, USER)
    if (path === '/api/v1/jobs') return json(route, 200, { items: [job], total: 1, page: 1, limit: 20 })
    if (path === '/api/v1/jobs/recommended') return json(route, 200, { items: [job], total: 1, page: 1, limit: 20 })
    if (path === '/api/v1/jobs/saved') return json(route, 200, [])
    if (path === '/api/v1/jobs/preferences') {
      return json(route, 200, {
        target_role_slug: null,
        target_role_name: null,
        preferred_locations: [],
        remote_preference: null,
        roles: [{ slug: 'data-analyst', name: 'Data Analyst' }],
      })
    }
    if (path === '/api/v1/applications') {
      return json(route, 200, [
        {
          id: 'app-1',
          job_title: 'Data Analyst with a deliberately long title for the Northwind analytics residency',
          company_name: 'Northwind Analytics Collective International',
          status: 'preparing',
          priority: 'normal',
          next_follow_up_at: null,
        },
      ])
    }
    if (path === '/api/v1/courses') {
      return json(route, 200, [
        {
          id: 'c1',
          slug: 'python',
          title: 'Python for analysts',
          level: 'beginner',
          summary: 'A short course.',
          lesson_count: 4,
          progress_percent: 0,
          is_featured: false,
        },
      ])
    }
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
        assignments: [],
        packs: [],
      })
    }
    if (path === '/api/v1/projects') {
      return json(route, 200, [
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
    if (path === '/api/v1/practice/catalog') {
      return json(route, 200, { domains: [] })
    }
    if (path === '/api/v1/mistakes') return json(route, 200, [])
    if (path === '/api/v1/jobs/summary') {
      return json(route, 200, {
        saved_count: 1,
        applications_total: 1,
        applied_count: 0,
        interview_count: 0,
        offer_count: 0,
        follow_ups_due: 0,
        follow_ups_overdue: 0,
        follow_ups_today: 0,
      })
    }
    return json(route, 200, {
      items: [],
      total: 0,
      page: 1,
      limit: 20,
      tracks: [],
      scenarios: [],
      paths: [],
      projects: [],
      topics: [],
      weak_topics: [],
      sections: [],
      continue_learning: [],
      recently_practiced: [],
      recommended: [],
      materials: [],
      assignments: [],
      families: [],
      packs: [],
      domains: [],
      progress: {
        questions_reviewed: 0,
        needs_review: 0,
        sessions_completed: 0,
        scenario_attempted: 0,
        scenario_mastered: 0,
      },
      prompt_progress: { attempted: 0, mastered: 0 },
      continue_session: null,
      recent_sessions: [],
      needs_review_count: 0,
      target_role: null,
      score: null,
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
      overall_score_ready: false,
      is_hiring_probability: false,
      message: null,
      open_count: 0,
      top_weak_topics: [],
      solved_count: 0,
      attempted_count: 0,
      total_problems: null,
      execution_available: false,
      languages: [],
    })
  })
  return errors
}

const routes = [
  '/jobs',
  '/',
  '/practice',
  '/learn',
  '/practice/playground',
  '/practice/aptitude',
  '/mistakes',
  '/jobs/saved',
  '/jobs/recommended',
  '/jobs/applications',
  '/jobs/preferences',
  '/practice/dsa',
  '/practice/sql',
  '/practice/typing',
  '/learn/materials',
  '/learn/assignments',
  '/learn/syllabus',
  '/practice/projects',
  '/readiness',
  '/interviews',
  '/ai',
  '/cloud',
  '/devops',
  '/cybersecurity',
  '/bookmarks',
  '/ai/prompt-engineering/challenges',
]

test('top-level routes do not overflow at desktop or narrow mobile', async ({ page }) => {
  test.setTimeout(300_000)
  const errors = await install(page)
  for (const width of [1440, 390, 360]) {
    await page.setViewportSize({ width, height: 900 })
    for (const path of routes) {
      await page.goto(path, { waitUntil: 'domcontentloaded', timeout: 20_000 })
      await expect(page.locator('#main-content'), `${path} at ${width}`).toBeVisible({ timeout: 8_000 })
      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
      )
      expect(overflow, `${path} at ${width}`).toBeLessThanOrEqual(1)
    }
  }
  expect(errors).toEqual([])
})

test('representative layouts stay within the page at intermediate widths', async ({ page }) => {
  const errors = await install(page)
  for (const width of [430, 768, 1024, 1280]) {
    await page.setViewportSize({ width, height: 900 })
    for (const path of ['/jobs', '/learn', '/practice/projects', '/practice/sql', '/jobs/applications']) {
      await page.goto(path, { waitUntil: 'domcontentloaded' })
      await expect(page.locator('main')).toBeVisible()
      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
      )
      expect(overflow, `${path} at ${width}`).toBeLessThanOrEqual(1)
    }
  }
  expect(errors).toEqual([])
})

test('course catalog is a single list and applications use a readable stage', async ({ page }) => {
  await install(page)
  await page.goto('/learn')
  await expect(page.getByRole('link', { name: /Python for analysts/ })).toHaveCount(1)
  await expect(page.getByText('Beginner')).toBeVisible()
  await page.goto('/jobs/applications')
  await expect(page.getByRole('heading', { name: 'Preparing' })).toBeVisible()
  await page.goto('/jobs/preferences')
  await expect(page.getByLabel('Role')).toBeVisible()
  await expect(page.getByLabel('Preferred locations')).toBeVisible()
})

test('200% zoom does not create page overflow on jobs or materials', async ({ page }) => {
  await install(page)
  await page.setViewportSize({ width: 1280, height: 800 })
  for (const path of ['/jobs', '/learn/materials']) {
    await page.goto(path, { waitUntil: 'networkidle' })
    await page.evaluate(() => {
      document.documentElement.style.zoom = '2'
    })
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    )
    expect(overflow, path).toBeLessThanOrEqual(1)
  }
})
