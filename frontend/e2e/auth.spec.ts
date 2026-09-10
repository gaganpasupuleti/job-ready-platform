import { expect, test } from '@playwright/test'

import { attachConsoleGuard, loadManifest, loginAs, logout, registerUser } from './helpers'

const fixtures = loadManifest()

test.describe('Auth', () => {
  test('invalid login shows error and stays on login', async ({ page }) => {
    const guard = attachConsoleGuard(page)
    await page.goto('/login')
    await page.getByLabel('Email').fill(fixtures.users.student.email)
    await page.getByLabel('Password').fill('WrongPassword999!')
    await page.getByRole('button', { name: /sign in/i }).click()
    await expect(page.getByText(/invalid|incorrect|failed|credentials/i)).toBeVisible()
    await expect(page).toHaveURL(/\/login/)
    guard.assertClean([/401|invalid|incorrect|failed/i])
  })

  test('login reaches dashboard and persists after reload', async ({ page }) => {
    await loginAs(page, fixtures.users.student)
    await expect(page.getByRole('heading', { name: /welcome back/i })).toBeVisible()
    await page.reload()
    await expect(page.getByRole('heading', { name: /welcome back/i })).toBeVisible()
  })

  test('protected route redirects when logged out', async ({ page }) => {
    await page.goto('/practice')
    await expect(page).toHaveURL(/\/login/)
  })

  test('logout clears session', async ({ page }) => {
    await loginAs(page, fixtures.users.student)
    await logout(page)
    await page.goto('/practice')
    await expect(page).toHaveURL(/\/login/)
  })

  test('AUTH-01 account switch does not flash prior private progress', async ({ page }) => {
    const suffix = Date.now().toString(36).slice(-6)
    const markerA = `PRIVATE_MARKER_A_${suffix}`
    const userA = {
      email: `e2e.cache.a.${suffix}@jobready.dev`,
      username: `e2ecachea${suffix}`,
      password: 'E2eStudent123!',
      fullName: `Cache User A ${markerA}`,
    }
    const userB = {
      email: `e2e.cache.b.${suffix}@jobready.dev`,
      username: `e2ecacheb${suffix}`,
      password: 'E2eStudent123!',
      fullName: 'Cache User B',
    }

    await registerUser(page, userA)
    await expect(page.getByRole('heading', { name: /welcome back/i })).toBeVisible({
      timeout: 20_000,
    })

    // Seed identifiable private progress for user A inside the same SPA session.
    await page.goto('/jobs/applications')
    await expect(page.getByRole('heading').first()).toBeVisible({ timeout: 15_000 })
    await page.evaluate((marker) => {
      // Force a distinctive cached React Query entry that would flash if not cleared.
      const cacheKey = JSON.stringify(['AUTH01_PRIVATE', marker])
      sessionStorage.setItem(cacheKey, marker)
      ;(window as unknown as { __AUTH01_MARKER__?: string }).__AUTH01_MARKER__ = marker
    }, markerA)

    // Hold dashboard queries so a stale cache would still be visible after switch.
    await page.route('**/api/v1/mistakes/summary**', async (route) => {
      await new Promise((r) => setTimeout(r, 800))
      await route.continue()
    })
    await page.goto('/mistakes')
    await expect(page.getByRole('heading', { name: /mistake/i })).toBeVisible({ timeout: 15_000 })
    await expect(page.getByText(markerA)).toHaveCount(0)

    // Same-document account switch (no full browser restart).
    await logout(page)
    await registerUser(page, userB)
    await expect(page.getByRole('heading', { name: /welcome back/i })).toBeVisible({
      timeout: 20_000,
    })

    // Immediate checks before delayed private responses settle.
    await expect(page.getByText(markerA)).toHaveCount(0)
    await expect(page.getByText(userA.fullName, { exact: false })).toHaveCount(0)
    await expect(page.getByText(userA.email, { exact: false })).toHaveCount(0)

    await page.goto('/mistakes')
    await expect(page.getByRole('heading', { name: /mistake/i })).toBeVisible({ timeout: 15_000 })
    await expect(page.getByText(markerA)).toHaveCount(0)
    await expect(page.getByText(userA.email, { exact: false })).toHaveCount(0)

    await page.goto('/jobs/applications')
    await expect(page.getByRole('heading').first()).toBeVisible({ timeout: 15_000 })
    await expect(page.getByText(markerA)).toHaveCount(0)
    await expect(page.getByText(userA.email, { exact: false })).toHaveCount(0)
  })

  test('register creates a student account', async ({ page }) => {
    const suffix = Date.now().toString(36).slice(-6)
    await registerUser(page, {
      email: `e2e.new.${suffix}@jobready.dev`,
      username: `e2enew${suffix}`,
      password: 'E2eStudent123!',
      fullName: 'E2E Fresh Student',
    })
    await expect(page.getByRole('heading', { name: /welcome back/i })).toBeVisible({
      timeout: 20_000,
    })
  })
})
