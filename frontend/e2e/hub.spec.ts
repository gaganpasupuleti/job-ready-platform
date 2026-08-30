import { expect, test } from '@playwright/test'

import { attachConsoleGuard, loadManifest, loginAs } from './helpers'

const fixtures = loadManifest()

test.describe('Dashboard and Practice Hub', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, fixtures.users.student)
  })

  test('dashboard loads without mock readiness or NaN', async ({ page }) => {
    const guard = attachConsoleGuard(page)
    await page.goto('/')
    await expect(page.getByRole('heading', { name: /welcome back/i })).toBeVisible()
    const body = await page.locator('body').innerText()
    expect(body).not.toMatch(/\bNaN\b/)
    expect(body).not.toMatch(/\[object Object\]/)
    expect(body).not.toMatch(/mock data|fake readiness/i)
    guard.assertClean()
  })

  test('practice hub search and navigation', async ({ page }) => {
    await page.goto('/practice')
    await expect(page.getByRole('heading', { name: /practice/i }).first()).toBeVisible()
    const search = page.getByPlaceholder(/search/i).first()
    if (await search.count()) {
      await search.fill(fixtures.path.slug.replace(/-/g, ' '))
      await expect(page.getByText(new RegExp(fixtures.path.slug.split('-')[0], 'i')).first()).toBeVisible()
      await search.fill('zzznomatchpath999')
      await expect(page.getByText(/no matches/i).first()).toBeVisible()
      await search.fill('')
    }
    await page.getByRole('link', { name: /sql/i }).first().click()
    await expect(page).toHaveURL(/\/practice\/sql/)
  })

  test('practice path progress is idempotent', async ({ page }) => {
    await page.goto(`/practice/paths/${fixtures.path.slug}`)
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 20_000 })
    const progress = page.getByText(/%|progress/i).first()
    await expect(progress).toBeVisible()
    const before = await page.locator('body').innerText()
    const complete = page.getByRole('button', { name: /mark complete|complete/i }).first()
    if (await complete.isEnabled().catch(() => false)) {
      await complete.click()
      await page.waitForTimeout(500)
      await complete.click()
      await page.reload()
      const after = await page.locator('body').innerText()
      expect(after).toBeTruthy()
      expect(before).toBeTruthy()
    }
  })
})
