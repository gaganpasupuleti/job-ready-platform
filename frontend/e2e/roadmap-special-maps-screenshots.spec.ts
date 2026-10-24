/**
 * Desktop + mobile screenshots for PR24 special-case official roadmap graphs (live API).
 */
import { expect, test } from '@playwright/test'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { loadManifest, loginAs } from './helpers'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const shotDir = path.join(__dirname, 'artifacts', 'special-roadmap-maps')

const SPECIAL_SLUGS = [
  'code-review',
  'data-analyst',
  'ux-design',
  'design-system',
  'django',
  'javascript',
  'golang',
  'mongodb',
] as const

const fixtures = loadManifest()

test.describe('Special roadmap maps (live screenshots)', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, fixtures.users.student)
  })

  for (const slug of SPECIAL_SLUGS) {
    test(`${slug} desktop canvas`, async ({ page }) => {
      test.setTimeout(120_000)
      await page.setViewportSize({ width: 1366, height: 768 })
      await page.goto(`/roadmaps/${slug}`)
      await expect(page.locator('.ors-canvas .react-flow')).toBeVisible({ timeout: 90_000 })
      await page.screenshot({ path: path.join(shotDir, `${slug}-desktop-1366.png`) })
    })

    test(`${slug} mobile canvas`, async ({ page }) => {
      test.setTimeout(120_000)
      await page.setViewportSize({ width: 390, height: 844 })
      await page.goto(`/roadmaps/${slug}`)
      await expect(page.locator('.ors-canvas .react-flow')).toBeVisible({ timeout: 90_000 })
      await page.screenshot({ path: path.join(shotDir, `${slug}-mobile-390.png`) })
    })
  }
})
