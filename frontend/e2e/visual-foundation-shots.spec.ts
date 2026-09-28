import { expect, test } from '@playwright/test'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { loadManifest, loginAs } from './helpers'

const fixtures = loadManifest()
const outDir = path.join(path.dirname(fileURLToPath(import.meta.url)), 'artifacts', 'visual-foundation')

test.describe('Visual foundation screenshots', () => {
  test.beforeAll(() => {
    fs.mkdirSync(outDir, { recursive: true })
  })

  for (const project of ['desktop', 'mobile'] as const) {
    test.describe(project, () => {
      test.use(
        project === 'mobile'
          ? { viewport: { width: 390, height: 844 } }
          : { viewport: { width: 1440, height: 900 } },
      )

      test(`capture key surfaces (${project})`, async ({ page }) => {
        await loginAs(page, fixtures.users.student)

        const shots: Array<{ name: string; path: string }> = [
          { name: 'dashboard', path: '/' },
          { name: 'practice-hub', path: '/practice' },
          { name: 'coding', path: '/practice/coding' },
          { name: 'mcq', path: '/practice/mcq' },
          { name: 'python-playground', path: '/practice/python' },
        ]

        for (const shot of shots) {
          await page.goto(shot.path)
          await page.waitForTimeout(800)
          await page.screenshot({
            path: path.join(outDir, `${project}-${shot.name}.png`),
            fullPage: true,
          })
        }

        if (fixtures.coding.id) {
          await page.goto(`/practice/dsa/${fixtures.coding.id}`)
          await expect(page.getByRole('main').getByRole('heading', { level: 1 })).toBeVisible({
            timeout: 20_000,
          })
          await page.screenshot({
            path: path.join(outDir, `${project}-dsa-workspace.png`),
            fullPage: true,
          })
        }

        await page.goto('/practice/aptitude')
        await page.getByRole('button', { name: fixtures.mcq_topic.name, exact: true }).click()
        await page.getByRole('button', { name: /^easy$/i }).click()
        await page.getByRole('combobox').selectOption('5')
        await page.getByRole('button', { name: /^exam$/i }).click()
        await page.getByRole('button', { name: /start session/i }).click()
        await expect(page).toHaveURL(/\/practice\/sessions\//, { timeout: 20_000 })
        await page.waitForTimeout(600)
        await page.screenshot({
          path: path.join(outDir, `${project}-mcq-exam.png`),
          fullPage: true,
        })
      })
    })
  }
})
