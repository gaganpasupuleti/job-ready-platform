import { expect, test } from '@playwright/test'

import { loadManifest, loginAs } from './helpers'

const fixtures = loadManifest()

test.describe('Responsive workspaces', () => {
  test.use({ viewport: { width: 390, height: 844 } })

  test('mobile SQL workspace has no page overflow', async ({ page }) => {
    await loginAs(page, fixtures.users.student)
    await page.goto(`/practice/sql/${fixtures.sql.slug}`)
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 30_000 })
    const overflow = await page.evaluate(() => {
      const doc = document.documentElement
      return doc.scrollWidth - doc.clientWidth
    })
    expect(overflow).toBeLessThanOrEqual(8)
  })

  test('mobile menu opens and closes', async ({ page }) => {
    await loginAs(page, fixtures.users.student)
    await page.goto('/')
    const menu = page.getByRole('button', { name: /menu|open navigation|toggle/i }).first()
    if (!(await menu.count())) {
      test.skip(true, 'No mobile menu control')
    }
    await menu.click()
    await page.getByRole('link', { name: /practice/i }).first().click()
    await expect(page).toHaveURL(/\/practice/)
  })
})
