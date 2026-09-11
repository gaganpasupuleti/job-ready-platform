import { expect, test } from '@playwright/test'

import { loadManifest, loginAs } from './helpers'

const fixtures = loadManifest()

test.describe('Jobs portal', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, fixtures.users.student)
  })

  test('browse search and open job detail', async ({ page }) => {
    await page.goto('/jobs')
    await expect(page.getByRole('heading', { name: /^jobs$/i })).toBeVisible({ timeout: 20_000 })
    await page.getByPlaceholder('Keywords').fill('Data Engineer')
    await page.getByRole('button', { name: /^search$/i }).click()
    const jobLink = page.getByRole('link', { name: /data engineer/i }).first()
    await expect(jobLink).toBeVisible({ timeout: 15_000 })
    await jobLink.click()
    await expect(page).toHaveURL(/\/jobs\//)
    await expect(page.getByText(/description/i).first()).toBeVisible()
  })

  test('save unsave and saved page', async ({ page }) => {
    await page.goto('/jobs/data-engineer-remote-infosys')
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 20_000 })
    const saveBtn = page.getByRole('button', { name: /save job|^saved$/i })
    await expect(saveBtn).toBeVisible({ timeout: 15_000 })
    if (/save job/i.test((await saveBtn.textContent()) || '')) {
      await saveBtn.click()
      await expect(page.getByRole('button', { name: /^saved$/i })).toBeVisible()
    }
    await page.goto('/jobs/saved')
    await expect(page.getByRole('heading', { name: /saved jobs/i })).toBeVisible()
    await expect(page.getByText(/data engineer/i).first()).toBeVisible({ timeout: 15_000 })
  })

  test('mark applied and application detail', async ({ page, request }) => {
    const token = await page.evaluate(() => localStorage.getItem('jrp_access_token'))
    expect(token).toBeTruthy()
    const api = process.env.E2E_API_URL || 'http://127.0.0.1:8000/api/v1'
    const headers = { Authorization: `Bearer ${token}` }

    const listed = await request.get(`${api}/jobs?limit=50`, { headers })
    expect(listed.ok()).toBeTruthy()
    const listJson = await listed.json()
    const candidates = (listJson.items as { id: string; slug: string; title: string }[]).filter(
      (item) =>
        item.slug &&
        !item.slug.startsWith('admin-manual') &&
        !item.slug.includes('python-developer-sync'),
    )

    let target: {
      id: string
      slug: string
      title: string
      application_status: string | null
    } | null = null
    for (const item of candidates) {
      const detailRes = await request.get(`${api}/jobs/${item.id}`, { headers })
      expect(detailRes.ok()).toBeTruthy()
      const detail = await detailRes.json()
      const status = detail.application_status as string | null
      if (!status || status === 'preparing' || status === 'saved') {
        target = {
          id: detail.id,
          slug: detail.slug,
          title: detail.title,
          application_status: status,
        }
        break
      }
    }
    expect(target, 'need at least one seeded job without an applied+ application').toBeTruthy()

    await page.goto(`/jobs/${target!.slug}`)
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 20_000 })
    const applyBtn = page.getByRole('button', { name: /mark applied/i })
    await expect(applyBtn).toBeVisible({ timeout: 15_000 })
    await applyBtn.click()
    await expect(page).toHaveURL(/\/jobs\/applications\/[^/]+/, { timeout: 15_000 })

    // Persisted status on application detail
    await expect(page.getByText(/^applied$/i).first()).toBeVisible({ timeout: 15_000 })

    // Applications list includes this role
    await page.goto('/jobs/applications')
    await expect(page.getByRole('heading', { name: /applications/i }).first()).toBeVisible({
      timeout: 15_000,
    })
    const titleMatcher = new RegExp(target!.title.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i')
    await expect(page.getByText(titleMatcher).first()).toBeVisible({ timeout: 15_000 })

    // Refresh job detail: applied badge + View application (Mark applied hidden)
    await page.goto(`/jobs/${target!.slug}`)
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 20_000 })
    await expect(page.getByText(/^applied$/i).first()).toBeVisible()
    await expect(page.getByRole('link', { name: /view application/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /mark applied/i })).toHaveCount(0)

    // Hard refresh still persists
    await page.reload()
    await expect(page.getByText(/^applied$/i).first()).toBeVisible({ timeout: 15_000 })
    await expect(page.getByRole('link', { name: /view application/i })).toBeVisible()
  })

  test('recommended page without match score', async ({ page }) => {
    await page.goto('/jobs/recommended')
    await expect(page.getByRole('heading', { name: /relevant jobs/i })).toBeVisible({
      timeout: 20_000,
    })
    await expect(page.getByText(/\d+%\s*match/i)).toHaveCount(0)
    await expect(page.getByText(/best match/i)).toHaveCount(0)
  })

  test('student blocked from admin jobs', async ({ page }) => {
    await page.goto('/admin/jobs')
    await expect(page).toHaveURL(/\/($|\?)/)
  })
})
