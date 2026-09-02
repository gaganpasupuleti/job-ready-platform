import { expect, test } from '@playwright/test'

import { loadManifest, loginAs } from './helpers'

const fixtures = loadManifest()

test.describe('Readiness', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, fixtures.users.student)
  })

  test('readiness page loads with disclaimer', async ({ page }) => {
    await page.goto('/readiness')
    await expect(page.getByRole('heading', { name: 'Job Readiness' })).toBeVisible({ timeout: 20_000 })
    await expect(page.getByText(/not a prediction of hiring outcomes/i)).toBeVisible()
  })

  test('why score toggle', async ({ page }) => {
    await page.goto('/readiness')
    const why = page.getByRole('button', { name: /why this score/i })
    if (await why.isVisible()) {
      await why.click()
      await expect(page.getByText(/importance|effective|evidence/i).first()).toBeVisible()
    }
  })

  test('student blocked from admin readiness', async ({ page }) => {
    await page.goto('/admin/readiness')
    await expect(page).not.toHaveURL(/\/admin\/readiness/)
  })
})

test.describe('Readiness admin', () => {
  test('admin readiness route works', async ({ page }) => {
    await loginAs(page, fixtures.users.admin)
    await page.goto('/admin/readiness')
    await expect(page.getByRole('heading', { name: /readiness config/i })).toBeVisible({
      timeout: 20_000,
    })
  })
})
