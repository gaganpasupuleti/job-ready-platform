import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { expect, type APIRequestContext, type Page } from '@playwright/test'

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
  coding: {
    id: string | null
    slug: string | null
    title: string | null
    domain_id?: string | null
    category_id?: string | null
    topic_id?: string | null
  }
  path: { slug: string }
  project: { slug: string }
  sql_project: { slug: string }
  course: { slug: string }
  prompt: { slug: string | null }
  scenario: { slug: string | null; domain_key: string | null }
  mcq_topic: { slug: string; name: string }
}

export type CodingFixture = { id: string; slug: string; title: string }

export function apiBaseUrl(): string {
  const raw = (process.env.E2E_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')
  return raw.endsWith('/api/v1') ? raw : `${raw}/api/v1`
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
  // Prefer env / local BE seed overlays; committed seed-manifest keeps coding id
  // available on FE-only checkouts (fixtures/manifest.json remains gitignored).
  const candidates = [
    process.env.E2E_MANIFEST_PATH,
    path.join(__dirname, 'fixtures', 'manifest.json'),
    path.join(__dirname, '..', '..', 'backend', 'e2e-manifest.json'),
    path.join(__dirname, 'fixtures', 'seed-manifest.json'),
  ].filter(Boolean) as string[]
  for (const candidate of candidates) {
    if (fs.existsSync(candidate)) {
      return { ...fallbackManifest, ...JSON.parse(fs.readFileSync(candidate, 'utf8')) }
    }
  }
  return fallbackManifest
}

async function loginAccessToken(
  request: APIRequestContext,
  user: { email: string; password: string },
): Promise<string> {
  const res = await request.post(`${apiBaseUrl()}/auth/login`, {
    data: { email: user.email, password: user.password },
  })
  if (!res.ok()) {
    throw new Error(`Acceptance auth failed for ${user.email}: HTTP ${res.status()}`)
  }
  const body = await res.json()
  if (!body?.access_token) {
    throw new Error(`Acceptance auth failed for ${user.email}: missing access_token`)
  }
  return body.access_token as string
}

/**
 * Resolve a live coding problem against the API. Seed IDs are hints only —
 * verify id/slug on the running DB, create a deterministic echo-input fixture
 * when missing, and fail clearly when the acceptance fixture cannot be ensured.
 */
export async function ensureCodingFixture(
  request: APIRequestContext,
  preferred: E2EManifest['coding'] = loadManifest().coding,
): Promise<CodingFixture> {
  const api = apiBaseUrl()
  const studentToken = await loginAccessToken(request, loadManifest().users.student)
  const studentHeaders = { Authorization: `Bearer ${studentToken}` }

  const asFixture = (row: { id: string; slug: string; title: string }): CodingFixture => ({
    id: row.id,
    slug: row.slug,
    title: row.title,
  })

  if (preferred?.id) {
    const byId = await request.get(`${api}/coding/problems/${preferred.id}`, {
      headers: studentHeaders,
    })
    if (byId.ok()) {
      const body = await byId.json()
      return asFixture(body)
    }
  }

  const slug = preferred?.slug || 'echo-input'
  const search = await request.get(`${api}/coding/problems`, {
    headers: studentHeaders,
    params: { search: slug, limit: 50 },
  })
  if (search.ok()) {
    const body = await search.json()
    const match = (body.items ?? []).find(
      (item: { slug?: string }) => item.slug === slug,
    )
    if (match) return asFixture(match)
  }

  const adminToken = await loginAccessToken(request, loadManifest().users.admin)
  const adminHeaders = {
    Authorization: `Bearer ${adminToken}`,
    'Content-Type': 'application/json',
  }

  let domainId = preferred?.domain_id ?? null
  let categoryId = preferred?.category_id ?? null
  let topicId = preferred?.topic_id ?? null
  if (!domainId || !categoryId || !topicId) {
    const adminList = await request.get(`${api}/admin/coding/problems`, {
      headers: adminHeaders,
      params: { limit: 1 },
    })
    if (adminList.ok()) {
      const listed = await adminList.json()
      const sample = listed.items?.[0]
      if (sample) {
        const detail = await request.get(`${api}/admin/coding/problems/${sample.id}`, {
          headers: adminHeaders,
        })
        if (detail.ok()) {
          const d = await detail.json()
          domainId = domainId || d.domain_id
          categoryId = categoryId || d.category_id
          topicId = topicId || d.topic_id
        }
      }
    }
  }

  if (!domainId || !categoryId || !topicId) {
    throw new Error(
      `Acceptance fixture missing: coding problem id=${preferred?.id ?? 'null'} slug=${slug}. ` +
        `Not present in ${api} and taxonomy is unavailable to create one.`,
    )
  }

  const created = await request.post(`${api}/admin/coding/problems`, {
    headers: adminHeaders,
    data: {
      slug,
      title: preferred?.title || 'Echo Input',
      description:
        'Read one line from standard input and print it exactly as received.',
      difficulty: 'easy',
      domain_id: domainId,
      category_id: categoryId,
      topic_id: topicId,
      constraints: 'Line length at most 1000 characters.',
      input_format: 'A single line of text.',
      output_format: 'The same line.',
      tags: ['io', 'strings', 'e2e-fixture'],
      supported_language_ids: [71, 62, 54, 63],
      starter_code: {
        '71': 'import sys\nprint(sys.stdin.read().strip())\n',
      },
      is_active: true,
      is_sample: true,
      test_cases: [
        {
          name: 'Sample 1',
          input: 'hello',
          expected_output: 'hello',
          is_sample: true,
          is_hidden: false,
        },
      ],
    },
  })
  if (!created.ok()) {
    throw new Error(
      `Acceptance fixture missing: coding problem slug=${slug} could not be created ` +
        `(HTTP ${created.status()}): ${await created.text()}`,
    )
  }
  const body = await created.json()
  return asFixture(body)
}

export async function archiveAdminJobs(
  request: APIRequestContext,
  jobIds: string[],
): Promise<void> {
  if (!jobIds.length) return
  const api = apiBaseUrl()
  const token = await loginAccessToken(request, loadManifest().users.admin)
  const headers = { Authorization: `Bearer ${token}` }
  for (const jobId of jobIds) {
    const res = await request.post(`${api}/admin/jobs/${jobId}/archive`, { headers })
    if (!res.ok() && res.status() !== 404) {
      throw new Error(`Failed to archive e2e job ${jobId}: HTTP ${res.status()}`)
    }
  }
}

export async function createIsolatedE2EJob(
  request: APIRequestContext,
): Promise<{ id: string; slug: string; title: string }> {
  const api = apiBaseUrl()
  const token = await loginAccessToken(request, loadManifest().users.admin)
  const suffix = `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`
  const created = await request.post(`${api}/admin/jobs`, {
    headers: { Authorization: `Bearer ${token}` },
    data: {
      title: `E2E Apply Target ${suffix}`,
      company_name: 'E2E Fixture Co',
      description:
        'Isolated listing created for mark-applied Playwright coverage. Not a production vacancy.',
      location_text: 'Remote',
      work_mode: 'remote',
      is_remote: true,
      status: 'active',
      skills: ['Python'],
    },
  })
  if (!created.ok()) {
    throw new Error(`Failed to create isolated e2e job: HTTP ${created.status()} ${await created.text()}`)
  }
  return created.json()
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
  const logoutBtn = page.getByRole('button', { name: /^logout$/i })
  if (!(await logoutBtn.isVisible().catch(() => false))) {
    const profileLogout = page.getByRole('button', { name: /log out/i })
    await expect(profileLogout, 'Logout control must be present for real sign-out').toBeVisible({
      timeout: 8_000,
    })
    await profileLogout.click()
    await page.waitForURL(/\/login/, { timeout: 15_000 })
    return
  }
  await expect(logoutBtn, 'Logout control must be present for real sign-out').toBeVisible({
    timeout: 8_000,
  })
  await logoutBtn.click()
  await page.waitForURL(/\/login/, { timeout: 15_000 })
}

export async function openPrimaryNav(page: Page) {
  const jobs = page.getByRole('navigation', { name: /main navigation/i }).getByRole('link', { name: /^jobs$/i })
  if (await jobs.isVisible().catch(() => false)) return
  const menu = page.getByRole('button', { name: /open navigation/i })
  if (await menu.isVisible().catch(() => false)) await menu.click()
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
