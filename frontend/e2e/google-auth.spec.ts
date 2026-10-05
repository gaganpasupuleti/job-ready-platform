import { expect, test } from '@playwright/test'

import { apiBaseUrl } from './helpers'

const CLIENT = 'e2e-google-client.apps.googleusercontent.com'

async function installGoogleStub(page: import('@playwright/test').Page) {
  await page.addInitScript((clientId) => {
    window.__JOBREADY_E2E_GOOGLE_CLIENT_ID = clientId
    window.google = {
      accounts: {
        id: {
          initialize(config: { callback: (response: { credential?: string }) => void }) {
            ;(window as unknown as { __googleCallback?: typeof config.callback }).__googleCallback = config.callback
          },
          renderButton(parent: HTMLElement) {
            const button = document.createElement('button')
            button.type = 'button'
            button.textContent = 'Continue with Google'
            button.onclick = () => {
              const callback = (window as unknown as { __googleCallback?: (response: { credential?: string }) => void })
                .__googleCallback
              callback?.({ credential: 'e2e.header.payload' })
            }
            parent.appendChild(button)
          },
        },
      },
    }
  }, CLIENT)
}

test('Google button stays hidden when it is not configured', async ({ page }) => {
  await page.goto('/login')
  await expect(page.getByRole('heading', { name: /sign in/i })).toBeVisible()
  await expect(page.getByRole('button', { name: /continue with google/i })).toHaveCount(0)
  await expect(page.getByLabel('Email')).toBeVisible()
  await page.goto('/register')
  await expect(page.getByRole('heading', { name: /create account/i })).toBeVisible()
  await expect(page.getByRole('button', { name: /continue with google/i })).toHaveCount(0)
  await expect(page.getByLabel('Password')).toBeVisible()
})

test('new Google student stores a session and opens job preferences', async ({ page, request }) => {
  const suffix = Date.now().toString(36)
  const email = `e2e.google.new.${suffix}@example.com`
  const created = await request.post(`${apiBaseUrl()}/auth/register`, {
    data: {
      email,
      username: `e2egoogle${suffix}`.slice(0, 24),
      full_name: 'E2E Google New',
      password: 'E2eStudent123!',
    },
  })
  expect(created.ok()).toBeTruthy()
  const auth = await created.json()

  await installGoogleStub(page)
  await page.route('**/api/v1/auth/google', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ ...auth, is_new_user: true }),
    })
  })
  await page.goto('/login')
  await page.getByRole('button', { name: /continue with google/i }).click()
  await expect(page).toHaveURL(/\/jobs\/preferences/, { timeout: 20_000 })
  await expect(page.getByRole('heading', { name: /job preferences/i })).toBeVisible()
  const token = await page.evaluate(() => localStorage.getItem('jrp_access_token'))
  expect(token).toBe(auth.access_token)
})

test('existing Google student follows the from destination', async ({ page, request }) => {
  const suffix = Date.now().toString(36)
  const email = `e2e.google.old.${suffix}@example.com`
  const created = await request.post(`${apiBaseUrl()}/auth/register`, {
    data: {
      email,
      username: `e2egoogleold${suffix}`.slice(0, 24),
      password: 'E2eStudent123!',
    },
  })
  expect(created.ok()).toBeTruthy()
  const auth = await created.json()

  await installGoogleStub(page)
  await page.route('**/api/v1/auth/google', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ ...auth, is_new_user: false }),
    })
  })
  await page.goto('/login?from=/practice')
  await page.getByRole('button', { name: /continue with google/i }).click()
  await expect(page).toHaveURL(/\/practice/, { timeout: 20_000 })
  await expect(page.getByRole('heading', { name: /practice hub/i })).toBeVisible()
})

test('failed Google sign-in shows an error and stays on login', async ({ page }) => {
  await installGoogleStub(page)
  await page.route('**/api/v1/auth/google', async (route) => {
    await route.fulfill({
      status: 401,
      contentType: 'application/json',
      body: JSON.stringify({ detail: 'Google sign-in failed' }),
    })
  })
  await page.goto('/login')
  await page.getByRole('button', { name: /continue with google/i }).click()
  await expect(page.getByText('Google sign-in failed')).toBeVisible()
  await expect(page).toHaveURL(/\/login/)
  await expect(page.getByLabel('Email')).toBeVisible()
})
