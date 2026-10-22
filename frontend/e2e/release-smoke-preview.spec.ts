/**
 * Live API smoke against vite preview (E2E_SKIP_WEBSERVER=1).
 * Does not replace mocked UI specs; proves production bundle + real backend.
 */
import { expect, test } from '@playwright/test'

import { jobDetailRoot, loadManifest, loginAs } from './helpers'

const fixtures = loadManifest()
const LIVE_JOB_SLUG = 'data-engineer-remote-infosys'

test.describe('Release preview smoke (live API)', () => {
  test.skip(
    !process.env.E2E_SKIP_WEBSERVER,
    'Runs only against vite preview (set E2E_SKIP_WEBSERVER=1 via scripts/run-release-smoke.ps1)',
  )
  test.beforeEach(async ({ page }) => {
    await loginAs(page, fixtures.users.student)
  })

  test('core student surfaces render on preview build', async ({ page }) => {
    await page.goto('/jobs')
    await expect(page.locator('#main-content')).toBeVisible({ timeout: 20_000 })

    await page.goto('/practice/projects')
    await expect(page.locator('.jr-page-title', { hasText: 'Projects' })).toBeVisible({ timeout: 20_000 })
    await expect(page.locator('#main-content')).toBeVisible()

    await page.goto('/roadmaps')
    await expect(page.locator('#main-content')).toBeVisible({ timeout: 20_000 })
  })

  test('jobs save and unsave on preview', async ({ page }) => {
    await page.goto(`/jobs/${LIVE_JOB_SLUG}`)
    const detail = jobDetailRoot(page, LIVE_JOB_SLUG)
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 20_000 })
    const saveBtn = detail.getByRole('button', { name: /save job|^saved$/i })
    await expect(saveBtn).toBeVisible({ timeout: 20_000 })
    const label = (await saveBtn.textContent())?.trim() ?? ''
    if (/save job/i.test(label)) {
      await saveBtn.click()
      await expect(detail.getByRole('button', { name: /^saved$/i })).toBeVisible()
    }
    await page.reload()
    await expect(detail.getByRole('button', { name: /^saved$/i })).toBeVisible({ timeout: 20_000 })

    await detail.getByRole('button', { name: /^saved$/i }).click()
    await expect(detail.getByRole('button', { name: /save job/i })).toBeVisible()
    await page.reload()
    await expect(detail.getByRole('button', { name: /save job/i })).toBeVisible({ timeout: 20_000 })
  })

  test('live roadmap article opens on preview', async ({ page }) => {
    await page.goto('/roadmaps/api-design')
    await expect(page.getByRole('heading', { name: /api design/i })).toBeVisible({ timeout: 30_000 })
    await expect(page.locator('.ors-canvas .react-flow')).toBeVisible({ timeout: 60_000 })
    const topic = page.locator('.ors-node--topic').first()
    await expect(topic).toBeVisible({ timeout: 20_000 })
    await topic.click()
    const articleHeading = page.getByRole('heading', { level: 2 })
    await expect(articleHeading).toBeVisible({ timeout: 30_000 })
    const articleText = await page.locator('.ors-panel--desktop .ors-markdown').innerText()
    expect(articleText.replace(/\s+/g, ' ').trim().length).toBeGreaterThan(80)
    expect(articleText.toLowerCase()).not.toMatch(/^#?\s*\w+\s*$/)
  })
})
