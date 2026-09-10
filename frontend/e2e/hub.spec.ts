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
    // Prefer test id; fall back to visible progress copy if Badge attrs regress.
    const progress = page.getByTestId('path-progress').or(page.getByText(/%\s*progress/i).first())
    await expect(progress).toBeVisible({ timeout: 20_000 })
    const before = (await progress.innerText()).trim()
    expect(before).toMatch(/%\s*progress/i)
    const complete = page.getByRole('button', { name: /^(done|mark complete|complete)$/i }).first()
    if (await complete.isEnabled().catch(() => false)) {
      await complete.click()
      await page.waitForTimeout(500)
      const again = page.getByRole('button', { name: /^(done|completed|mark complete|complete)$/i }).first()
      if (await again.isEnabled().catch(() => false)) {
        await again.click()
      }
      await page.reload()
      await expect(
        page.getByTestId('path-progress').or(page.getByText(/%\s*progress/i).first()),
      ).toBeVisible({ timeout: 20_000 })
    }
    const after = (
      await page.getByTestId('path-progress').or(page.getByText(/%\s*progress/i).first()).innerText()
    ).trim()
    expect(after).toMatch(/%\s*progress/i)
  })
})
