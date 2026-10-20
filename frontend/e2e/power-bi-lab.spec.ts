/**
 * Mock-auth lab UI checks. Static assets only; does not verify Power BI Desktop rebuild.
 */
import { expect, test, type Page, type Route } from '@playwright/test'

const OUT = 'e2e-artifacts/power-bi-lab'
const LAB = '/reports/executive-sales-toast/lab'

const USER = {
  id: 'student-1',
  email: 'student@example.com',
  username: 'preview',
  full_name: 'Preview Student',
  role: 'student',
  is_active: true,
  created_at: '2026-01-01T00:00:00Z',
}

function json(route: Route, status: number, body: unknown) {
  return route.fulfill({
    status,
    contentType: 'application/json',
    body: JSON.stringify(body),
  })
}

async function installMockAuth(page: Page) {
  await page.addInitScript(() => localStorage.setItem('jrp_access_token', 'preview-token'))
  await page.route('**/*', async (route) => {
    const url = new URL(route.request().url())
    const local = url.hostname === '127.0.0.1' || url.hostname === 'localhost'
    if (local && url.pathname === '/api/v1/auth/me') return json(route, 200, USER)
    if (url.pathname.startsWith('/api/')) return json(route, 200, {})
    await route.continue()
  })
}

test.describe('Power BI build lab', () => {
  test('guided lab navigation, downloads, progress', async ({ page }, testInfo) => {
    await installMockAuth(page)
    await page.goto(LAB)
    await expect(page.getByRole('heading', { name: /Build lab/i })).toBeVisible()

    await page.getByRole('tab', { name: 'Guided build' }).click()
    await expect(page.getByRole('article')).toBeVisible()
    await page.getByRole('button', { name: /Mark complete/i }).click()
    await expect(page.getByRole('button', { name: /Completed/i })).toBeVisible()

    const downloadPromise = page.waitForEvent('download')
    await page.getByRole('link', { name: /Datasets/i }).click()
    const download = await downloadPromise
    expect(download.suggestedFilename()).toMatch(/datasets\.zip/i)

    await page.getByRole('tab', { name: 'Resources' }).click()
    await expect(page.getByRole('link', { name: 'Download' }).first()).toBeVisible()

    await page.getByRole('tab', { name: 'Final validation' }).click()
    await page.getByRole('button', { name: /Reset progress/i }).click()

    await page.screenshot({
      path: testInfo.project.name === 'mobile' ? `${OUT}/lab-mobile.png` : `${OUT}/lab-desktop.png`,
      fullPage: true,
    })
  })

  test('failed workshop asset surfaces error', async ({ page }) => {
    await installMockAuth(page)
    await page.route('**/workshop-content.json', (route) => route.fulfill({ status: 500, body: 'fail' }))
    await page.goto(LAB)
    await expect(page.getByText(/Could not load workshop/i)).toBeVisible()
  })
})
