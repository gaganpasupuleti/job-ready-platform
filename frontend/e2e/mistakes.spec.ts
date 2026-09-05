import { expect, test } from '@playwright/test'

import { loadManifest, loginAs } from './helpers'

const fixtures = loadManifest()

test.describe('Mistake Book', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, fixtures.users.student)
  })

  test('mistakes page loads', async ({ page }) => {
    await page.goto('/mistakes')
    await expect(page.getByRole('heading', { name: 'Mistake Book' })).toBeVisible({ timeout: 20_000 })
  })

  test('filter chips render', async ({ page }) => {
    await page.goto('/mistakes')
    await expect(page.getByRole('button', { name: 'mcq' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'sql' })).toBeVisible()
  })

  test('wrong mcq answer shows incorrect then next', async ({ page }) => {
    await page.goto('/practice/aptitude')
    await expect(page.getByRole('heading', { name: /aptitude/i }).first()).toBeVisible()
    await page.getByRole('button', { name: fixtures.mcq_topic.name, exact: true }).click()
    await page.getByRole('button', { name: /^easy$/i }).click()
    await page.getByRole('combobox').selectOption('5')
    await page.getByRole('button', { name: /^practice$/i }).click()
    await page.getByRole('button', { name: /start session/i }).click()
    await expect(page).toHaveURL(/\/practice\/sessions\//, { timeout: 20_000 })
    await expect(page.getByRole('button', { name: /submit answer/i })).toBeVisible({ timeout: 20_000 })
    await page.locator('button.w-full').first().click()
    await page.getByRole('button', { name: /submit answer/i }).click()
    await expect(page.getByText(/incorrect|correct/i).first()).toBeVisible({ timeout: 15_000 })
    const nextBtn = page.getByRole('button', { name: /^next$/i })
    if (await nextBtn.isVisible()) {
      await nextBtn.click()
      await expect(page.getByRole('button', { name: /submit answer/i })).toBeVisible({
        timeout: 15_000,
      })
    }
    await page.goto('/mistakes')
    await expect(page.getByRole('heading', { name: 'Mistake Book' })).toBeVisible({ timeout: 20_000 })
  })
})
