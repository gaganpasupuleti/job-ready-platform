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

  test('mark applied and application detail', async ({ page }) => {
    await page.goto('/jobs/devops-engineer-cognizant')
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 20_000 })
    const applyBtn = page.getByRole('button', { name: /mark applied/i })
    await expect(applyBtn).toBeVisible({ timeout: 15_000 })
    await applyBtn.click()
    await expect(page).toHaveURL(/\/jobs\/applications\//, { timeout: 15_000 })
    await page.goto('/jobs/applications')
    await expect(page.getByRole('heading', { name: /applications/i }).first()).toBeVisible({
      timeout: 15_000,
    })
    await expect(
      page.getByText(/python developer|data analyst|devops engineer/i).first(),
    ).toBeVisible({ timeout: 15_000 })
  })

  test('recommended page without match score', async ({ page }) => {
    await page.goto('/jobs/recommended')
    await expect(page.getByRole('heading', { name: /relevant jobs/i })).toBeVisible({
      timeout: 20_000,
    })
    await expect(page.getByText(/\d+%\s*match/i)).toHaveCount(0)
    await expect(page.getByText(/best match/i)).toHaveCount(0)
  })

  test('sample demos filter and badge', async ({ page }) => {
    await page.goto('/jobs?include_sample=1')
    await expect(page.getByRole('heading', { name: /^jobs$/i })).toBeVisible({ timeout: 20_000 })
    await expect(page.getByLabel(/show sample demos/i)).toBeChecked()
    const sampleSignal = page.getByText(/^sample$/i).or(page.getByText(/SAMPLE DEMO/i))
    if ((await sampleSignal.count()) > 0) {
      await expect(sampleSignal.first()).toBeVisible()
    }
  })

  test('job detail external apply and practice links', async ({ page }) => {
    await page.goto('/jobs/data-engineer-remote-infosys')
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 20_000 })
    await expect(page.getByRole('button', { name: /practice missing skills/i })).toBeVisible({
      timeout: 15_000,
    })
    const external = page.locator('a[rel*="noopener"][target="_blank"]').filter({
      hasText: /apply on company site/i,
    })
    if ((await external.count()) > 0) {
      await expect(external.first()).toBeVisible()
    }
    await page.getByRole('button', { name: /practice missing skills/i }).click()
    await expect(page).toHaveURL(/\/practice/)
  })

  test('interview prep link from job detail when present', async ({ page }) => {
    await page.goto('/jobs/data-engineer-remote-infosys')
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 20_000 })
    const interview = page.getByRole('link', { name: /interview prep/i })
    if (await interview.count()) {
      await interview.first().click()
      await expect(page).toHaveURL(/interview|practice|company/i)
    }
  })

  test('student blocked from admin jobs', async ({ page }) => {
    await page.goto('/admin/jobs')
    await expect(page).toHaveURL(/\/($|\?)/)
  })
})
