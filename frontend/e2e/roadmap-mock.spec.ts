/**
 * Mock-only roadmap & Jobs UI verification (synthetic auth + API fixtures).
 * Does not prove live backend graph fetch or production authorization.
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { expect, test, type Page, type Route } from '@playwright/test'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const SHOTS = path.join(__dirname, 'artifacts', 'acceptance-shots', 'roadmap-ui')
const graphFixture = JSON.parse(
  fs.readFileSync(path.join(__dirname, 'fixtures', 'roadmap-mock-graph.json'), 'utf8'),
)

const USER = {
  id: 'roadmap-e2e',
  email: 'roadmap@jobready.dev',
  username: 'roadmap_e2e',
  full_name: 'Roadmap E2E',
  role: 'student',
  is_active: true,
  created_at: '2026-01-01T00:00:00Z',
}

const catalog = {
  roadmaps: [
    {
      family_slug: 'api-design',
      title: 'API Design',
      description: 'Design reliable HTTP APIs.',
      preview_only: false,
      student_eligible: true,
      source: 'official',
      graph_fetchable: true,
      graph_available: false,
      articles_available: true,
    },
    {
      family_slug: 'backend',
      title: 'Backend',
      description: 'Backend development path.',
      preview_only: false,
      student_eligible: true,
      source: 'official',
      graph_fetchable: true,
      graph_available: false,
      articles_available: false,
    },
  ],
  source: 'official',
  meta: { total: 2, has_bundled_catalog: true },
}

function json(route: Route, status: number, body: unknown) {
  return route.fulfill({
    status,
    contentType: 'application/json',
    body: JSON.stringify(body),
  })
}

let jobsSaveShouldFail = false
let jobFixtureSaved = false

async function installMocks(page: Page) {
  await page.addInitScript(() => {
    localStorage.setItem('jrp_access_token', 'roadmap-mock-token')
  })

  await page.route('**/*', async (route) => {
    const url = new URL(route.request().url())
    const local = url.hostname === '127.0.0.1' || url.hostname === 'localhost'
    if (!local) {
      await route.continue()
      return
    }
    if (!url.pathname.startsWith('/api/')) {
      await route.continue()
      return
    }
    const p = url.pathname
    if (p === '/api/v1/auth/me') return json(route, 200, USER)
    if (p === '/api/v1/roadmap/catalog') return json(route, 200, catalog)
    if (p === '/api/v1/roadmap/official/api-design/graph') return json(route, 200, graphFixture)
    if (p === '/api/v1/roadmap/official/backend/graph') return json(route, 200, { ...graphFixture, slug: 'backend' })
    if (p.startsWith('/api/v1/roadmap/official/api-design/topics/')) {
      return json(route, 200, {
        title: 'REST principles',
        markdown: '# REST\n\n```js\nfetch("/api")\n```\n\nLong paragraph. '.repeat(40),
        attribution: 'Fixture attribution.',
      })
    }
    if (p === '/api/v1/jobs/summary') {
      return json(route, 200, { saved_count: 1, applications_total: 0, offer_count: 0, follow_ups_due: 0 })
    }
    if (p === '/api/v1/jobs/family-counts') {
      return json(route, 200, {
        all: 2,
        families: [
          { id: 'data', label: 'Data', count: 1 },
          { id: 'eng', label: 'Engineering', count: 1 },
        ],
      })
    }
    if (p === '/api/v1/jobs/filter-options') {
      return json(route, 200, { locations: ['Remote'], companies: ['Acme'], experience_buckets: ['Mid'] })
    }
    if (p === '/api/v1/jobs') {
      return json(route, 200, {
        total: 1,
        limit: 20,
        page: 1,
        items: [
          {
            id: 'job-1',
            slug: 'fixture-role',
            title: 'Fixture role with a very long title that should wrap without breaking the layout',
            company_name: 'Acme Corp',
            location_text: 'Remote',
            experience_bucket: 'Mid',
            work_mode: 'remote',
            is_remote: true,
            is_saved: jobFixtureSaved,
            first_seen_at: '2026-10-01T00:00:00Z',
            posted_at: '2026-09-28T00:00:00Z',
            top_skills: ['TypeScript', 'HTTP'],
            experience_min_years: 2,
            experience_max_years: 5,
            employment_type: 'full_time',
          },
        ],
      })
    }
    if (/^\/api\/v1\/jobs\/[^/]+\/save$/.test(p) && route.request().method() === 'POST') {
      if (jobsSaveShouldFail) return json(route, 500, { detail: 'save failed' })
      jobFixtureSaved = true
      return json(route, 200, { saved: true })
    }
    if (p === '/api/v1/notifications/unread-count') return json(route, 200, { count: 0 })
    return json(route, 404, { detail: 'unmocked' })
  })
}

