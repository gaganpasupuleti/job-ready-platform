/**
 * Live roadmap catalog rendering (E2E seed backend). Separate from mocked roadmap-mock specs.
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { expect, test } from '@playwright/test'

import {
  apiBaseUrl,
  attachConsoleGuard,
  loadManifest,
  loginAccessToken,
  loginAs,
} from './helpers'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const catalogPath = path.resolve(
  __dirname,
  '..',
  '..',
  'backend',
  'app',
  'data',
  'official-roadmap-catalog.json',
)
const resultsPath = path.join(__dirname, 'artifacts', 'roadmap-catalog-browser-results.json')
const bundledCatalog = JSON.parse(fs.readFileSync(catalogPath, 'utf8')) as {
  roadmaps: Array<{ family_slug: string; title: string }>
}
const bundledSlugs = bundledCatalog.roadmaps.map((r) => r.family_slug).sort()

const fixtures = loadManifest()

type SlugBrowserStatus = 'pass' | 'fail' | 'unavailable' | 'unverified'

type SlugBrowserRow = {
  slug: string
  status: SlugBrowserStatus
  nodeCount?: number
  error?: string
}

function writeBrowserResults(rows: SlugBrowserRow[], meta: Record<string, unknown>) {
  fs.mkdirSync(path.dirname(resultsPath), { recursive: true })
  const totals = rows.reduce(
    (acc, row) => {
      acc[row.status] = (acc[row.status] ?? 0) + 1
      return acc
    },
    {} as Record<SlugBrowserStatus, number>,
  )
  fs.writeFileSync(
    resultsPath,
    JSON.stringify(
      {
        capturedAt: new Date().toISOString(),
        slugTotal: bundledSlugs.length,
        totals,
        meta,
        rows,
      },
      null,
      2,
    ),
  )
}

test.describe('Roadmap catalog render (live)', () => {
  test.describe.configure({ timeout: 900_000 })

  test.beforeEach(async ({ page }) => {
    await loginAs(page, fixtures.users.student)
  })

  test('live catalog matches bundled slug inventory', async ({ request }) => {
    const token = await loginAccessToken(request, fixtures.users.student)
    const res = await request.get(`${apiBaseUrl()}/roadmap/catalog`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    expect(res.ok(), `catalog HTTP ${res.status()}`).toBeTruthy()
    const body = await res.json()
    const liveSlugs = (body.roadmaps ?? [])
      .map((r: { family_slug: string }) => r.family_slug)
      .sort()
    expect(liveSlugs).toEqual(bundledSlugs)
  })

  test('every catalog graph mounts with nodes (per-slug report)', async ({ page }) => {
    const guard = attachConsoleGuard(page)
    const titleBySlug = new Map(bundledCatalog.roadmaps.map((r) => [r.family_slug, r.title]))
    const rows: SlugBrowserRow[] = []

    for (const slug of bundledSlugs) {
      const title = titleBySlug.get(slug) ?? slug
      try {
        await page.goto(`/roadmaps/${slug}`, { waitUntil: 'domcontentloaded' })
        await expect(page.locator('#main-content')).toBeVisible({ timeout: 20_000 })
        await expect(page.getByRole('heading', { name: new RegExp(title, 'i') })).toBeVisible({
          timeout: 30_000,
        })
        const flow = page.locator('.ors-canvas .react-flow')
        await expect(flow).toBeVisible({ timeout: 60_000 })
        let nodeCount = 0
        try {
          await expect
            .poll(async () => page.locator('.ors-canvas .react-flow__node').count(), {
              timeout: 90_000,
            })
            .toBeGreaterThan(0)
          nodeCount = await page.locator('.ors-canvas .react-flow__node').count()
        } catch {
          nodeCount = await page.locator('.ors-canvas .react-flow__node').count()
          rows.push({
            slug,
            status: 'fail',
            nodeCount,
            error: 'no visible react-flow nodes after mount (graph empty or onlyRenderVisibleElements)',
          })
          continue
        }
        rows.push({ slug, status: 'pass', nodeCount })
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err)
        const status: SlugBrowserStatus = /timeout|net::|ECONNREFUSED|503|502/i.test(message)
          ? 'unavailable'
          : 'fail'
        rows.push({ slug, status, error: message.slice(0, 500) })
      }
    }

    writeBrowserResults(rows, { consoleErrors: guard.errors })
    const totals = rows.reduce(
      (acc, row) => {
        acc[row.status] = (acc[row.status] ?? 0) + 1
        return acc
      },
      {} as Record<SlugBrowserStatus, number>,
    )

    guard.assertClean([/react-flow|ResizeObserver|favicon/i])

    expect(totals.fail ?? 0, `catalog browser failures: ${JSON.stringify(rows.filter((r) => r.status === 'fail'))}`).toBe(0)
    expect(totals.unavailable ?? 0).toBe(0)
  })
})
