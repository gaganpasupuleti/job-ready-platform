import { expect, request as playwrightRequest, test } from '@playwright/test'

import {
  archiveAdminJobs,
  createIsolatedE2EJob,
  loadManifest,
  loginAs,
} from './helpers'

const fixtures = loadManifest()
const createdJobIds: string[] = []

test.describe('Jobs portal', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, fixtures.users.student)
  })

  test.afterAll(async () => {
    const ctx = await playwrightRequest.newContext()
    try {
      await archiveAdminJobs(ctx, [...createdJobIds])
      createdJobIds.length = 0
    } finally {
      await ctx.dispose()
    }
  })

  test('browse search and open job detail', async ({ page }) => {
    await page.goto('/jobs')
    await expect(page.getByRole('heading', { name: /^jobs$/i })).toBeVisible({ timeout: 20_000 })
    await expect(page.getByText(/\d+ jobs? found/i)).toBeVisible({ timeout: 20_000 })
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
    const target = await createIsolatedE2EJob(request)
    createdJobIds.push(target.id)

    try {
      await page.goto(`/jobs/${target.slug}`)
      await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 20_000 })
      const applyBtn = page.getByRole('button', { name: /mark applied/i })
      await expect(applyBtn).toBeVisible({ timeout: 15_000 })
      await applyBtn.click()
      await expect(page).toHaveURL(/\/jobs\/applications\/[^/]+/, { timeout: 15_000 })

      await expect(page.getByText(/^applied$/i).first()).toBeVisible({ timeout: 15_000 })

      await page.goto('/jobs/applications')
      await expect(page.getByRole('heading', { name: /applications/i }).first()).toBeVisible({
        timeout: 15_000,
      })
      const titleMatcher = new RegExp(target.title.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i')
      await expect(page.getByText(titleMatcher).first()).toBeVisible({ timeout: 15_000 })

      await page.goto(`/jobs/${target.slug}`)
      await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 20_000 })
      await expect(page.getByText(/^applied$/i).first()).toBeVisible()
      await expect(page.getByRole('link', { name: /view application/i })).toBeVisible()
      await expect(page.getByRole('button', { name: /mark applied/i })).toHaveCount(0)

      await page.reload()
      await expect(page.getByText(/^applied$/i).first()).toBeVisible({ timeout: 15_000 })
      await expect(page.getByRole('link', { name: /view application/i })).toBeVisible()
    } finally {
      // Per-test teardown so a failed assert still archives only this run's job.
      await archiveAdminJobs(request, [target.id])
      const idx = createdJobIds.indexOf(target.id)
      if (idx >= 0) createdJobIds.splice(idx, 1)
    }
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

test.describe('Jobs-first student journey', () => {
  test('signup preferences browse save external apply then mark applied', async ({ page }) => {
    const suffix = Date.now().toString(36).slice(-6)
    await page.goto('/register')
    await page.getByLabel('Full name').fill(`Pilot ${suffix}`)
    await page.getByLabel('Email').fill(`e2e.jobs.${suffix}@jobready.dev`)
    await page.getByLabel('Username').fill(`e2ejobs${suffix}`)
    await page.getByLabel('Password').fill('E2eStudent123!')
    await page.getByRole('button', { name: /register/i }).click()
    await expect(page.getByRole('heading', { name: /job preferences/i })).toBeVisible({
      timeout: 20_000,
    })
    await page.getByLabel('Role').selectOption({ label: 'Data Engineer' })
    await page.getByLabel('Preferred locations').fill('Hyderabad')
    await page.getByRole('button', { name: /save and browse jobs/i }).click()
    await expect(page).toHaveURL(/\/jobs$/)
    await expect(page.getByRole('heading', { name: /^jobs$/i })).toBeVisible()

    await page.getByPlaceholder('Keywords').fill('Data Engineer')
    await page.getByRole('button', { name: /^search$/i }).click()
    const jobLink = page.getByRole('link', { name: /data engineer/i }).first()
    await expect(jobLink).toBeVisible({ timeout: 15_000 })
    await jobLink.click()
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible()

    const saveBtn = page.getByRole('button', { name: /save job/i })
    await saveBtn.click()
    await expect(page.getByRole('button', { name: /^saved$/i })).toBeVisible()

    const applyLink = page.getByRole('link', { name: /apply externally/i })
    if (await applyLink.count()) {
      const applyPosts: string[] = []
      page.on('request', (request) => {
        if (request.method() === 'POST' && /\/jobs\/[^/]+\/apply/.test(request.url())) {
          applyPosts.push(request.url())
        }
      })
      await applyLink.evaluate((node) => {
        node.setAttribute('target', '_self')
        node.addEventListener('click', (event) => event.preventDefault())
      })
      await applyLink.click()
      await expect(page.getByRole('button', { name: /mark applied/i })).toBeVisible()
      expect(applyPosts).toEqual([])
    }

    await page.getByRole('button', { name: /mark applied/i }).click()
    await expect(page).toHaveURL(/\/jobs\/applications\/[^/]+/, { timeout: 15_000 })
    await expect(page.getByText(/^applied$/i).first()).toBeVisible()
  })

  test('jobs controls stay reachable on a phone viewport', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    await loginAs(page, fixtures.users.student)
    await page.goto('/jobs')
    await expect(page.getByRole('heading', { name: /^jobs$/i })).toBeVisible({ timeout: 20_000 })
    await page.getByRole('button', { name: /open navigation/i }).click()
    await expect(page.getByRole('navigation', { name: /main navigation/i }).getByRole('link', { name: /^jobs$/i })).toBeVisible()
    await page.goto('/jobs/data-engineer-remote-infosys')
    await expect(page.getByRole('button', { name: /save job|^saved$/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /mark applied|view application/i })).toBeVisible()
  })
})
