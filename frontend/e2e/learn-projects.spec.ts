import { expect, test } from '@playwright/test'

import { loadManifest, loginAs } from './helpers'

const fixtures = loadManifest()

test.describe('Learn and Projects', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, fixtures.users.student)
  })

  test('learn course detail loads', async ({ page }) => {
    await page.goto('/learn')
    await expect(page.getByRole('heading', { level: 1 }).first()).toBeVisible()
    await page.goto(`/learn/courses/${fixtures.course.slug}`)
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 20_000 })
    await expect(page.getByText(/module|lesson|progress/i).first()).toBeVisible()
  })

  test('projects list and detail', async ({ page }) => {
    await page.goto('/practice/projects')
    await expect(page.getByRole('heading', { level: 1 }).first()).toBeVisible()
    await page.goto(`/practice/projects/${fixtures.project.slug}`)
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 20_000 })
    await expect(page.getByText(/roadmap|task|skill|continue/i).first()).toBeVisible()
    const continueBtn = page.getByRole('link', { name: /continue project/i }).or(
      page.getByRole('button', { name: /continue project/i }),
    )
    if (await continueBtn.count()) {
      await continueBtn.first().click()
      await expect(page).toHaveURL(/\/projects\/.+\/tasks\//)
    }
  })

  test('checklist task items persist', async ({ page }) => {
    await page.goto(`/practice/projects/${fixtures.project.slug}`)
    const checklist = page.getByText(/checklist/i).first()
    if (!(await checklist.count())) {
      test.skip(true, 'No checklist task visible on seeded project')
    }
    await checklist.click()
    const box = page.getByRole('checkbox').first()
    if (!(await box.count())) {
      test.skip(true, 'No checklist checkboxes')
    }
    const wasChecked = await box.isChecked()
    await box.click()
    await page.reload()
    await expect(box).toBeChecked({ checked: !wasChecked })
  })
})
