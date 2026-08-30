import { expect, test } from '@playwright/test'

import { fillPromptEditor, loadManifest, loginAs } from './helpers'

const fixtures = loadManifest()

test.describe('Prompt and Scenario', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, fixtures.users.student)
  })

  test('prompt challenge test and submit', async ({ page }) => {
    test.skip(!fixtures.prompt.slug, 'No prompt challenge seeded')
    await page.goto(`/ai/prompt-engineering/challenges/${fixtures.prompt.slug}`)
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 20_000 })
    await expect(page.getByText(/requirement|example|hint|mastery|score|instruction/i).first()).toBeVisible()
    await fillPromptEditor(page, 'Extract skills from {{document_context}} as JSON with a skills array. Do not invent employers.')
    const testBtn = page.getByRole('button', { name: /test prompt/i })
    await testBtn.click()
    await expect(testBtn).toBeEnabled({ timeout: 45_000 })
    await expect(page.getByText(/score|rubric|pass|fail|result/i).first()).toBeVisible()
    const submit = page.getByRole('button', { name: /submit prompt/i })
    await submit.click()
    await expect(submit).toBeEnabled({ timeout: 45_000 })
    await expect(page.getByText(/score|master|submission|overall/i).first()).toBeVisible()
    const body = await page.locator('body').innerText()
    expect(body.toLowerCase()).not.toMatch(/hidden input:|secret case input/)
  })

  test('scenario workflow completes', async ({ page }) => {
    test.skip(!fixtures.scenario.slug, 'No scenario seeded')
    await page.goto(`/scenarios/${fixtures.scenario.slug}`)
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 20_000 })
    await expect(page.getByText(/evidence|metric|log|alert|architecture|timeline|step|current step/i).first()).toBeVisible()

    for (let i = 0; i < 12; i += 1) {
      const submitScenario = page.getByRole('button', { name: /submit scenario/i })
      if (await submitScenario.count()) {
        await submitScenario.click()
        break
      }
      const nextStep = page.getByRole('button', { name: /^next step$/i })
      if (await nextStep.count()) {
        await nextStep.click()
        continue
      }
      const option = page.locator('label').filter({ has: page.locator('input[type="radio"]:not([disabled])') }).first()
      if (await option.count()) {
        await option.click()
        const confirm = page.getByRole('button', { name: /confirm decision/i })
        await expect(confirm).toBeEnabled()
        await confirm.click()
        continue
      }
      break
    }

    await expect(page.getByText(/score|master|retry|next scenario|review|correct/i).first()).toBeVisible({
      timeout: 20_000,
    })
  })
})
