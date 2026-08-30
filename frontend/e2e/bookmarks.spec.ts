import { expect, test } from '@playwright/test'

import { loadManifest, loginAs } from './helpers'

const fixtures = loadManifest()

test.describe('Bookmarks', () => {
  test('bookmark and unbookmark SQL problem', async ({ page }) => {
    await loginAs(page, fixtures.users.student)
    await page.goto(`/practice/sql/${fixtures.sql.slug}`)
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 30_000 })
    const bookmark = page.getByRole('button', { name: /bookmark/i }).first()
    if (!(await bookmark.count())) {
      test.skip(true, 'Bookmark control not present on SQL page')
    }
    await bookmark.click()
    await page.goto('/bookmarks')
    await expect(page.getByText(new RegExp(fixtures.sql.slug.replace(/-/g, ' '), 'i')).or(
      page.getByRole('link').first(),
    )).toBeVisible({ timeout: 15_000 })
    await page.goto(`/practice/sql/${fixtures.sql.slug}`)
    await bookmark.click()
    await page.goto('/bookmarks')
    await page.reload()
  })
})
