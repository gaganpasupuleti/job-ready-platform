import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { expect, type Page } from '@playwright/test'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

export type E2EManifest = {
  users: {
    student: { email: string; password: string; username: string }
    admin: { email: string; password: string }
  }
  sql: {
    slug: string
    accepted_query: string
    wrong_query: string
    invalid_query: string
    blocked_query: string
  }
  coding: { id: string | null; slug: string | null; title: string | null }
  path: { slug: string }
  project: { slug: string }
  sql_project: { slug: string }
  course: { slug: string }
  prompt: { slug: string | null }
  scenario: { slug: string | null; domain_key: string | null }
  mcq_topic: { slug: string; name: string }
}

const fallbackManifest: E2EManifest = {
  users: {
    student: {
      email: 'e2e.student@jobready.dev',
      password: 'E2eStudent123!',
      username: 'e2e_student',
    },
    admin: { email: 'admin@jobready.dev', password: 'Admin123!' },
  },
  sql: {
    slug: 'active-catalog-items',
    accepted_query:
      'SELECT product_name, price\nFROM products\nWHERE is_active = TRUE\nORDER BY price DESC',
    wrong_query: 'SELECT product_name FROM products LIMIT 1',
    invalid_query: 'SELECT product_name FROM products WHERE',
    blocked_query: 'DELETE FROM products',
  },
  coding: { id: null, slug: null, title: null },
  path: { slug: 'beginner-arrays' },
  project: { slug: 'python-calculator' },
  sql_project: { slug: 'sql-ecommerce-analytics' },
  course: { slug: 'python-foundations' },
  prompt: { slug: null },
  scenario: { slug: null, domain_key: null },
  mcq_topic: { slug: 'percentages', name: 'Percentages' },
}

export function loadManifest(): E2EManifest {
  const candidates = [
    process.env.E2E_MANIFEST_PATH,
    path.join(__dirname, 'fixtures', 'manifest.json'),
    path.join(__dirname, '..', '..', 'backend', 'e2e-manifest.json'),
  ].filter(Boolean) as string[]
  for (const candidate of candidates) {
    if (fs.existsSync(candidate)) {
      return { ...fallbackManifest, ...JSON.parse(fs.readFileSync(candidate, 'utf8')) }
    }
  }
  return fallbackManifest
}

export async function loginAs(
  page: Page,
  user: { email: string; password: string },
) {
  await page.goto('/login')
  await page.getByLabel('Email').fill(user.email)
  await page.getByLabel('Password').fill(user.password)
  await page.getByRole('button', { name: /sign in/i }).click()
  await expect(page).not.toHaveURL(/\/login/)
}

export async function registerUser(
  page: Page,
  user: { email: string; username: string; password: string; fullName?: string },
) {
  await page.goto('/register')
  await page.getByLabel('Full name').fill(user.fullName ?? 'E2E New Student')
  await page.getByLabel('Email').fill(user.email)
  await page.getByLabel('Username').fill(user.username)
  await page.getByLabel('Password').fill(user.password)
  await page.getByRole('button', { name: /register/i }).click()
  await expect(page).not.toHaveURL(/\/register/)
}

export async function logout(page: Page) {
  const logoutBtn = page.getByRole('button', { name: /logout/i })
  await expect(logoutBtn, 'Logout control must be present for real sign-out').toBeVisible({
    timeout: 8_000,
  })
  await logoutBtn.click()
  await page.waitForURL(/\/login/, { timeout: 15_000 })
}

export async function registerUserInApp(
  page: Page,
  user: { email: string; username: string; password: string; fullName?: string },
) {
  // Client-side navigation only — no page.goto / reload.
  const registerLink = page.getByRole('link', { name: /register|create account|sign up/i }).first()
  if (await registerLink.count()) {
    await registerLink.click()
  } else {
    await page.getByRole('button', { name: /register|sign up/i }).first().click()
  }
  await expect(page).toHaveURL(/\/register/)
  await page.getByLabel('Full name').fill(user.fullName ?? 'E2E New Student')
  await page.getByLabel('Email').fill(user.email)
  await page.getByLabel('Username').fill(user.username)
  await page.getByLabel('Password').fill(user.password)
  await page.getByRole('button', { name: /register/i }).click()
  await expect(page).not.toHaveURL(/\/register/)
}

