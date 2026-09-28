import { expect, test } from '@playwright/test'

import { loginAs, loadManifest } from './helpers'

const fixtures = loadManifest()

test.describe('Visual foundation keyboard & shells', () => {
  test('theme toggle and practice hub search are keyboard reachable', async ({ page }) => {
    await loginAs(page, fixtures.users.student)
    await page.goto('/practice')
    await expect(page.getByRole('heading', { name: /practice hub/i })).toBeVisible({
      timeout: 15_000,
    })

    const search = page.getByLabel(/search practice content/i)
    await search.focus()
    await expect(search).toBeFocused()
    await search.fill('python')
    await expect(search).toHaveValue('python')

    const themeToggle = page.getByRole('button', { name: /switch to (dark|light) mode/i })
    await themeToggle.focus()
    await expect(themeToggle).toBeFocused()
    const beforeDark = await page.locator('html').evaluate((el) => el.classList.contains('dark'))
    await themeToggle.press('Enter')
    await expect
      .poll(async () => page.locator('html').evaluate((el) => el.classList.contains('dark')))
      .not.toBe(beforeDark)
  })

  test('coding page language filters expose pressed state', async ({ page }) => {
    await loginAs(page, fixtures.users.student)
    await page.goto('/practice/coding')
    await expect(page.getByRole('heading', { name: /coding practice/i })).toBeVisible({
      timeout: 15_000,
    })
    const group = page.getByRole('group', { name: /language filter/i })
    await expect(group).toBeVisible()
    const python = group.getByRole('button', { name: 'Python — Coming soon' })
    await expect(python).toBeDisabled()
    await expect(python).toHaveAttribute('aria-pressed', 'false')
    const javascript = group.getByRole('button', { name: 'JS' })
    await javascript.focus()
    await javascript.press('Enter')
    await expect(javascript).toHaveAttribute('aria-pressed', 'true')
  })

  test('assessment and focused shells set data-shell', async ({ page }) => {
    await loginAs(page, fixtures.users.student)
    await page.goto('/practice/aptitude')
    await page.getByRole('button', { name: fixtures.mcq_topic.name, exact: true }).click()
    await page.getByRole('button', { name: /^easy$/i }).click()
    await page.getByRole('combobox').selectOption('5')
    await page.getByRole('button', { name: /^exam$/i }).click()
    await page.getByRole('button', { name: /start session/i }).click()
    await expect(page).toHaveURL(/\/practice\/sessions\//, { timeout: 20_000 })
    await expect(page.locator('[data-shell="assessment"]')).toBeVisible()

    test.skip(!fixtures.coding.id, 'No coding problem seeded')
    await page.goto(`/practice/dsa/${fixtures.coding.id}`)
    await expect(page.locator('[data-shell="focused"]')).toBeVisible({ timeout: 20_000 })
  })
})
