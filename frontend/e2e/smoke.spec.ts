import { expect, test } from '@playwright/test'

import { attachConsoleGuard, loadManifest, loginAs } from './helpers'

const fixtures = loadManifest()

const placeholderRoutes = [
  '/company-prep',
  '/assessments',
  '/contests',
  '/jobs',
  '/jobs/recommended',
  '/jobs/saved',
  '/jobs/applications',
  '/readiness',
  '/mistakes',
  '/leaderboard',
  '/ai/ml',
]

const aiSmoke = [
  '/ai',
  '/ai/genai',
  '/ai/rag',
  '/ai/prompt-engineering',
  '/ai/agents',
  '/ai/mcp',
  '/ai/tool-calling',
  '/ai/evaluation',
  '/ai/security',
  '/ai/system-design',
  '/ai/progress',
]

const infraSmoke = [
  '/cloud',
  '/cloud/aws',
  '/cloud/progress',
  '/devops',
  '/devops/docker',
  '/devops/kubernetes',
  '/devops/progress',
  '/cybersecurity',
  '/cybersecurity/soc',
  '/cybersecurity/api-security',
  '/cybersecurity/progress',
]

test.describe('Smoke routes', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, fixtures.users.student)
  })

  test('placeholder and future routes render', async ({ page }) => {
    for (const route of placeholderRoutes) {
      await page.goto(route)
      await expect(page.getByText(/coming soon|not available|page not found|under construction|placeholder/i).or(
        page.getByRole('heading').first(),
      )).toBeVisible({ timeout: 15_000 })
      await expect(page).not.toHaveURL(/\/login/)
    }
  })

  test('AI track smoke', async ({ page }) => {
    for (const route of aiSmoke) {
      await page.goto(route)
      await expect(page.locator('body')).not.toHaveText(/Cannot GET|Not Found 404/i)
      await expect(page.getByRole('heading').first()).toBeVisible({ timeout: 15_000 })
    }
    await page.goto('/ai/rag')
    const text = (await page.locator('body').innerText()).toLowerCase()
    expect(text).toMatch(/rag|retrieval|vector|embedding/)
  })

  test('cloud devops cyber smoke', async ({ page }) => {
    for (const route of infraSmoke) {
      await page.goto(route)
      await expect(page.getByRole('heading').first()).toBeVisible({ timeout: 15_000 })
    }
  })

  test('interviews smoke', async ({ page }) => {
    await page.goto('/interviews')
    await expect(page.getByRole('heading').first()).toBeVisible()
  })

  test('deep link refresh for SQL', async ({ page }) => {
    const guard = attachConsoleGuard(page)
    await page.goto(`/practice/sql/${fixtures.sql.slug}`)
    await expect(page.getByRole('main').getByRole('heading', { level: 1 })).toBeVisible({
      timeout: 30_000,
    })
    await page.reload()
    await expect(page.getByRole('main').getByRole('heading', { level: 1 })).toBeVisible({
      timeout: 30_000,
    })
    await expect(page).not.toHaveURL(/404/)
    guard.assertClean()
  })

  test('unknown route shows not found', async ({ page }) => {
    await page.goto('/this-route-does-not-exist-7-2')
    await expect(page.getByText(/page not found|not found/i)).toBeVisible()
    await expect(page.getByRole('main').getByRole('link', { name: /^dashboard$/i })).toBeVisible()
    await expect(page.getByRole('main').getByRole('link', { name: /practice hub/i })).toBeVisible()
  })
})

test.describe('Admin smoke', () => {
  test('admin routes open for admin and block student', async ({ page }) => {
    await loginAs(page, fixtures.users.student)
    await page.goto('/admin/questions')
    // AdminRoute sends non-admins to the dashboard
    await expect(page).toHaveURL(/\/($|\?)/)
    await expect(page.getByRole('heading', { name: /welcome back/i })).toBeVisible()

    await page.evaluate(() => localStorage.clear())
    await loginAs(page, fixtures.users.admin)
    for (const route of [
      '/admin/questions',
      '/admin/sql',
      '/admin/coding',
      '/admin/content',
      '/admin/practice-paths',
      '/admin/courses',
      '/admin/projects',
      '/admin/ai',
      '/admin/scenarios',
    ]) {
      await page.goto(route)
      await expect(page.getByRole('heading').first()).toBeVisible({ timeout: 20_000 })
    }
  })
})
