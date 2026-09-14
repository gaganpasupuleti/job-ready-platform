import { expect, test } from '@playwright/test'
import path from 'node:path'
import fs from 'node:fs'

import { loadManifest, loginAs } from './helpers'

const fixtures = loadManifest()
const shotDir = path.resolve('e2e-artifacts/acceptance-shots')

async function shot(page: import('@playwright/test').Page, name: string) {
  fs.mkdirSync(shotDir, { recursive: true })
  const file = path.join(shotDir, `${name}.png`)
  await page.screenshot({ path: file, fullPage: true })
  return file
}

test.describe('Acceptance shots', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, fixtures.users.student)
  })

  test('SQL playground success and error', async ({ page }) => {
    await page.goto('/practice/playground/sql')
    await expect(page.getByTestId('sql-playground-heading')).toBeVisible({ timeout: 20_000 })
    const project = test.info().project.name
    if (project === 'mobile') {
      await page.getByRole('tab', { name: 'Schema' }).click()
    } else {
      const expanders = page.locator('aside button')
      if (await expanders.count()) {
        await expanders.first().click({ timeout: 5_000 }).catch(() => {})
      }
    }
    await shot(page, `sql-schema-${project}`)

    if (project === 'mobile') {
      await page.getByRole('tab', { name: 'Editor' }).click()
    }
    const runBtn = page.getByRole('button', { name: /run query/i })
    await expect(runBtn).toBeEnabled({ timeout: 45_000 })
    await runBtn.click()
    await expect(page.getByText(/not graded|does not create/i).first()).toBeVisible({ timeout: 45_000 })
    await page.waitForFunction(
      () => {
        const resultsHeading = [...document.querySelectorAll('h2')].find(
          (el) => el.textContent?.trim() === 'Results',
        )
        const panel = resultsHeading?.closest('div')
        if (!panel) return false
        const text = panel.innerText ?? ''
        if (/Run a query to see rows here/i.test(text)) return false
        if (/Running query/i.test(text)) return false
        if (/Unable to run/i.test(text)) return false
        if (panel.querySelector('[role="alert"]')) return false
        const dataRows = panel.querySelectorAll('table tbody tr')
        if (dataRows.length > 0) return true
        return /\d+\s+rows?\b/i.test(text) && !/Row limit/i.test(text)
      },
      null,
      { timeout: 45_000 },
    )
    if (project === 'mobile') {
      await page.getByRole('tab', { name: 'Results' }).click()
    }
    await shot(page, `sql-success-${project}`)

    // Force an invalid query through the editor textarea/monaco fallback
    await page.evaluate(() => {
      const key = Object.keys(localStorage).find((item) => item.includes('sql-playground-draft'))
      if (key) localStorage.setItem(key, 'SELECT missing_column FROM books')
    })
    await page.reload()
    await expect(page.getByTestId('sql-playground-heading')).toBeVisible({ timeout: 20_000 })
    await page.getByRole('button', { name: /run query/i }).click()
    await expect(page.getByRole('alert')).toBeVisible({ timeout: 30_000 })
    await shot(page, `sql-error-${test.info().project.name}`)
  })

  test('Python lock aliases', async ({ page }) => {
    for (const route of ['/practice/python', '/practice/compiler', '/practice/compiler/python']) {
      await page.goto(route)
      await expect(page.getByText('Python — Coming soon')).toBeVisible({ timeout: 15_000 })
      await expect(page.locator('.monaco-editor')).toHaveCount(0)
      await expect(page.getByRole('button', { name: /^run$/i })).toHaveCount(0)
    }
    await shot(page, `python-locked-${test.info().project.name}`)
  })

  test('Locked python assignment and non-python draft', async ({ page }) => {
    await page.goto('/learn/assignments/py-assign-exceptions')
    await expect(page.getByText(/unavailable|locked/i).first()).toBeVisible({ timeout: 15_000 })
    await expect(page.getByRole('button', { name: /submit for review/i })).toHaveCount(0)
    await shot(page, `assignment-python-locked-${test.info().project.name}`)

    await page.goto('/learn/assignments/da-assign-paid-totals')
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 15_000 })
    await expect(page.getByRole('button', { name: /save draft/i })).toBeVisible()
    await shot(page, `assignment-sql-available-${test.info().project.name}`)
  })

  test('Syllabus lesson with practice', async ({ page }) => {
    await page.goto('/learn/syllabus')
    await expect(page.getByRole('heading', { name: 'Syllabus' })).toBeVisible({ timeout: 15_000 })
    await expect(page.getByText('CRT / Aptitude')).toBeVisible()
    await expect(page.getByRole('heading', { name: 'DSA Foundations' })).toBeVisible()
    await expect(page.getByText('Coming soon').first()).toBeVisible()
    await shot(page, `syllabus-index-${test.info().project.name}`)

    await page.goto('/learn/syllabus/syl-crt-quant-percentages')
    await expect(page.getByRole('heading', { name: /percentages for placement/i }).first()).toBeVisible({
      timeout: 30_000,
    })
    await expect(page.getByText(/worked example|sale price|percent/i).first()).toBeVisible()
    await page.getByRole('radio').first().check()
    await page.getByRole('button', { name: /check answer/i }).click()
    await expect(page.getByText(/correct|not quite/i).first()).toBeVisible({ timeout: 15_000 })
    await shot(page, `syllabus-lesson-practice-${test.info().project.name}`)
  })
})