/** Create a distinctive private application note for the current session via API. */
export async function seedPrivateApplicationNote(page: Page, marker: string) {
  const result = await page.evaluate(async (noteMarker) => {
    const token = localStorage.getItem('jrp_access_token')
    if (!token) throw new Error('missing auth token')
    const headers = {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    }
    const jobsRes = await fetch('/api/v1/jobs?limit=1', { headers })
    if (!jobsRes.ok) throw new Error(`jobs list failed: ${jobsRes.status}`)
    const jobsBody = await jobsRes.json()
    const jobId = jobsBody.items?.[0]?.id
    if (!jobId) throw new Error('no jobs available to seed private note')

    const applyRes = await fetch(`/api/v1/jobs/${jobId}/apply`, {
      method: 'POST',
      headers,
      body: JSON.stringify({}),
    })
    let applicationId: string | null = null
    if (applyRes.ok) {
      const applied = await applyRes.json()
      applicationId = applied.id ?? null
    } else {
      const appsRes = await fetch('/api/v1/applications', { headers })
      if (!appsRes.ok) throw new Error(`applications list failed: ${appsRes.status}`)
      const apps = await appsRes.json()
      const list = Array.isArray(apps) ? apps : []
      applicationId = list[0]?.id ?? null
    }
    if (!applicationId) throw new Error('could not resolve application id')

    const patchRes = await fetch(`/api/v1/applications/${applicationId}`, {
      method: 'PATCH',
      headers,
      body: JSON.stringify({ notes: noteMarker }),
    })
    if (!patchRes.ok) throw new Error(`note update failed: ${patchRes.status}`)
    return { applicationId, jobId }
  }, marker)
  return result
}

/** Sign in via client-side navigation from the login screen (no page.goto). */
export async function loginInApp(
  page: Page,
  user: { email: string; password: string },
) {
  await expect(page).toHaveURL(/\/login/)
  await page.getByLabel('Email').fill(user.email)
  await page.getByLabel('Password').fill(user.password)
  await page.getByRole('button', { name: /sign in/i }).click()
  await expect(page).not.toHaveURL(/\/login/)
}

export function attachConsoleGuard(page: Page) {
  const errors: string[] = []
  page.on('pageerror', (err) => errors.push(`pageerror: ${err.message}`))
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      const text = msg.text()
      // Allow expected auth/network noise in some flows
      if (/favicon|Failed to load resource|net::ERR_/i.test(text)) return
      errors.push(`console.error: ${text}`)
    }
  })
  return {
    assertClean: (allowed: RegExp[] = []) => {
      const unexpected = errors.filter((e) => !allowed.some((re) => re.test(e)))
      expect(unexpected, unexpected.join('\n')).toEqual([])
    },
    errors,
  }
}

export async function fillMonaco(page: Page, text: string) {
  const codeTab = page.getByRole('button', { name: /^code$/i })
  if (await codeTab.count()) {
    await codeTab.click()
  }
  const editor = page.locator('.monaco-editor:visible').first()
  await expect(editor).toBeVisible({ timeout: 30_000 })
  await editor.click()

  // Prefer editor instance exposed by SqlEditor onMount (updates React controlled state).
  const setViaApi = await page.evaluate((value) => {
    const w = window as unknown as {
      __jobReadyMonaco?: { setValue: (v: string) => void; getValue: () => string }
      monaco?: { editor?: { getEditors?: () => Array<{ setValue: (v: string) => void; getValue: () => string }> } }
    }
    const ed = w.__jobReadyMonaco ?? w.monaco?.editor?.getEditors?.()?.[0]
    if (!ed) return false
    ed.setValue(value)
    return ed.getValue() === value
  }, text)

  if (!setViaApi) {
    const modifier = process.platform === 'darwin' ? 'Meta' : 'Control'
    await page.keyboard.press(`${modifier}+A`)
    await page.keyboard.insertText(text)
  }

  const probe = text.trim().split(/\r?\n/).find((line) => line.trim().length > 0) ?? text
  await expect(page.getByText(probe.slice(0, Math.min(probe.length, 32))).first()).toBeVisible({
    timeout: 5_000,
  })
}

export async function fillPromptEditor(page: Page, text: string) {
  const area = page.getByRole('textbox').first()
  await expect(area).toBeVisible({ timeout: 20_000 })
  await area.fill(text)
}
