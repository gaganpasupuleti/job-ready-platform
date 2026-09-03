import { expect, test } from '@playwright/test'

import { loadManifest, loginAs } from './helpers'

const fixtures = loadManifest()

test.describe('Interview practice', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, fixtures.users.student)
  })

  test('hub loads and packs are reachable', async ({ page }) => {
    await page.goto('/interviews')
    await expect(page.getByRole('heading', { name: /interview prep/i })).toBeVisible({
      timeout: 20_000,
    })
    await page.goto('/interviews/packs')
    await expect(page.getByRole('heading', { name: /interview packs/i })).toBeVisible({
      timeout: 20_000,
    })
    await page.goto('/interviews/packs/sql-interview-essentials')
    await expect(page.getByRole('button', { name: /start study/i })).toBeVisible({ timeout: 20_000 })
  })

  test('study session: reveal review complete results', async ({ page }) => {
    await page.goto('/interviews/packs/sql-interview-essentials')
    const study = page.getByRole('button', { name: /start study/i }).first()
    await expect(study).toBeVisible({ timeout: 20_000 })
    await study.click()
    await expect(page).toHaveURL(/\/interviews\/sessions\//, { timeout: 20_000 })
    await expect(page.getByLabel(/your answer notes/i)).toBeVisible({ timeout: 15_000 })
    await page.getByLabel(/your answer notes/i).fill(
      'Window functions keep result rows and support ranking.',
    )
    await expect(page.getByText(/expected answer/i).first()).toBeVisible()
    const checkbox = page.getByRole('checkbox').first()
    if (await checkbox.count()) await checkbox.check()
    await page.getByLabel(/^medium$/i).check()
    await page.getByLabel(/^good$/i).check()
    await page.getByRole('button', { name: /save self-review/i }).click()
    await page.getByRole('button', { name: /complete session/i }).click()
    await expect(page).toHaveURL(/\/results/, { timeout: 15_000 })
    await expect(page.getByText(/self-review|reviewed|coverage/i).first()).toBeVisible()
    // Disclaimers may say "not an interview score" — forbid positive score claims only.
    await expect(page.getByText(/\bhiring probability\b/i)).toHaveCount(0)
    await expect(page.getByText(/\bai rating\b/i)).toHaveCount(0)
    await expect(page.getByText(/your interview score|overall interview score/i)).toHaveCount(0)
  })

  test('mock mode hides expected answer until reveal', async ({ page }) => {
    await page.goto('/interviews/packs/behavioral-essentials')
    const mock = page.getByRole('button', { name: /start mock/i }).first()
    await expect(mock).toBeVisible({ timeout: 20_000 })
    await mock.click()
    await expect(page).toHaveURL(/\/interviews\/sessions\//)
    await expect(page.getByText(/expected answer/i)).toHaveCount(0)
    await page.getByRole('button', { name: /review my answer/i }).click()
    await expect(page.getByText(/expected answer|key point/i).first()).toBeVisible()
  })

  test('history progress review and company prep', async ({ page }) => {
    await page.goto('/interviews/history')
    await expect(page.getByRole('heading').first()).toBeVisible()
    await page.goto('/interviews/progress')
    await expect(page.getByRole('heading').first()).toBeVisible()
    await page.goto('/interviews/review')
    await expect(page.getByRole('heading').first()).toBeVisible()
    await page.goto('/company-prep')
    await expect(page.getByText(/not affiliated|hiring patterns|disclaimer/i).first()).toBeVisible({
      timeout: 15_000,
    })
  })

  test('admin interview packs blocked for student', async ({ page }) => {
    await page.goto('/admin/interviews/packs')
    await expect(page).toHaveURL(/\/($|\?)/)
  })
})
