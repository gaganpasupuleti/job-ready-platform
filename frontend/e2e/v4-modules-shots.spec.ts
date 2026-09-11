import { expect, test } from '@playwright/test'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { loadManifest, loginAs } from './helpers'

const fixtures = loadManifest()
const __dirname = path.dirname(fileURLToPath(import.meta.url))
const outDir = path.join(__dirname, 'artifacts', 'v4-modules')

test.describe('V4 module visual shots', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, fixtures.users.student)
  })

  test('capture overview practice learn jobs studios', async ({ page }, testInfo) => {
    const project = testInfo.project.name
    const shots: Array<{ name: string; url: string }> = [
      { name: 'overview', url: '/' },
      { name: 'practice-hub', url: '/practice' },
      { name: 'learn', url: '/learn' },
      { name: 'jobs', url: '/jobs' },
      { name: 'python-playground', url: '/practice/python' },
    ]

    for (const shot of shots) {
      await page.goto(shot.url)
      await expect(page.locator('main, .home-v4, .module-page, .studio-main').first()).toBeVisible({
        timeout: 20_000,
      })
      await page.screenshot({
        path: path.join(outDir, `${project}-${shot.name}.png`),
        fullPage: true,
      })
    }

    // Coding workspace if manifest has a problem
    if (fixtures.coding?.id || fixtures.coding?.slug) {
      const id = fixtures.coding.id || fixtures.coding.slug
      await page.goto(`/practice/dsa/${id}`)
      await expect(page.locator('.studio-main, .dsa-workbench').first()).toBeVisible({
        timeout: 20_000,
      })
      await page.screenshot({
        path: path.join(outDir, `${project}-dsa-workspace.png`),
        fullPage: false,
      })
    }
  })
})
