/**
 * Live roadmap catalog rendering (E2E seed backend). Separate from mocked roadmap-mock specs.
 */
import { expect, test } from '@playwright/test'

import { loadManifest, loginAs } from './helpers'

const fixtures = loadManifest()

test.describe('Roadmap catalog render (live)', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, fixtures.users.student)
  })

  test('catalog and representative graph mount', async ({ page }) => {
    await page.goto('/roadmaps')
    await expect(page.locator('#main-content')).toBeVisible({ timeout: 20_000 })

    await page.goto('/roadmaps/api-design')
    await expect(page.getByRole('heading', { name: 'API Design' })).toBeVisible({ timeout: 30_000 })
    await expect(page.locator('.react-flow')).toBeVisible({ timeout: 45_000 })
  })
})