test.beforeAll(() => {
  fs.mkdirSync(SHOTS, { recursive: true })
})

test.describe('roadmap mock UI', () => {
  test('catalog and viewer screenshots (mocked)', async ({ page }) => {
    jobsSaveShouldFail = false
    jobFixtureSaved = false
    await installMocks(page)

    await page.setViewportSize({ width: 1366, height: 900 })
    await page.goto('/roadmaps')
    await expect(page.locator('#main-content').getByRole('heading', { name: 'Career roadmaps' })).toBeVisible()
    await page.screenshot({ path: path.join(SHOTS, 'catalog-light-1366.png'), fullPage: true })

    await page.goto('/roadmaps/api-design')
    await expect(page.getByRole('heading', { name: 'API Design' })).toBeVisible()
    await expect(page.locator('.ors-canvas .react-flow')).toBeVisible()
    await page.screenshot({ path: path.join(SHOTS, 'viewer-no-article-1366.png'), fullPage: true })

    await page.getByRole('button', { name: 'REST principles' }).first().click()
    await expect(page.getByRole('heading', { name: 'REST principles', level: 2 })).toBeVisible()
    await page.screenshot({ path: path.join(SHOTS, 'viewer-article-open-1366.png'), fullPage: true })

    await page.getByRole('button', { name: 'Hide outline' }).click()
    await page.screenshot({ path: path.join(SHOTS, 'viewer-outline-closed-1366.png'), fullPage: true })

    await page.emulateMedia({ colorScheme: 'dark' })
    await page.screenshot({ path: path.join(SHOTS, 'viewer-dark-1366.png'), fullPage: true })
  })

  test('topic search with outline closed', async ({ page }) => {
    await installMocks(page)
    await page.setViewportSize({ width: 1366, height: 900 })
    await page.goto('/roadmaps/api-design')
    await page.getByRole('button', { name: 'Hide outline' }).click()
    await page.getByRole('searchbox', { name: 'Find topic in outline' }).fill('Versioning')
    await expect(page.locator('.ors-topic-search-results')).toBeVisible()
    await expect(page.locator('.ors-topic-search-item')).toContainText('Versioning')
  })

  test('mobile article sheet (mocked)', async ({ page }) => {
    await installMocks(page)
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto('/roadmaps/api-design')
    await page.locator('.ors-node--topic').click()
    await expect(page.getByRole('dialog', { name: 'Topic details' })).toBeVisible()
    await page.screenshot({ path: path.join(SHOTS, 'mobile-topic-sheet-390.png'), fullPage: true })
    await page.getByRole('button', { name: 'Close' }).click()
    await expect(page.getByRole('dialog', { name: 'Topic details' })).toBeHidden()
  })

  test('jobs save failure surfaces (mocked)', async ({ page }) => {
    jobsSaveShouldFail = true
    jobFixtureSaved = false
    await installMocks(page)
    await page.setViewportSize({ width: 1366, height: 900 })
    await page.goto('/jobs')
    const card = page.locator('article.job-card-wrap[data-job-slug="fixture-role"]')
    const saveBtn = card.getByRole('button', { name: 'Save job' })
    await expect(saveBtn).toBeVisible()
    await saveBtn.click()
    await expect(page.getByText(/could not update this saved job/i)).toBeVisible()
    jobsSaveShouldFail = false
    await page.getByRole('button', { name: /retry save/i }).click()
    await expect(card.getByRole('button', { name: 'Remove from saved' })).toBeVisible()
    await page.screenshot({ path: path.join(SHOTS, 'jobs-save-error-1366.png'), fullPage: true })
  })
})
