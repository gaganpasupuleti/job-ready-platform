import { expect, test } from '@playwright/test'

import { attachConsoleGuard, fillMonaco, loadManifest, loginAs } from './helpers'

const fixtures = loadManifest()
const apiUrl = process.env.E2E_API_URL || 'http://127.0.0.1:8000'

async function sqlSandboxReady(): Promise<boolean> {
  try {
    const res = await fetch(`${apiUrl}/api/v1/sql/execution-status`)
    if (!res.ok) return false
    const data = (await res.json()) as { available?: boolean; status?: string }
    return Boolean(data.available) && data.status !== 'sandbox_unavailable'
  } catch {
    return false
  }
}

test.describe('SQL practice', () => {
  test.beforeEach(async ({ page }) => {
    test.skip(!(await sqlSandboxReady()), 'SQL sandbox unavailable — start postgres_sql_sandbox')
    await loginAs(page, fixtures.users.student)
  })

  test('run success recovers button and shows rows', async ({ page }) => {
    const guard = attachConsoleGuard(page)
    await page.goto(`/practice/sql/${fixtures.sql.slug}`)
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 30_000 })
    await fillMonaco(page, fixtures.sql.accepted_query)
    const run = page.getByRole('button', { name: /^run$/i })
    await run.click()
    await expect(page.getByRole('button', { name: /running/i })).toBeVisible()
    await expect(run).toBeEnabled({ timeout: 45_000 })
    await expect(page.getByText(/row/i).first()).toBeVisible()
    guard.assertClean()
  })

  test('syntax error recovers from Running', async ({ page }) => {
    await page.goto(`/practice/sql/${fixtures.sql.slug}`)
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 30_000 })
    await fillMonaco(page, fixtures.sql.invalid_query)
    const run = page.getByRole('button', { name: /^run$/i })
    await run.click()
    await expect(run).toBeEnabled({ timeout: 45_000 })
    await expect(page.getByText(/error|syntax|failed|invalid/i).first()).toBeVisible()
  })

  test('blocked statement is rejected safely', async ({ page }) => {
    await page.goto(`/practice/sql/${fixtures.sql.slug}`)
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 30_000 })
    await fillMonaco(page, fixtures.sql.blocked_query)
    const run = page.getByRole('button', { name: /^run$/i })
    await run.click()
    await expect(run).toBeEnabled({ timeout: 45_000 })
    await expect(page.getByText(/only select|read-only|not allowed|forbidden|blocked|safety/i).first()).toBeVisible()
  })

  test('wrong submit does not reveal expected rows', async ({ page }) => {
    await page.goto(`/practice/sql/${fixtures.sql.slug}`)
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 30_000 })
    await fillMonaco(page, fixtures.sql.wrong_query)
    const submit = page.getByRole('button', { name: /^submit$/i })
    await submit.click()
    await expect(submit).toBeEnabled({ timeout: 45_000 })
    await expect(page.getByText(/wrong answer|incorrect|not match/i).first()).toBeVisible()
    await expect(page.getByText(/hidden|expected result rows stay hidden/i).first()).toBeVisible()
  })

  test('accepted submit unlocks solution path', async ({ page }) => {
    await page.goto(`/practice/sql/${fixtures.sql.slug}`)
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 30_000 })
    await fillMonaco(page, fixtures.sql.accepted_query)
    const submit = page.getByRole('button', { name: /^submit$/i })
    await submit.click()
    await expect(page.getByText(/accepted/i).first()).toBeVisible({ timeout: 45_000 })
    await expect(submit).toBeEnabled()
    const solutionTab = page.getByRole('tab', { name: /solution/i })
    if (await solutionTab.count()) {
      await solutionTab.click()
      await expect(page.getByText(/solution|explanation|query/i).first()).toBeVisible()
    }
    await page.reload()
    await expect(page.getByText(/solved|accepted/i).first()).toBeVisible()
  })

  test('draft persists across reload', async ({ page }) => {
    await page.goto(`/practice/sql/${fixtures.sql.slug}`)
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 30_000 })
    const marker = `-- e2e-draft-${Date.now()}`
    await fillMonaco(page, `${marker}\nSELECT 1`)
    await page.waitForTimeout(400)
    await page.reload()
    await expect(page.locator('.monaco-editor')).toBeVisible({ timeout: 30_000 })
    await expect(page.getByText(marker)).toBeVisible({ timeout: 10_000 })
  })
})
