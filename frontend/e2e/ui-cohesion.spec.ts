/**
 * Mocked UI cohesion screenshots — PR #24 evidence (no production auth).
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { execSync } from 'node:child_process'

import { expect, test, type Browser, type Page, type Route } from '@playwright/test'

import {
  expectAppTheme,
  expectControlContrast,
  expectRenderedDarkTheme,
  probeControlContrast,
  type ContrastProbeResult,
} from './helpers'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const graphFixture = JSON.parse(
  fs.readFileSync(path.join(__dirname, 'fixtures', 'roadmap-mock-graph.json'), 'utf8'),
)
const shotRoot = process.env.UI_COHESION_DIR
  ? path.resolve(process.env.UI_COHESION_DIR)
  : path.join(__dirname, 'artifacts', 'ui-cohesion', 'after')
const BEFORE = path.join(__dirname, 'artifacts', 'ui-cohesion', 'before')
const AFTER = shotRoot

const USER = {
  id: 'ui-cohesion',
  email: 'ui@jobready.dev',
  username: 'ui_e2e',
  full_name: 'UI E2E',
  role: 'student',
  is_active: true,
  created_at: '2026-01-01T00:00:00Z',
}

const LIBRARY_BOOK = {
  id: 'book-1',
  title: 'CODING FOR BEGINNERS USING PYTHON',
  author: 'Cloudflare storage',
  category: 'Programming',
  description: 'Catalog entry for learning Python fundamentals.',
  available: true,
  has_file: true,
  external_url: null,
  bookmarked: false,
  reading_status: 'reading',
  last_page: 23,
}

function json(route: Route, status: number, body: unknown) {
  return route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) })
}

async function installRouteMocks(page: Page) {
  await page.route('**/*', async (route) => {
    const url = new URL(route.request().url())
    if (!['127.0.0.1', 'localhost'].includes(url.hostname) || !url.pathname.startsWith('/api/')) {
      await route.continue()
      return
    }
    const p = url.pathname
    if (p === '/api/v1/auth/me') return json(route, 200, USER)
    if (p === '/api/v1/roadmap/catalog') {
      return json(route, 200, {
        roadmaps: [
          {
            family_slug: 'api-design',
            title: 'API Design',
            description: 'Design reliable HTTP APIs.',
            preview_only: false,
            student_eligible: true,
            source: 'official',
            graph_fetchable: true,
            graph_available: true,
            articles_available: true,
          },
        ],
        source: 'official',
        meta: { total: 1, has_bundled_catalog: true },
      })
    }
    if (p === '/api/v1/roadmap/official/api-design/graph') return json(route, 200, graphFixture)
    if (p.startsWith('/api/v1/roadmap/official/api-design/topics/')) {
      return json(route, 200, {
        title: 'REST principles',
        markdown: '# REST\n\nBody text for article panel.',
        attribution: 'Fixture.',
      })
    }
    if (p === '/api/v1/jobs/summary') {
      return json(route, 200, { saved_count: 1, applications_total: 0, offer_count: 0, follow_ups_due: 0 })
    }
    if (p === '/api/v1/jobs/family-counts') {
      return json(route, 200, { all: 1, families: [{ id: 'py', label: 'Python Developer', count: 26 }] })
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
            slug: 'role',
            title: 'Python Developer',
            company_name: 'Acme',
            location_text: 'Remote',
            experience_bucket: 'Mid',
            work_mode: 'remote',
            is_remote: true,
            is_saved: false,
            first_seen_at: '2026-10-01T00:00:00Z',
            posted_at: '2026-10-01T00:00:00Z',
            top_skills: ['Python'],
            experience_min_years: 1,
            experience_max_years: 3,
            employment_type: 'full_time',
          },
        ],
      })
    }
    if (p === '/api/v1/library/books/book-1' || p === '/api/v1/students/ui-cohesion/library/books/book-1') {
      return json(route, 200, LIBRARY_BOOK)
    }
    if (p.startsWith('/api/v1/library') || p.includes('/library/')) {
      return json(route, 200, { items: [LIBRARY_BOOK], total: 1 })
    }
    if (p === '/api/v1/notifications/unread-count') return json(route, 200, { count: 0 })
    if (p === '/api/v1/auth/public-config') return json(route, 200, { registration_open: false })
    if (p === '/api/v1/auth/registration-open') return json(route, 200, { open: false })
    return json(route, 404, { detail: 'unmocked ' + p })
  })
}

async function openThemedCohesionPage(browser: Browser, theme: 'light' | 'dark') {
  const context = await browser.newContext({ colorScheme: theme })
  await context.addInitScript((mode: 'light' | 'dark') => {
    localStorage.setItem('jrp-theme', mode)
    localStorage.setItem('jrp_access_token', 'ui-cohesion-mock')
  }, theme)
  const page = await context.newPage()
  await installRouteMocks(page)
  return { context, page }
}

const contrastReport: Array<ContrastProbeResult & { selector: string; surface: string }> = []

async function recordContrast(page: Page, selector: string, surface: string, hover = false) {
  const result = await probeControlContrast(page, selector, hover ? { hover: true } : {})
  contrastReport.push({ ...result, selector, surface: hover ? `${surface} (hover)` : surface })
  if (result.status === 'pass') return
  if (result.status === 'unsupported_transparency') return
  await expectControlContrast(page, selector, hover ? { hover: true } : {})
}

async function assertJobsPrimaryContrast(page: Page) {
  const primary = '.jr-btn[data-variant="primary"]'
  await recordContrast(page, primary, 'jobs-primary')
  await recordContrast(page, primary, 'jobs-primary', true)
}

