import { expect, test } from '@playwright/test'

import { ensureCodingFixture, loadManifest, loginAs, type CodingFixture } from './helpers'

const fixtures = loadManifest()
let coding: CodingFixture

test.describe('Coding / DSA with Judge0 disabled', () => {
  test.beforeAll(async ({ request }) => {
    coding = await ensureCodingFixture(request, fixtures.coding)
  })

  test.beforeEach(async ({ page }) => {
    await loginAs(page, fixtures.users.student)
  })

  test('workspace loads with execution unavailable banner', async ({ page }) => {
    await page.goto(`/practice/dsa/${coding.id}`)
    await expect(page.getByRole('main').getByRole('heading', { level: 1 })).toBeVisible({
      timeout: 30_000,
    })
    await expect(
      page.getByRole('status').filter({
        hasText: 'Code execution is coming soon. You can write code and save drafts.',
      }),
    ).toBeVisible()
    await expect(page.getByRole('button', { name: /^run$/i })).toBeDisabled()
    await expect(page.getByRole('button', { name: /^submit$/i })).toBeDisabled()
    const codeTab = page.getByRole('button', { name: /^code$/i })
    if (await codeTab.count()) await codeTab.click()
    await expect(page.locator('.monaco-editor:visible').first()).toBeVisible({ timeout: 30_000 })
  })

  test('draft persists while execution is off', async ({ page }) => {
    await page.goto(`/practice/dsa/${coding.id}`)
    await expect(page.getByRole('main').getByRole('heading', { level: 1 })).toBeVisible({
      timeout: 30_000,
    })
    const marker = `# e2e-draft-${Date.now()}`
    await page.evaluate(
      ({ problemId, markerText }) => {
        const keys = Object.keys(localStorage).filter(
          (k) => k.includes(problemId) && k.startsWith('coding-draft:'),
        )
        const key = keys[0] || `coding-draft:anon:${problemId}:71`
        localStorage.setItem(key, `${markerText}\nprint("persisted")`)
      },
      { problemId: coding.id, markerText: marker },
    )
    await page.reload()
    const codeTab = page.getByRole('button', { name: /^code$/i })
    if (await codeTab.count()) await codeTab.click()
    await expect(page.getByText(marker)).toBeVisible({ timeout: 15_000 })
  })

  test('keyboard shortcuts cannot run or submit while execution is locked', async ({ page }) => {
    await page.goto(`/practice/dsa/${coding.id}`)
    await expect(
      page.getByRole('status').filter({
        hasText: 'Code execution is coming soon. You can write code and save drafts.',
      }),
    ).toBeVisible()
    const run = page.getByRole('button', { name: /^run$/i })
    const submit = page.getByRole('button', { name: /^submit$/i })
    await expect(run).toBeDisabled()
    await expect(submit).toBeDisabled()
    await page.locator('.monaco-editor:visible').first().click()
    let executionCalls = 0
    page.on('request', (request) => {
      if (/\/run$|\/submit$/.test(request.url()) && request.method() === 'POST') {
        executionCalls += 1
      }
    })
    await page.keyboard.press('Control+Enter')
    await page.keyboard.press('Control+Shift+Enter')
    await expect(run).toBeDisabled()
    await expect(submit).toBeDisabled()
    expect(executionCalls).toBe(0)
  })
})
