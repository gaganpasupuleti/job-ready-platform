/**
 * Workbench transplant browser QA gate.
 * Marks sandbox/Judge0-dependent assertions as skipped when infra is unavailable.
 */
import { expect, test, type Page } from '@playwright/test'

import { attachConsoleGuard, fillMonaco, loadManifest, loginAs } from './helpers'

const fixtures = loadManifest()
const apiUrl = process.env.E2E_API_URL || 'http://127.0.0.1:8000'
const SQL_SLUG = fixtures.sql.slug
const DSA_ID = fixtures.coding.id

async function sqlSandboxReady(): Promise<boolean> {
  try {
    const res = await fetch(`${apiUrl}/api/v1/sql/execution-status`)
    if (!res.ok) return false
    const data = (await res.json()) as { available?: boolean; status?: string }
    return Boolean(data.available) && data.status !== 'sandbox_unavailable'
  } catch {
    return false
  }
}

async function judge0Ready(page: Page): Promise<boolean> {
  try {
    const token = await page.evaluate(
      () =>
        localStorage.getItem('jrp_access_token') ||
        localStorage.getItem('access_token') ||
        localStorage.getItem('token'),
    )
    const res = await fetch(`${apiUrl}/api/v1/coding/execution-status`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    if (!res.ok) return false
    const data = (await res.json()) as { available?: boolean }
    return Boolean(data.available)
  } catch {
    return false
  }
}

test.describe('SQL workbench QA', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, fixtures.users.student)
  })

  test('catalog + 3-pane desktop workbench chrome', async ({ page }) => {
    const guard = attachConsoleGuard(page)
    await page.setViewportSize({ width: 1440, height: 900 })

    await page.goto('/practice/sql')
    await expect(page.getByRole('heading', { name: /sql practice/i })).toBeVisible({ timeout: 30_000 })
    await expect(page.getByText(/practice recommendations|continue unfinished|browse catalog/i).first()).toBeVisible()

    await page.goto(`/practice/sql/${SQL_SLUG}`)
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 30_000 })

    // 3-pane chrome
    await expect(page.locator('.sql-workbench')).toBeVisible()
    await expect(page.getByText(/^Schema$/)).toBeVisible()
    await expect(page.getByText('Practice Question')).toBeVisible()
    await expect(page.getByText('Query Editor')).toBeVisible()
    await expect(page.locator('.monaco-editor:visible').first()).toBeVisible({ timeout: 30_000 })
    await expect(page.getByRole('tablist', { name: 'Results' })).toBeVisible()

    // Resize handles present on desktop
    await expect(page.getByRole('button', { name: 'Resize side panel' }).first()).toBeVisible()
    await expect(page.getByRole('button', { name: 'Resize results panel' })).toBeVisible()

    // Controls
    await expect(page.getByRole('button', { name: /^reset$/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /^format$/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /clear output/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /reset layout/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /^run$/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /^submit$/i })).toBeVisible()

    // Learning guide + expected columns + templates
    await expect(page.getByText(/how to approach this/i)).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Expected columns' })).toBeVisible()
    await expect(page.getByText(/quick queries/i)).toBeVisible()
    await expect(page.getByRole('button', { name: 'SELECT *' })).toBeVisible()

    // Font presets
    await expect(page.getByRole('button', { name: /^small$/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /^medium$/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /^large$/i })).toBeVisible()
    await page.getByRole('button', { name: /^large$/i }).click()
    await expect(page.getByRole('button', { name: /^large$/i })).toHaveClass(/bg-\[var\(--color-accent\)\]/)

    // Shortcut hint strip
    await expect(page.getByText(/Run: Ctrl\/Cmd\+Enter/i)).toBeVisible()

    guard.assertClean([/favicon|Failed to load resource|net::ERR_/i])
  })

  test('pane collapse/expand + reset layout + layout persist', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 })
    await page.goto(`/practice/sql/${SQL_SLUG}`)
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 30_000 })

    await page.getByRole('button', { name: 'Collapse Schema explorer' }).click()
    await expect(page.getByRole('button', { name: 'Expand Schema explorer' })).toBeVisible()
    await page.getByRole('button', { name: 'Expand Schema explorer' }).click()
    await expect(page.getByText(/^Schema$/)).toBeVisible()

    await page.getByRole('button', { name: 'Collapse Problem' }).click()
    await expect(page.getByRole('button', { name: 'Expand Problem' })).toBeVisible()
    await page.getByRole('button', { name: 'Expand Problem' }).click()
    await expect(page.getByText('Practice Question')).toBeVisible()

    await page.getByRole('button', { name: 'Collapse Results' }).click()
    await expect(page.getByRole('button', { name: 'Expand Results' })).toBeVisible()
    await page.getByRole('button', { name: 'Expand Results' }).click()
    await expect(page.getByRole('tablist', { name: 'Results' })).toBeVisible()

    // Collapse left and reload — layout should persist
    await page.getByRole('button', { name: 'Collapse Schema explorer' }).click()
    await expect(page.getByRole('button', { name: 'Expand Schema explorer' })).toBeVisible()
    await page.reload()
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 30_000 })
    await expect(page.getByRole('button', { name: 'Expand Schema explorer' })).toBeVisible()

    await page.getByRole('button', { name: /reset layout/i }).click()
    await expect(page.getByText(/^Schema$/)).toBeVisible()
  })

  test('mobile Problem|Code|Output does not duplicate workspace', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto(`/practice/sql/${SQL_SLUG}`)
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 30_000 })

    const workspaceTabs = page.getByRole('tablist', { name: 'Workspace' })
    await expect(workspaceTabs).toBeVisible()
    await expect(workspaceTabs.getByRole('button', { name: /^problem$/i })).toBeVisible()
    await expect(workspaceTabs.getByRole('button', { name: /^code$/i })).toBeVisible()
    await expect(workspaceTabs.getByRole('button', { name: /^output$/i })).toBeVisible()

    // Only one workspace mode visible at a time — no desktop 3-pane duplication
    await expect(page.getByRole('button', { name: 'Resize side panel' })).toHaveCount(0)

    await workspaceTabs.getByRole('button', { name: /^problem$/i }).click()
    await expect(page.getByText(/^Schema$/)).toBeVisible()
    await expect(page.getByText('Practice Question')).toBeVisible()

    await workspaceTabs.getByRole('button', { name: /^code$/i }).click()
    await expect(page.locator('.monaco-editor:visible').first()).toBeVisible({ timeout: 30_000 })

    await workspaceTabs.getByRole('button', { name: /^output$/i }).click()
    await expect(page.getByRole('tablist', { name: 'Results' })).toBeVisible()
  })

  test('narrow viewport (<1024) Problem|Code|Output', async ({ page }) => {
    // Breakpoint matches PracticeWorkspace: desktop at min-width 1024px.
    await page.setViewportSize({ width: 1023, height: 768 })
    await page.goto(`/practice/sql/${SQL_SLUG}`)
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 30_000 })
    await expect(page.getByRole('tablist', { name: 'Workspace' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Resize side panel' })).toHaveCount(0)
  })

  test('schema select, insert SELECT/column, templates, format, clear, reset, tabs', async ({
    page,
  }) => {
    await page.setViewportSize({ width: 1440, height: 900 })
    await page.goto(`/practice/sql/${SQL_SLUG}`)
    await expect(page.getByRole('main').getByRole('heading', { level: 1 })).toBeVisible({
      timeout: 30_000,
    })

    // Select schema table
    const tableBtn = page
      .locator('.sql-workbench')
      .getByRole('button')
      .filter({ hasText: /^products$/i })
      .first()
    await tableBtn.click()
    // Expand columns
    await page.getByRole('button', { name: /expand table/i }).first().click()
    await expect(page.getByTitle('Insert column').first()).toBeVisible()

    // Insert SELECT
    await page.getByTitle('Insert SELECT *').first().click()
    await expect(page.getByText(/template inserted|SELECT \*/i).first()).toBeVisible({
      timeout: 10_000,
    })

    // Insert column
    await page.getByTitle('Insert column').first().click()

    // Quick query template
    await page.getByRole('button', { name: 'WHERE' }).click()
    await expect(page.getByText(/quick query inserted/i)).toBeVisible()

    // Format
    await fillMonaco(page, 'select product_name from products')
    await page.getByRole('button', { name: /^format$/i }).click()
    await expect(page.getByText(/SELECT/i).first()).toBeVisible()

    // Bottom tabs
    for (const name of [/results/i, /expected/i, /messages/i, /history|submissions/i]) {
      await page.getByRole('tablist', { name: 'Results' }).getByRole('tab', { name }).click()
    }
    await page
      .getByRole('tablist', { name: 'Results' })
      .getByRole('tab', { name: /expected/i })
      .click()
    await expect(page.getByText(/sample|expected|column/i).first()).toBeVisible()

    // Hints tab in problem panel
    await page.getByRole('tab', { name: /^hints$/i }).click()
    await expect(page.getByText(/hint|reveal|no hints/i).first()).toBeVisible()

    // Solution gated
    await page.getByRole('tab', { name: /^solution$/i }).click()
    await expect(page.getByText(/locked|accept|solve|solution/i).first()).toBeVisible()

    // Clear output
    await page.getByRole('button', { name: /clear output/i }).click()

    // Reset editor
    page.once('dialog', (d) => d.accept())
    await page.getByRole('button', { name: /^reset$/i }).click()

    // Reload preserves problem
    await page.reload()
    await expect(page).toHaveURL(new RegExp(`/practice/sql/${SQL_SLUG}`))
    await expect(page.getByRole('main').getByRole('heading', { level: 1 })).toBeVisible({
      timeout: 30_000,
    })
  })

  test('Monaco schema-aware completion + editor shortcuts (non-run)', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 })
    await page.goto(`/practice/sql/${SQL_SLUG}`)
    await expect(page.locator('.monaco-editor:visible').first()).toBeVisible({ timeout: 30_000 })

    // Drive Monaco via the exposed editor API so cursor/prefix are deterministic.
    const triggered = await page.evaluate(() => {
      const w = window as unknown as {
        __jobReadyMonaco?: {
          setValue: (v: string) => void
          getValue: () => string
          setPosition: (p: { lineNumber: number; column: number }) => void
          focus: () => void
          trigger: (source: string, handlerId: string, payload: unknown) => void
        }
      }
      const ed = w.__jobReadyMonaco
      if (!ed) return false
      ed.setValue('SELECT * FROM prod')
      ed.setPosition({ lineNumber: 1, column: 'SELECT * FROM prod'.length + 1 })
      ed.focus()
      ed.trigger('qa', 'editor.action.triggerSuggest', {})
      return true
    })
    expect(triggered).toBe(true)

    const suggest = page.locator('.editor-widget.suggest-widget.visible')
    await expect(suggest).toBeVisible({ timeout: 10_000 })
    const showMore = suggest.getByText(/show more/i)
    if (await showMore.isVisible().catch(() => false)) {
      await showMore.click()
    }
    await expect(suggest).toContainText(/products/i, { timeout: 10_000 })

    // Format shortcut
    await fillMonaco(page, 'select 1')
    await page.locator('.monaco-editor:visible').first().click()
    await page.keyboard.press('Control+Shift+F')
    await expect(page.getByText(/SELECT/i).first()).toBeVisible()
  })

  test('Run/Submit API wiring when sandbox available; otherwise honest skip', async ({ page }) => {
    const ready = await sqlSandboxReady()
    test.skip(!ready, 'SQL sandbox unavailable (postgres :5433 / Docker)')

    await page.goto(`/practice/sql/${SQL_SLUG}`)
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 30_000 })
    await fillMonaco(page, fixtures.sql.accepted_query)

    const runReq = page.waitForRequest(
      (r) => r.url().includes('/api/v1/sql/') && r.url().includes('/run') && r.method() === 'POST',
    )
    await page.getByRole('button', { name: /^run$/i }).click()
    await runReq
    await expect(page.getByRole('button', { name: /^run$/i })).toBeEnabled({ timeout: 45_000 })

    await fillMonaco(page, fixtures.sql.wrong_query)
    const submitReq = page.waitForRequest(
      (r) => r.url().includes('/api/v1/sql/') && r.url().includes('/submit') && r.method() === 'POST',
    )
    await page.getByRole('button', { name: /^submit$/i }).click()
    await submitReq
    await expect(page.getByRole('button', { name: /^submit$/i })).toBeEnabled({ timeout: 45_000 })
    await expect(page.getByText(/hidden|expected result rows stay hidden|wrong|incorrect/i).first()).toBeVisible()
  })

  test('when sandbox down: banner shown, Run/Submit disabled, no fake success', async ({ page }) => {
    const ready = await sqlSandboxReady()
    test.skip(ready, 'Sandbox is available — unavailable-path check not applicable')

    await page.goto(`/practice/sql/${SQL_SLUG}`)
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 30_000 })
    await expect(page.getByText(/sql execution is temporarily unavailable/i)).toBeVisible()
    await expect(page.getByRole('button', { name: /^run$/i })).toBeDisabled()
    await expect(page.getByRole('button', { name: /^submit$/i })).toBeDisabled()
    await expect(page.getByText(/accepted/i)).toHaveCount(0)
  })
})

