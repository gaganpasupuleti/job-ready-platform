import { expect, test } from '@playwright/test'

import { loadManifest, loginAs } from './helpers'

const fixtures = loadManifest()

test.describe('Coding / DSA with Judge0 disabled', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, fixtures.users.student)
  })

  test('workspace loads with execution unavailable banner', async ({ page }) => {
    test.skip(!fixtures.coding.id, 'No coding problem seeded')
    await page.goto(`/practice/dsa/${fixtures.coding.id}`)
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 30_000 })
    await expect(page.getByText(/execution is temporarily unavailable|currently unavailable/i)).toBeVisible()
    await expect(page.getByRole('button', { name: /^run$/i })).toBeDisabled()
    await expect(page.getByRole('button', { name: /^submit$/i })).toBeDisabled()
    const codeTab = page.getByRole('button', { name: /^code$/i })
    if (await codeTab.count()) await codeTab.click()
    await expect(page.locator('.monaco-editor:visible').first()).toBeVisible({ timeout: 30_000 })
  })

  test('draft persists while execution is off', async ({ page }) => {
    test.skip(!fixtures.coding.id, 'No coding problem seeded')
    await page.goto(`/practice/dsa/${fixtures.coding.id}`)
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 30_000 })
    const marker = `# e2e-draft-${Date.now()}`
    await page.evaluate(
      ({ problemId, markerText }) => {
        const keys = Object.keys(localStorage).filter((k) => k.includes(problemId) && k.startsWith('coding-draft:'))
        const key =
          keys[0] ||
          `coding-draft:anon:${problemId}:71`
        localStorage.setItem(key, `${markerText}\nprint("persisted")`)
      },
      { problemId: fixtures.coding.id!, markerText: marker },
    )
    await page.reload()
    const codeTab = page.getByRole('button', { name: /^code$/i })
    if (await codeTab.count()) await codeTab.click()
    await expect(page.getByText(marker)).toBeVisible({ timeout: 15_000 })
  })
})
