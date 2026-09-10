import { expect, test } from '@playwright/test'

import {
  attachConsoleGuard,
  loadManifest,
  loginAs,
  logout,
  registerUser,
  registerUserInApp,
  seedPrivateApplicationNote,
} from './helpers'

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

  test('failed logout still clears local session', async ({ page }) => {
    await loginAs(page, fixtures.users.student)
    await page.route('**/api/v1/auth/logout**', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: '{"detail":"logout failed"}',
      })
    })
    await logout(page)
    await page.goto('/practice')
    await expect(page).toHaveURL(/\/login/)
  })

  test('stale 401 clears private cache and redirects to login', async ({ page }) => {
    await loginAs(page, fixtures.users.student)
    await page.goto('/mistakes')
    await expect(page.getByRole('heading', { name: /mistake/i })).toBeVisible({ timeout: 15_000 })
    await page.route('**/api/v1/**', async (route) => {
      if (/\/auth\/(login|register)\b/.test(route.request().url())) {
        await route.continue()
        return
      }
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: '{"detail":"expired"}',
      })
    })
    await page.goto('/jobs/applications')
    await expect(page).toHaveURL(/\/login/, { timeout: 15_000 })
  })

  test('cross-tab token clear signs out this tab', async ({ page }) => {
    await loginAs(page, fixtures.users.student)
    await expect(page.getByRole('heading', { name: /welcome back/i })).toBeVisible()
    await page.evaluate(() => {
      const key = 'jrp_access_token'
      const oldValue = localStorage.getItem(key)
      localStorage.removeItem(key)
      window.dispatchEvent(
        new StorageEvent('storage', {
          key,
          oldValue,
          newValue: null,
          storageArea: localStorage,
        }),
      )
    })
    await page.goto('/practice')
    await expect(page).toHaveURL(/\/login/, { timeout: 15_000 })
  })

  test('AUTH-01 account switch does not leak prior private records', async ({ page }) => {
    const suffix = Date.now().toString(36).slice(-6)
    const markerA = `PRIVATE_MARKER_A_${suffix}`
    const userA = {
      email: `e2e.cache.a.${suffix}@jobready.dev`,
      username: `e2ecachea${suffix}`,
      password: 'E2eStudent123!',
      fullName: `Cache User A ${suffix}`,
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

    const seeded = await seedPrivateApplicationNote(page, markerA)
    expect(seeded.applicationId).toBeTruthy()

    // Render + cache A's private note through the real UI (SPA navigation).
    await page.getByRole('link', { name: /^jobs$/i }).click()
    await expect(page).toHaveURL(/\/jobs/)
    await page.getByRole('link', { name: /applications/i }).first().click()
    await expect(page).toHaveURL(/\/jobs\/applications/)
    await page.locator(`a[href="/jobs/applications/${seeded.applicationId}"]`).click()
    await expect(page).toHaveURL(new RegExp(`/jobs/applications/${seeded.applicationId}`))
    await expect(page.getByLabel(/^notes$/i)).toHaveValue(markerA, { timeout: 15_000 })

    const tokenA = await page.evaluate(() => localStorage.getItem('jrp_access_token'))
    expect(tokenA).toBeTruthy()

    type DelayedMode = 'success' | 'unauthorized'
    const queue: DelayedMode[] = []
    const waiters: Array<(mode: DelayedMode) => void> = []
    const takeDelayedA = () =>
      new Promise<DelayedMode>((resolve) => {
        const next = queue.shift()
        if (next) resolve(next)
        else waiters.push(resolve)
      })
    const releaseDelayedA = (mode: DelayedMode) => {
      const waiter = waiters.shift()
      if (waiter) waiter(mode)
      else queue.push(mode)
    }

    let delayedSuccessHandled = false
    let delayed401Handled = false
    let applicationsProbeParked = false
    let summaryProbeParked = false

    await page.route('**/api/v1/applications**', async (route) => {
      const url = route.request().url()
      const authHeader = route.request().headers()['authorization'] ?? ''
      const isProbe =
        authHeader === `Bearer ${tokenA}` && /[?&]auth01_probe=1(?:&|$)/.test(url)
      // Only hold the detached A probe — let normal UI traffic continue.
      if (isProbe) {
        applicationsProbeParked = true
        const mode = await takeDelayedA()
        delayedSuccessHandled = true
        if (mode === 'unauthorized') {
          await route.fulfill({
            status: 401,
            contentType: 'application/json',
            body: '{"detail":"expired"}',
          })
          return
        }
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            {
              id: seeded.applicationId,
              job_id: seeded.jobId,
              job_title: 'AUTH01 Private Job',
              company_name: 'AUTH01 Co',
              status: 'applied',
              priority: 'medium',
              job_status: 'active',
            },
          ]),
        })
        return
      }
      if (authHeader !== `Bearer ${tokenA}`) {
        // Delay B private responses so a leaked A cache would still be visible.
        await new Promise((r) => setTimeout(r, 1000))
      }
      await route.continue()
    })

    await page.route('**/api/v1/mistakes/summary**', async (route) => {
      const url = route.request().url()
      const authHeader = route.request().headers()['authorization'] ?? ''
      const isProbe =
        authHeader === `Bearer ${tokenA}` && /[?&]auth01_probe=1(?:&|$)/.test(url)
      if (isProbe) {
        summaryProbeParked = true
        const mode = await takeDelayedA()
        if (mode === 'unauthorized') {
          delayed401Handled = true
          await route.fulfill({
            status: 401,
            contentType: 'application/json',
            body: '{"detail":"expired"}',
          })
          return
        }
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            open_count: 99,
            repeated_count: 0,
            resolved_count: 0,
            top_weak_topics: [{ title: markerA, count: 99 }],
          }),
        })
        return
      }
      if (authHeader !== `Bearer ${tokenA}`) {
        await new Promise((r) => setTimeout(r, 1000))
      }
      await route.continue()
    })

    // Detached axios probes survive logout's queryClient.clear(); Authorization is A.
    await page.evaluate(() => {
      const w = window as unknown as {
        __jobReadyApiClient?: {
          get: (url: string, cfg?: object) => Promise<unknown>
        }
        __auth01Probes?: Promise<unknown>[]
      }
      const client = w.__jobReadyApiClient
      if (!client) throw new Error('missing __jobReadyApiClient for AUTH-01 probes')
      w.__auth01Probes = [
        client.get('/api/v1/applications', { params: { auth01_probe: '1' } }),
        client.get('/api/v1/mistakes/summary', { params: { auth01_probe: '1' } }),
      ]
    })
    await expect.poll(() => applicationsProbeParked && summaryProbeParked).toBe(true)

    // Same-document switch: logout → register B (no page.goto / reload / new context).
    await logout(page)
    await registerUserInApp(page, userB)
    await expect(page.getByRole('heading', { name: /welcome back/i })).toBeVisible({
      timeout: 20_000,
    })

    const tokenB = await page.evaluate(() => localStorage.getItem('jrp_access_token'))
    expect(tokenB).toBeTruthy()
    expect(tokenB).not.toEqual(tokenA)

    // Immediate checks while B private responses are still delayed.
    await expect(page.getByText(markerA)).toHaveCount(0)
    await expect(page.getByText(userA.email, { exact: false })).toHaveCount(0)

    await page.getByRole('link', { name: /^jobs$/i }).click()
    await page.getByRole('link', { name: /applications/i }).first().click()
    await expect(page).toHaveURL(/\/jobs\/applications/)
    await expect(page.getByText(markerA)).toHaveCount(0)
    await expect(page.getByText('AUTH01 Private Job')).toHaveCount(0)

    // Delayed A success after B must not leak into the UI.
    releaseDelayedA('success')
    await expect.poll(() => delayedSuccessHandled).toBe(true)
    await expect(page.getByText(markerA)).toHaveCount(0)
    await expect(page.getByText('AUTH01 Private Job')).toHaveCount(0)

    // Old A 401 after B authenticates must not clear B's token or cache.
    releaseDelayedA('unauthorized')
    await expect.poll(() => delayed401Handled).toBe(true)
    await expect
      .poll(async () => page.evaluate(() => localStorage.getItem('jrp_access_token')))
      .toBe(tokenB)
    await expect(page).not.toHaveURL(/\/login/)
    await expect(page.getByText(markerA)).toHaveCount(0)
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
