/**
 * Dev-only screenshot capture for roadmap preview delivery.
 * Requires: npm run dev on 5185, and a reachable API for login (or seeded local).
 */
import { chromium, devices } from '@playwright/test'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const outDir = path.resolve(__dirname, '../../docs/screenshots')
const base = process.env.ROADMAP_PREVIEW_URL ?? 'http://127.0.0.1:5185'

async function login(page) {
  await page.goto(`${base}/login`)
  await page.getByLabel(/email/i).fill('admin@jobready.dev')
  await page.getByLabel(/password/i).fill('Admin123!')
  await page.getByRole('button', { name: /sign in|log in|login/i }).click()
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 20000 })
}

async function shot(page, name) {
  await page.goto(`${base}/dev/roadmap-preview`)
  await page.waitForTimeout(1500)
  await page.screenshot({ path: path.join(outDir, name), fullPage: true })
}

async function main() {
  const browser = await chromium.launch({ headless: true })
  const desktop = await browser.newPage({ viewport: { width: 1440, height: 900 } })
  try {
    await login(desktop)
    await shot(desktop, 'desktop-map.png')
    await desktop.locator('.rm-toolbar').getByRole('button', { name: 'Start here' }).click()
    await desktop.waitForTimeout(500)
    await desktop.screenshot({
      path: path.join(outDir, 'desktop-start-here-sql.png'),
      fullPage: true,
    })
    await desktop.locator('.rm-toolbar').getByRole('button', { name: 'List', exact: true }).click()
    await desktop.waitForTimeout(400)
    await desktop.screenshot({ path: path.join(outDir, 'desktop-list.png'), fullPage: true })

    const state = await desktop.context().storageState()
    const tabletCtx = await browser.newContext({
      viewport: { width: 820, height: 1100 },
      storageState: state,
    })
    const tpage = await tabletCtx.newPage()
    await shot(tpage, 'tablet.png')
    await tpage.close()
    await tabletCtx.close()

    const mobileCtx = await browser.newContext({
      ...devices['iPhone 13'],
      storageState: state,
    })
    const mpage = await mobileCtx.newPage()
    await shot(mpage, 'mobile-list.png')
    await mpage.close()
    await mobileCtx.close()

    console.log('screenshots written to', outDir)
  } catch (err) {
    console.error('screenshot capture blocked:', err instanceof Error ? err.message : err)
    process.exitCode = 2
  } finally {
    await desktop.close()
    await browser.close()
  }
}

await main()
