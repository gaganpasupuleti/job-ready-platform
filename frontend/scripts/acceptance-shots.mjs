/**
 * Lean authenticated acceptance screenshots (desktop + 390px).
 * Avoids Playwright test runner hang/buffering issues on overloaded hosts.
 */
import { chromium } from '@playwright/test'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const root = path.resolve(__dirname, '..')
const outDir = path.join(root, 'e2e-artifacts', 'acceptance-shots')
const baseURL = (process.env.E2E_BASE_URL || 'http://127.0.0.1:5180').trim()
const apiURL = (process.env.E2E_API_URL || 'http://127.0.0.1:8020').trim().replace(/\/$/, '')
const email = process.env.E2E_EMAIL || 'e2e.student@jobready.dev'
const password = process.env.E2E_PASSWORD || 'E2eStudent123!'

fs.mkdirSync(outDir, { recursive: true })

function log(msg) {
  process.stdout.write(`${msg}\n`)
}

async function loginToken() {
  const res = await fetch(`${apiURL}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!res.ok) throw new Error(`login HTTP ${res.status}: ${await res.text()}`)
  const body = await res.json()
  if (!body.access_token) throw new Error('missing access_token')
  return body.access_token
}

async function shot(page, name) {
  const file = path.join(outDir, `${name}.png`)
  await page.screenshot({ path: file, fullPage: true })
  log(`SHOT ${file}`)
  return file
}

async function attachApiProxy(context) {
  const apiOrigin = new URL(apiURL).origin
  await context.route(/\/api\/v1\//, async (route) => {
    const req = route.request()
    const url = new URL(req.url())
    const proxied =
      url.origin === apiOrigin
        ? req.url()
        : `${apiURL}${url.pathname}${url.search}`
    const response = await route.fetch({
      url: proxied,
      method: req.method(),
      headers: req.headers(),
      postData: req.postData(),
    })
    await route.fulfill({ response })
  })
}

async function withViewport(browser, size, label, token, fn) {
  const context = await browser.newContext({
    viewport: size,
    baseURL,
  })
  await attachApiProxy(context)
  await context.addInitScript((accessToken) => {
    localStorage.setItem('jrp_access_token', accessToken)
  }, token)
  const page = await context.newPage()
  page.setDefaultTimeout(45_000)
  try {
    await fn(page, label, token)
  } finally {
    await context.close()
  }
}

async function authGoto(page, _token, route) {
  await page.goto(route, { waitUntil: 'networkidle', timeout: 60_000 })
  if (page.url().includes('/login')) {
    throw new Error(`unexpected login redirect for ${route}`)
  }
}

async function runSuite(page, label, token) {
  // SQL IDE
  await authGoto(page, token, '/practice/playground/sql')
  await page.getByTestId('sql-playground-heading').waitFor({ state: 'visible', timeout: 45_000 })
  if (label === 'mobile') {
    await page.getByRole('tab', { name: 'Schema' }).click()
  } else {
    const expander = page.locator('aside button').first()
    if (await expander.count()) await expander.click({ timeout: 5_000 }).catch(() => {})
  }
  await shot(page, `sql-schema-${label}`)

  if (label === 'mobile') {
    await page.getByRole('tab', { name: 'Editor' }).click()
  }
  const runBtn = page.getByRole('button', { name: /run query/i })
  await runBtn.waitFor({ state: 'visible', timeout: 45_000 })
  await page.waitForFunction(
    () => {
      const btn = [...document.querySelectorAll('button')].find((el) =>
        /run query/i.test(el.textContent ?? ''),
      )
      return Boolean(btn && !btn.disabled)
    },
    null,
    { timeout: 45_000 },
  )
  await runBtn.click()
  await page.getByText(/not graded|does not create/i).first().waitFor({ state: 'visible', timeout: 45_000 })
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
  if (label === 'mobile') {
    await page.getByRole('tab', { name: 'Results' }).click()
  }
  await shot(page, `sql-success-${label}`)

  // Invalid query via draft restore path
  await page.evaluate(() => {
    const key = Object.keys(localStorage).find((item) => item.includes('sql-playground-draft'))
    if (key) localStorage.setItem(key, 'SELECT missing_column FROM books')
  })
  await page.reload()
  await page.getByTestId('sql-playground-heading').waitFor({ state: 'visible', timeout: 45_000 })
  if (label === 'mobile') {
    await page.getByRole('tab', { name: 'Editor' }).click()
  }
  const draftSql = 'SELECT missing_column FROM books'
  const monaco = page.locator('.monaco-editor textarea').first()
  if (await monaco.count()) {
    await monaco.click({ force: true })
    await monaco.fill(draftSql)
  }
  await page.getByRole('button', { name: /run query/i }).click()
  await page.getByRole('alert').first().waitFor({ state: 'visible', timeout: 45_000 })
  await shot(page, `sql-error-${label}`)

  // Python locked
  await authGoto(page, token, '/practice/python')
  await page.getByText('Python — Coming soon').waitFor({ state: 'visible' })
  if ((await page.locator('.monaco-editor').count()) !== 0) throw new Error('monaco mounted on locked python')
  await shot(page, `python-locked-${label}`)

  // Locked assignment
  await authGoto(page, token, '/learn/assignments/py-assign-exceptions')
  await page.getByText(/unavailable|locked/i).first().waitFor({ state: 'visible' })
  await shot(page, `assignment-python-locked-${label}`)

  // Non-python assignment
  await authGoto(page, token, '/learn/assignments/da-assign-paid-totals')
  await page.getByRole('button', { name: /save draft/i }).waitFor({ state: 'visible' })
  await shot(page, `assignment-sql-available-${label}`)

  // Syllabus + practice
  await authGoto(page, token, '/learn/syllabus')
  await page.getByRole('heading', { name: 'Syllabus' }).waitFor({ state: 'visible' })
  await shot(page, `syllabus-index-${label}`)

  await authGoto(page, token, '/learn/syllabus/syl-crt-quant-percentages')
  await page.locator('header h1').first().waitFor({ state: 'visible' })
  const radio = page.getByRole('radio').first()
  if (await radio.count()) {
    await radio.check()
    await page.getByRole('button', { name: /check answer/i }).click()
    await page.getByText(/correct|not quite/i).first().waitFor({ state: 'visible', timeout: 20_000 })
  }
  await shot(page, `syllabus-lesson-practice-${label}`)
}

async function main() {
  log(`BASE ${baseURL}`)
  log(`API ${apiURL}`)
  const token = await loginToken()
  log('AUTH ok')
  const browser = await chromium.launch({ headless: true })
  try {
    await withViewport(browser, { width: 1440, height: 900 }, 'desktop', token, (page, label) =>
      runSuite(page, label, token),
    )
    await withViewport(browser, { width: 390, height: 844 }, 'mobile', token, (page, label) =>
      runSuite(page, label, token),
    )
  } finally {
    await browser.close()
  }
  log('ACCEPTANCE_SHOTS_OK')
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
