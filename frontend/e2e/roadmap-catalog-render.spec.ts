/**
 * Live roadmap catalog rendering (E2E seed backend). Separate from mocked roadmap-mock specs.
 */
import { expect, test } from '@playwright/test'

import {
  apiBaseUrl,
  loadManifest,
  loginAccessToken,
  loginAs,
} from './helpers'
import {
  assertCatalogTotals,
  auditSlugInBrowser,
  bundledCatalog,
  bundledSlugs,
} from './roadmap-catalog-shared'

const fixtures = loadManifest()
const titleBySlug = new Map(bundledCatalog.roadmaps.map((r) => [r.family_slug, r.title]))
const BATCH_SIZE = 18
const batches: string[][] = []
for (let i = 0; i < bundledSlugs.length; i += BATCH_SIZE) {
  batches.push(bundledSlugs.slice(i, i + BATCH_SIZE))
}

const catalogRows: import('./roadmap-catalog-shared').SlugBrowserRow[] = []

test.describe('Roadmap catalog render (live)', () => {
  test.describe.configure({ mode: 'serial', timeout: 600_000 })

  test.beforeEach(async ({ page }) => {
    await loginAs(page, fixtures.users.student)
  })

  test.afterAll(() => {
    assertCatalogTotals(catalogRows)
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

  for (let batchIndex = 0; batchIndex < batches.length; batchIndex += 1) {
    const slugs = batches[batchIndex]
    test(`catalog graph mounts batch ${batchIndex + 1}/${batches.length}`, async ({
      page,
      request,
    }) => {
      test.setTimeout(900_000)
      const token = await loginAccessToken(request, fixtures.users.student)
      for (const slug of slugs) {
        const title = titleBySlug.get(slug) ?? slug
        await auditSlugInBrowser(page, request, slug, title, token, catalogRows)
      }
    })
  }

})
