import { expect, test } from '@playwright/test'

import { loadManifest, loginAs } from './helpers'

const fixtures = loadManifest()

test.describe('Mistake Book', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, fixtures.users.student)
  })

  test('mistakes page loads', async ({ page }) => {
    await page.goto('/mistakes')
    await expect(page.getByRole('heading', { name: 'Mistake Book' })).toBeVisible({ timeout: 20_000 })
  })

  test('filter chips render', async ({ page }) => {
    await page.goto('/mistakes')
    await expect(page.getByRole('button', { name: 'mcq' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'sql' })).toBeVisible()
  })
})