test.describe('DSA workbench QA', () => {
  test.beforeEach(async ({ page }) => {
    test.skip(!DSA_ID, 'No coding problem id in manifest')
    await loginAs(page, fixtures.users.student)
  })

  test('catalog + problem chrome, fonts, bottom tabs, gating', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 })
    await page.goto('/practice/dsa')
    await expect(page.getByRole('heading', { name: /dsa practice/i })).toBeVisible({ timeout: 30_000 })

    await page.goto(`/practice/dsa/${DSA_ID}`)
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 30_000 })

    await expect(page.locator('.dsa-workbench').first()).toBeVisible()
    await expect(page.getByText(/· editor/i).first()).toBeVisible()
    await expect(page.getByRole('button', { name: /^small$/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /^run$/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /^submit$/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /^reset$/i })).toBeVisible()

    for (const name of [/test results/i, /^hints$/i, /submissions/i, /^output$/i]) {
      await page.getByRole('tab', { name }).click()
    }

    await page.getByRole('button', { name: /^large$/i }).click()
    await expect(page.locator('.monaco-editor:visible').first()).toBeVisible({ timeout: 30_000 })
  })

  test('Judge0 unavailable: no fake success; draft + reset', async ({ page }) => {
    await page.goto(`/practice/dsa/${DSA_ID}`)
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 30_000 })

    const ready = await judge0Ready(page)
    if (!ready) {
      await expect(
        page.getByText(/execution is temporarily unavailable|currently unavailable/i),
      ).toBeVisible()
      await expect(page.getByRole('button', { name: /^run$/i })).toBeDisabled()
      await expect(page.getByRole('button', { name: /^submit$/i })).toBeDisabled()
      await expect(page.getByText(/accepted|all tests passed/i)).toHaveCount(0)
    } else {
      test.info().annotations.push({ type: 'note', description: 'Judge0 available — unavailable path N/A' })
    }

    const codeTab = page.getByRole('button', { name: /^code$/i })
    if (await codeTab.count()) await codeTab.click()

    const marker = `# qa-draft-${Date.now()}`
    await page.evaluate(
      ({ problemId, markerText }) => {
        const keys = Object.keys(localStorage).filter(
          (k) => k.includes(problemId) && k.startsWith('coding-draft:'),
        )
        const key = keys[0] || `coding-draft:anon:${problemId}:71`
        localStorage.setItem(key, `${markerText}\nprint("persisted")`)
      },
      { problemId: DSA_ID!, markerText: marker },
    )
    await page.reload()
    if (await codeTab.count()) await codeTab.click()
    await expect(page.getByText(marker)).toBeVisible({ timeout: 15_000 })

    page.once('dialog', (d) => d.accept())
    await page.getByRole('button', { name: /^reset$/i }).click()
  })

  test('Judge0 run integration when available', async ({ page }) => {
    await page.goto(`/practice/dsa/${DSA_ID}`)
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 30_000 })
    const ready = await judge0Ready(page)
    test.skip(!ready, 'Judge0 disabled/unavailable')
    await expect(page.getByRole('button', { name: /^run$/i })).toBeEnabled()
  })
})

test.describe('Regression routes smoke', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, fixtures.users.student)
  })

  test('core practice + track routes render', async ({ page }) => {
    const routes = [
      '/practice',
      '/practice/sql',
      '/practice/dsa',
      '/learn',
      '/ai',
      '/projects',
      '/interviews',
      '/cloud',
      '/devops',
      '/cybersecurity',
      '/readiness',
      '/mistakes',
      '/jobs',
    ]
    for (const route of routes) {
      await page.goto(route)
      await expect(page.locator('body')).not.toHaveText(/Cannot GET|Internal Server Error/i)
      await expect(page).not.toHaveURL(/\/login/)
      await expect(page.getByRole('heading').first()).toBeVisible({ timeout: 20_000 })
    }
  })
})