const viewports = [
  { name: '390', width: 390, height: 844 },
  { name: '768', width: 768, height: 900 },
  { name: '1280', width: 1280, height: 800 },
  { name: '1366', width: 1366, height: 768 },
  { name: '1920', width: 1920, height: 900 },
] as const

function captureMeta() {
  let sha = process.env.UI_COHESION_SHA?.trim()
  if (!sha) {
    try {
      sha = execSync('git rev-parse HEAD', { encoding: 'utf8' }).trim()
    } catch {
      sha = 'unknown'
    }
  }
  return {
    sha,
    theme: 'separate browser contexts per theme (single jrp-theme init each)',
    data: 'mocked API',
    viewports: viewports.map((vp) => ({ name: vp.name, width: vp.width, height: vp.height })),
    capturedAt: new Date().toISOString(),
  }
}

test.beforeAll(() => {
  fs.mkdirSync(AFTER, { recursive: true })
  if (fs.existsSync(BEFORE)) fs.mkdirSync(BEFORE, { recursive: true })
  fs.writeFileSync(path.join(AFTER, 'meta.json'), JSON.stringify(captureMeta(), null, 2))
})

test.afterAll(() => {
  fs.writeFileSync(path.join(AFTER, 'contrast-report.json'), JSON.stringify(contrastReport, null, 2))
})

test.describe('UI cohesion (mocked)', () => {
  for (const theme of ['light', 'dark'] as const) {
    test(`viewport captures (${theme})`, async ({ browser }) => {
      const { context, page } = await openThemedCohesionPage(browser, theme)
      try {
        for (const vp of viewports) {
          await page.setViewportSize({ width: vp.width, height: vp.height })
          await page.goto('/jobs')
          await expectAppTheme(page, theme)
          await expect(page.getByRole('heading', { name: 'Jobs' })).toBeVisible()
          await assertJobsPrimaryContrast(page)
          await page.screenshot({ path: path.join(AFTER, `jobs-${theme}-${vp.name}.png`) })

          await page.goto('/library/book-1')
          await expectAppTheme(page, theme)
          await expect(page.getByRole('heading', { name: /CODING FOR BEGINNERS/i })).toBeVisible({
            timeout: 15_000,
          })
          await recordContrast(page, '.jr-action-link', 'library-action-link')
          await recordContrast(page, '.jr-action-link', 'library-action-link', true)
          await page.screenshot({ path: path.join(AFTER, `library-book-${theme}-${vp.name}.png`) })

          await page.goto('/practice/projects')
          await expectAppTheme(page, theme)
          await expect(page.locator('#main-content')).toBeVisible({ timeout: 15_000 })
          await expect(page.locator('.jr-page-title', { hasText: 'Projects' })).toBeVisible()
          await page.screenshot({ path: path.join(AFTER, `projects-${theme}-${vp.name}.png`) })
        }
      } finally {
        await context.close()
      }
    })
  }

  test('desktop chrome and roadmap (light)', async ({ browser }) => {
    const { context, page } = await openThemedCohesionPage(browser, 'light')
    try {
      await page.setViewportSize({ width: 1366, height: 768 })
      await page.goto('/jobs')
      await expectAppTheme(page, 'light')
      await page.getByRole('button', { name: 'More' }).click()
      await expect(page.locator('#more-mega-panel')).toBeVisible()
      await expect(page.getByRole('link', { name: 'SQL' }).first()).toBeVisible()
      await page.screenshot({ path: path.join(AFTER, 'more-open-1366.png') })
      await page.keyboard.press('Escape')

      await page.getByRole('button', { name: /Account menu/i }).click()
      await expect(page.getByRole('menu', { name: 'Account' })).toBeVisible()
      await page.screenshot({ path: path.join(AFTER, 'account-open-1366.png') })

      await page.goto('/roadmaps')
      await expectAppTheme(page, 'light')
      await page.screenshot({ path: path.join(AFTER, 'roadmap-catalog-1366.png') })

      await page.goto('/roadmaps/api-design')
      await expectAppTheme(page, 'light')
      await expect(page.getByRole('heading', { name: 'API Design' })).toBeVisible()
      await page.getByRole('button', { name: 'REST principles' }).first().click()
      await expect(page.getByRole('heading', { name: 'REST principles', level: 2 })).toBeVisible()
      await page.screenshot({ path: path.join(AFTER, 'roadmap-article-1366.png') })
    } finally {
      await context.close()
    }
  })

  test('dark jobs hero (isolated context)', async ({ browser }) => {
    const { context, page } = await openThemedCohesionPage(browser, 'dark')
    try {
      await page.setViewportSize({ width: 1366, height: 768 })
      await page.goto('/jobs')
      await expectRenderedDarkTheme(page)
      await assertJobsPrimaryContrast(page)
      await page.screenshot({ path: path.join(AFTER, 'jobs-dark-1366.png') })
    } finally {
      await context.close()
    }
  })

  test('mobile nav and roadmap sheet (light)', async ({ browser }) => {
    const { context, page } = await openThemedCohesionPage(browser, 'light')
    try {
      await page.setViewportSize({ width: 390, height: 844 })
      await page.goto('/jobs')
      await expectAppTheme(page, 'light')
      await page.getByRole('button', { name: 'Open navigation' }).click()
      await expect(page.locator('.main-navigation.mobile-open')).toBeVisible()
      await page.screenshot({ path: path.join(AFTER, 'mobile-nav-390.png') })

      await page.goto('/roadmaps/api-design')
      await expectAppTheme(page, 'light')
      await page.getByRole('button', { name: 'REST principles' }).first().click()
      await expect(page.getByRole('dialog', { name: 'Topic details' })).toBeVisible()
      await page.screenshot({ path: path.join(AFTER, 'roadmap-mobile-article-390.png') })
    } finally {
      await context.close()
    }
  })
})
