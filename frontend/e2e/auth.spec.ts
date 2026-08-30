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
