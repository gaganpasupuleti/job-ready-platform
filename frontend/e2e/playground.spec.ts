import { expect, test } from '@playwright/test'

import { loadManifest, loginAs } from './helpers'

const fixtures = loadManifest()

test.describe('Python Playground', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, fixtures.users.student)
  })

  test('playground stays locked with no run control', async ({ page }) => {
    await page.goto('/practice/python')
    const mainHeading = page.getByRole('main').getByRole('heading', {
      level: 1,
      name: 'Python — Coming soon',
    })
    await expect(mainHeading).toBeVisible({ timeout: 15_000 })
    await expect(mainHeading).toHaveCount(1)
    await expect(page.getByText('Python execution is locked. This page does not run or grade code.')).toBeVisible()
    await expect(page.getByRole('button', { name: /^run$/i })).toHaveCount(0)
    await expect(page.locator('.monaco-editor')).toHaveCount(0)
  })

  test('compiler aliases stay locked', async ({ page }) => {
    await page.goto('/practice/compiler/python')
    await expect(page.getByText('Python — Coming soon')).toBeVisible({ timeout: 15_000 })
    await expect(page.locator('.monaco-editor')).toHaveCount(0)
  })

  test('locked page does not call the runner', async ({ page }) => {
    let runCalls = 0
    page.on('request', (request) => {
      if (request.url().includes('/playground/run') && request.method() === 'POST') runCalls += 1
    })
    await page.goto('/practice/python')
    await expect(page.getByText('Python execution is locked. This page does not run or grade code.')).toBeVisible({
      timeout: 15_000,
    })
    await page.keyboard.press('Control+Enter')
    expect(runCalls).toBe(0)
    await expect(page.getByText(/stdout/i)).toHaveCount(0)
  })
})

test.describe('SQL Playground', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, fixtures.users.student)
  })

  test('masthead playground opens the SQL IDE path', async ({ page }) => {
    await page.goto('/practice/playground')
    await page.getByTestId('sql-playground-tile').click()
    await expect(page.getByTestId('sql-playground-heading')).toBeVisible({ timeout: 15_000 })
    await expect(page.getByRole('button', { name: /run query/i })).toBeVisible()
  })
})
