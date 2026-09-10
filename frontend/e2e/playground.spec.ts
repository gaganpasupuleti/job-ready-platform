import { expect, test } from '@playwright/test'

import { loadManifest, loginAs } from './helpers'

const fixtures = loadManifest()

test.describe('Python Playground', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, fixtures.users.student)
  })

  test('playground loads with clear non-assessed labeling', async ({ page }) => {
    await page.goto('/practice/python')
    const mainHeading = page.getByRole('main').getByRole('heading', {
      level: 1,
      name: 'Python Playground',
    })
    await expect(mainHeading).toBeVisible({ timeout: 15_000 })
    await expect(mainHeading).toHaveCount(1)
    await expect(page.getByText(/not an assessed problem/i)).toBeVisible()
    await expect(page.getByRole('button', { name: /^run$/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /^reset$/i })).toBeVisible()
    await expect(page.getByLabel(/standard input/i)).toBeVisible()
  })

  test('unavailable executor does not fabricate stdout', async ({ page }) => {
    await page.route('**/api/v1/coding/execution-status**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          enabled: false,
          available: false,
          provider: 'none',
          message: 'Judge0 disabled in test',
          languages: [],
        }),
      })
    })
    await page.goto('/practice/python')
    await expect(
      page.getByRole('main').getByRole('status').filter({ hasText: /judge0 disabled|executor unavailable/i }),
    ).toBeVisible({
      timeout: 15_000,
    })
    await expect(page.getByRole('button', { name: /^run$/i })).toBeDisabled()
  })
})
