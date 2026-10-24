/**
 * Learner-visible behavior for data-analyst "VLOOKUP / HLOOKUP" after upstream edge sanitize.
 * Does not assert a graph edge that upstream never materialized as a topic link.
 */
import { expect, test } from '@playwright/test'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { loadManifest, loginAs } from './helpers'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const shotDir = path.join(__dirname, 'artifacts', 'special-roadmap-maps')

const fixtures = loadManifest()
const VLOOKUP_NODE = '9sIP-jpNjtA1JPCBjTf-H'

test.describe('data-analyst unresolved topic path (live)', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, fixtures.users.student)
  })

  test('outline opens VLOOKUP article when content is provisioned', async ({ page }) => {
    test.setTimeout(120_000)
    await page.goto('/roadmaps/data-analyst')
    await expect(page.getByRole('heading', { name: /data analyst/i })).toBeVisible({ timeout: 60_000 })
    await expect(page.locator('.ors-canvas .react-flow')).toBeVisible({ timeout: 60_000 })

    const topicSearch = page.getByRole('searchbox', { name: /find topic in outline/i })
    await expect(topicSearch).toBeVisible({ timeout: 20_000 })
    await topicSearch.fill('VLOOKUP')
    const searchHit = page
      .getByRole('region', { name: /topic search results/i })
      .getByRole('button', { name: /vlookup/i })
      .first()
    await expect(searchHit).toBeVisible({ timeout: 20_000 })
    await searchHit.click()

    await expect(page.getByRole('heading', { level: 2, name: /vlookup/i })).toBeVisible({
      timeout: 30_000,
    })
    const articleText = await page.locator('.ors-panel--desktop .ors-markdown, [role="dialog"] .ors-markdown')
      .first()
      .innerText()
    expect(articleText.replace(/\s+/g, ' ').trim().length).toBeGreaterThan(80)

    await page.screenshot({
      path: path.join(shotDir, 'data-analyst-vlookup-outline-1366.png'),
      fullPage: false,
    })
  })

  test('topic API returns markdown for VLOOKUP node id', async ({ request }) => {
    const loginRes = await request.post(`${process.env.E2E_API_URL ?? 'http://127.0.0.1:8000'}/api/v1/auth/login`, {
      data: { email: fixtures.users.student.email, password: fixtures.users.student.password },
    })
    expect(loginRes.ok()).toBeTruthy()
    const { access_token } = await loginRes.json()
    const articleRes = await request.get(
      `${process.env.E2E_API_URL ?? 'http://127.0.0.1:8000'}/api/v1/roadmap/official/data-analyst/topics/${VLOOKUP_NODE}`,
      { headers: { Authorization: `Bearer ${access_token}` } },
    )
    expect(articleRes.ok(), `article HTTP ${articleRes.status()}`).toBeTruthy()
    const body = await articleRes.json()
    expect(String(body.markdown ?? '').trim().length).toBeGreaterThan(80)
  })
})
