/**
 * Live API smoke against vite preview (E2E_SKIP_WEBSERVER=1).
 * Does not replace mocked UI specs; proves production bundle + real backend.
 */
import { expect, test } from '@playwright/test'

import { jobDetailRoot, loadManifest, loginAs } from './helpers'

const fixtures = loadManifest()

test.describe('Release preview smoke (live API)', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, fixtures.users.student)
  })

  test('core student surfaces render on preview build', async ({ page }) => {
    await page.goto('/jobs')
    await expect(page.locator('#main-content')).toBeVisible({ timeout: 20_000 })

    await page.goto('/practice/projects')
    await expect(page.getByRole('heading', { name: 'Projects' })).toBeVisible({ timeout: 20_000 })
    await expect(page.locator('#main-content')).toBeVisible()

    await page.goto('/roadmaps')
    await expect(page.locator('#main-content')).toBeVisible({ timeout: 20_000 })
  })

  test('jobs save control is scoped on detail', async ({ page }) => {
    const slug = 'data-engineer-remote-infosys'
    await page.goto(`/jobs/${slug}`)
    const detail = jobDetailRoot(page, slug)
    await expect(detail.getByRole('button', { name: /save job|^saved$/i })).toBeVisible({
      timeout: 20_000,
    })
  })
})
