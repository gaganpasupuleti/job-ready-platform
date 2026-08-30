import { expect, test } from '@playwright/test'

import { loadManifest, loginAs } from './helpers'

const fixtures = loadManifest()

test.describe('MCQ practice and exam', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, fixtures.users.student)
  })

  test('aptitude practice session starts and shows a question', async ({ page }) => {
    await page.goto('/practice/aptitude')
    await expect(page.getByRole('heading', { name: /aptitude/i }).first()).toBeVisible()
    await page.getByRole('button', { name: fixtures.mcq_topic.name, exact: true }).click()
    await page.getByRole('button', { name: /^easy$/i }).click()
    await page.getByRole('combobox').selectOption('5')
    await page.getByRole('button', { name: /^practice$/i }).click()
    await page.getByRole('button', { name: /start session/i }).click()
    await expect(page.getByText(/no questions found/i)).toHaveCount(0)
    await expect(page).toHaveURL(/\/practice\/sessions\//, { timeout: 20_000 })
    await expect(page.getByText(/question|option|submit|clear/i).first()).toBeVisible({
      timeout: 20_000,
    })
  })

  test('exam mode can be selected from aptitude catalog', async ({ page }) => {
    await page.goto('/practice/aptitude')
    await page.getByRole('button', { name: /^exam$/i }).click()
    await expect(page.getByText(/answers and explanations are hidden/i)).toBeVisible()
  })
})
