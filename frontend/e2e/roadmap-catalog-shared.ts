import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { expect, type APIRequestContext, type Page } from '@playwright/test'

import { apiBaseUrl, loginAccessToken } from './helpers'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
export const catalogPath = path.resolve(
  __dirname,
  '..',
  '..',
  'backend',
  'app',
  'data',
  'official-roadmap-catalog.json',
)
export const resultsPath = path.join(__dirname, 'artifacts', 'roadmap-catalog-browser-results.json')

export const bundledCatalog = JSON.parse(fs.readFileSync(catalogPath, 'utf8')) as {
  roadmaps: Array<{ family_slug: string; title: string }>
}
export const bundledSlugs = bundledCatalog.roadmaps.map((r) => r.family_slug).sort()

export type SlugBrowserStatus = 'pass' | 'fail' | 'unavailable' | 'unverified'

export type SlugBrowserRow = {
  slug: string
  status: SlugBrowserStatus
  graphUrl: string
  graphHttpStatus?: number
  payloadValid?: boolean
  nodeCount?: number
  browserNodeCount?: number
  rendererErrors?: string[]
  error?: string
}

const CATALOG_CONSOLE_ALLOWLIST: Array<{ pattern: RegExp; reason: string }> = [
  {
    pattern: /favicon/i,
    reason: 'Missing favicon in E2E static host does not affect roadmap rendering.',
  },
]

export function filterUnexpectedConsole(errors: string[]) {
  return errors.filter(
    (e) => !CATALOG_CONSOLE_ALLOWLIST.some(({ pattern }) => pattern.test(e)),
  )
}

export function writeBrowserResults(rows: SlugBrowserRow[], meta: Record<string, unknown>) {
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
        consoleAllowlist: CATALOG_CONSOLE_ALLOWLIST.map((e) => ({
          pattern: String(e.pattern),
          reason: e.reason,
        })),
        meta,
        rows,
      },
      null,
      2,
    ),
  )
}

function validateGraphPayload(body: unknown): { ok: boolean; reason?: string } {
  if (!body || typeof body !== 'object') return { ok: false, reason: 'not an object' }
  const record = body as { nodes?: unknown; edges?: unknown }
  if (!Array.isArray(record.nodes)) return { ok: false, reason: 'nodes missing' }
  if (!Array.isArray(record.edges)) return { ok: false, reason: 'edges missing' }
  if (record.nodes.length === 0) return { ok: false, reason: 'nodes empty' }
  return { ok: true }
}

export async function auditSlugInBrowser(
  page: Page,
  request: APIRequestContext,
  slug: string,
  title: string,
  token: string,
  rows: SlugBrowserRow[],
) {
  const graphUrl = `${apiBaseUrl()}/roadmap/official/${slug}/graph`
  const row: SlugBrowserRow = { slug, status: 'unverified', graphUrl }
  const slugErrors: string[] = []
  const onPageError = (err: Error) => slugErrors.push(`pageerror: ${err.message}`)
  const onConsole = (msg: { type: () => string; text: () => string }) => {
    if (msg.type() === 'error') slugErrors.push(`console.error: ${msg.text()}`)
  }
  page.on('pageerror', onPageError)
  page.on('console', onConsole)

  try {
    const graphRes = await request.get(graphUrl, {
      headers: { Authorization: `Bearer ${token}` },
    })
    row.graphHttpStatus = graphRes.status()
    if (!graphRes.ok()) {
      row.status = graphRes.status() >= 500 ? 'unavailable' : 'fail'
      row.error = `graph HTTP ${graphRes.status()}`
      return
    }
    const payload = await graphRes.json()
    const validation = validateGraphPayload(payload)
    row.payloadValid = validation.ok
    if (!validation.ok) {
      row.status = 'fail'
      row.error = `payload invalid: ${validation.reason}`
      return
    }
    row.nodeCount = (payload as { nodes: unknown[] }).nodes.length

    await page.goto(`/roadmaps/${slug}`, { waitUntil: 'domcontentloaded' })
    await expect(page.locator('#main-content')).toBeVisible({ timeout: 20_000 })
    await expect(page.getByRole('heading', { name: new RegExp(title, 'i') })).toBeVisible({
      timeout: 30_000,
    })
    const flow = page.locator('.ors-canvas .react-flow')
    await expect(flow).toBeVisible({ timeout: 60_000 })
    await expect
      .poll(async () => page.locator('.ors-canvas .react-flow__node').count(), {
        timeout: 45_000,
      })
      .toBeGreaterThan(0)
    row.browserNodeCount = await page.locator('.ors-canvas .react-flow__node').count()
    const unexpected = filterUnexpectedConsole(slugErrors)
    if (unexpected.length > 0) {
      row.rendererErrors = unexpected.slice(0, 8)
      row.status = 'fail'
      row.error = unexpected[0]?.slice(0, 300)
    } else {
      row.status = 'pass'
    }
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    row.error = message.slice(0, 500)
    if (/net::ERR_|ECONNREFUSED|503|502|fetch failed/i.test(message)) {
      row.status = 'unavailable'
    } else if (/timeout/i.test(message)) {
      row.status = 'fail'
      row.error = `render or assertion timeout: ${row.error}`
    } else {
      row.status = 'fail'
    }
  } finally {
    page.off('pageerror', onPageError)
    page.off('console', onConsole)
    rows.push(row)
  }
}

export function assertCatalogTotals(rows: SlugBrowserRow[]) {
  writeBrowserResults(rows, {})
  const totals = rows.reduce(
    (acc, row) => {
      acc[row.status] = (acc[row.status] ?? 0) + 1
      return acc
    },
    {} as Record<SlugBrowserStatus, number>,
  )
  expect(rows.length, 'every bundled slug must be audited').toBe(bundledSlugs.length)
  expect(totals.fail ?? 0, `catalog browser failures: ${JSON.stringify(rows.filter((r) => r.status === 'fail'))}`).toBe(0)
  expect(totals.unavailable ?? 0, `catalog unavailable: ${JSON.stringify(rows.filter((r) => r.status === 'unavailable'))}`).toBe(0)
  expect(totals.unverified ?? 0).toBe(0)
}
