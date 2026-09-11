import { expect, test } from '@playwright/test'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { ensureCodingFixture, loadManifest, loginAs, type CodingFixture } from './helpers'

const fixtures = loadManifest()
const __dirname = path.dirname(fileURLToPath(import.meta.url))
const outDir = path.join(__dirname, 'artifacts', 'v4-modules')
let coding: CodingFixture | null = null

test.describe('V4 module visual shots', () => {
  test.beforeAll(async ({ request }) => {
    coding = await ensureCodingFixture(request, fixtures.coding)
  })

  test.beforeEach(async ({ page }) => {
    await loginAs(page, fixtures.users.student)
  })

  test('capture overview practice learn jobs studios sql mcq', async ({ page }, testInfo) => {
    const project = testInfo.project.name

    await page.goto('/')
    await expect(page.getByRole('heading', { name: /a little practice/i })).toBeVisible({
      timeout: 20_000,
    })
    await page.screenshot({ path: path.join(outDir, `${project}-overview.png`), fullPage: true })

    await page.goto('/practice')
    await expect(page.getByRole('heading', { name: /practice hub/i })).toBeVisible({
      timeout: 20_000,
    })
    await page.screenshot({
      path: path.join(outDir, `${project}-practice-hub.png`),
      fullPage: true,
    })

    await page.goto('/learn')
    await expect(page.getByRole('heading', { name: /interactive courses/i })).toBeVisible({
      timeout: 20_000,
    })
    await page.screenshot({ path: path.join(outDir, `${project}-learn.png`), fullPage: true })

    await page.goto('/jobs')
    await expect(page.getByRole('heading', { name: /^jobs$/i })).toBeVisible({ timeout: 20_000 })
    await expect(page.getByText(/\d+ jobs? found|no jobs match/i).first()).toBeVisible({
      timeout: 20_000,
    })
    await page.screenshot({ path: path.join(outDir, `${project}-jobs.png`), fullPage: true })

    await page.goto('/practice/python')
    await expect(page.getByRole('heading', { name: /python playground/i })).toBeVisible({
      timeout: 20_000,
    })
    await expect(page.getByText(/currently unavailable|temporarily unavailable/i).first()).toBeVisible()
    await expect(page.locator('.monaco-editor').first()).toBeVisible({ timeout: 45_000 })
    await page.screenshot({
      path: path.join(outDir, `${project}-python-playground.png`),
      fullPage: false,
    })

    if (!coding) {
      throw new Error('Acceptance fixture missing: coding problem was not resolved in beforeAll')
    }
    await page.goto(`/practice/dsa/${coding.id}`)
    await expect(page.locator('.studio-main, .dsa-workbench').first()).toBeVisible({
      timeout: 20_000,
    })
    await expect(page.getByText(/currently unavailable|temporarily unavailable/i).first()).toBeVisible()
    const codeTab = page.getByRole('button', { name: /^code$/i })
    if (await codeTab.count()) await codeTab.click()
    await expect(page.locator('.monaco-editor').first()).toBeVisible({ timeout: 45_000 })
    await page.screenshot({
      path: path.join(outDir, `${project}-dsa-workspace.png`),
      fullPage: false,
    })

    await page.goto(`/practice/sql/${fixtures.sql.slug}`)
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 20_000 })
    await expect(page.locator('.monaco-editor, .sql-workbench, .studio-main').first()).toBeVisible({
      timeout: 45_000,
    })
    await page.screenshot({
      path: path.join(outDir, `${project}-sql-studio.png`),
      fullPage: false,
    })

    await page.goto('/practice/aptitude')
    await expect(page.getByRole('heading', { name: /aptitude/i }).first()).toBeVisible({
      timeout: 20_000,
    })
    await page.getByRole('button', { name: fixtures.mcq_topic.name, exact: true }).click()
    await page.getByRole('button', { name: /^easy$/i }).click()
    await page.getByRole('combobox').selectOption('5')
    await page.getByRole('button', { name: /^practice$/i }).click()
    await page.getByRole('button', { name: /start session/i }).click()
    await expect(page).toHaveURL(/\/practice\/sessions\//, { timeout: 20_000 })
    await expect(page.getByText(/question|option/i).first()).toBeVisible({ timeout: 20_000 })
    await page.screenshot({
      path: path.join(outDir, `${project}-mcq-session.png`),
      fullPage: false,
    })
  })
})
