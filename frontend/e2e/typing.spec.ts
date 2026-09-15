import { expect, test, type Page } from '@playwright/test'
import { advance, createSession, indentAt, metrics } from '../src/features/typing/engine'

// Auth is fixture-backed; actual typing runs in the app without backend services.
async function openStudio(page: Page) {
  await page.route('**/api/v1/auth/me', (route) =>
    route.fulfill({
      json: {
        id: 'typing-a',
        email: 'a@example.test',
        username: 'learner',
        full_name: 'Typing Learner',
        role: 'student',
        is_active: true,
      },
    }),
  )
  await page.addInitScript(() => localStorage.setItem('jrp_access_token', 'typing-fixture-token'))
  await page.goto('/practice/typing')
  await expect(page.getByRole('heading', { name: 'Find your typing rhythm.' })).toBeVisible()
}
async function custom(page: Page, text: string) {
  await page.getByRole('button', { name: 'Custom', exact: true }).click()
  await page.getByLabel('Your practice passage').fill(text)
  await page.getByRole('button', { name: 'Use this passage' }).click()
}

test('engine: final snapshot, corrections, deadline, idle and indentation', () => {
  let s = createSession('abcde')
  s = advance(s, { type: 'insert', text: 'x', now: 0 })
  s = advance(s, { type: 'backspace', now: 100 })
  s = advance(s, { type: 'insert', text: 'abcd', now: 500 })
  s = advance(s, { type: 'insert', text: 'e', now: 60000 })
  expect(s.phase).toBe('finished')
  expect(metrics(s, 80000)).toMatchObject({
    wpm: 1,
    accuracy: 83,
    errors: 1,
    elapsedMs: 60000,
    progress: 100,
  })
  expect(advance(s, { type: 'backspace', now: 90000 })).toBe(s)
  let timed = advance(createSession('abcdef', 30), { type: 'insert', text: 'a', now: 0 })
  timed = advance(timed, { type: 'insert', text: 'b', now: 30001 })
  expect(timed.input).toBe('a')
  expect(timed.endedAt).toBe(30000)
  expect(indentAt('x\n    y', 2)).toBe('    ')
  expect(indentAt('x    y', 1)).toBe('')
  expect(indentAt('\ty', 0)).toBe('\t')
  const idle = createSession('abc', 30)
  expect(advance(idle, { type: 'tick', now: 90000 })).toBe(idle)
})

test('completion, correction accuracy, persistence and clear', async ({ page }) => {
  await openStudio(page)
  await custom(page, 'abc')
  await page.keyboard.type('x')
  await page.keyboard.press('Backspace')
  await page.keyboard.type('abc', { delay: 100 })
  await expect(page.getByRole('heading', { name: 'One session stronger.' })).toBeVisible()
  await expect(page.getByTestId('typing-accuracy')).toHaveText('75%')
  await expect(page.getByTestId('typing-errors')).toHaveText('1')
  await expect(page.locator('.typing-history tbody tr')).toHaveCount(1)
  await page.reload()
  await expect(page.locator('.typing-history tbody tr')).toHaveCount(1)
  await page.getByRole('button', { name: 'Clear history' }).click()
  await expect(page.locator('.typing-history tbody tr')).toHaveCount(0)
})

test('code Enter and Tab, language selection, retry, no execution requests', async ({ page }) => {
  await openStudio(page)
  const requests: string[] = []
  page.on('request', (r) => {
    if (/\/api\/.*(submit|execute|run)/.test(r.url())) requests.push(r.url())
  })
  await page.getByRole('button', { name: 'Code', exact: true }).click()
  await page.getByLabel('Code language').selectOption('SQL')
  await expect(page.getByTestId('typing-passage')).toContainText('SELECT')
  await page.getByLabel('Code language').selectOption('Python')
  const plain = (await page.getByTestId('typing-passage').innerText()).replaceAll('↵', '')
  await page.getByLabel('Typing input', { exact: true }).focus()
  for (const [i, line] of plain.split('\n').entries()) {
    if (i) await page.keyboard.press('Enter')
    if (line.startsWith('    ')) {
      await page.keyboard.press('Tab')
      await page.keyboard.type(line.slice(4))
    } else await page.keyboard.type(line)
  }
  await expect(page.getByRole('heading', { name: 'One session stronger.' })).toBeVisible()
  await expect(page.getByTestId('typing-accuracy')).toHaveText('100%')
  expect(requests).toEqual([])
  await page.getByRole('button', { name: 'Try again' }).click()
  await expect(page.getByLabel('Typing input', { exact: true })).toHaveValue('')
})

test('deadline expires without input and saves once', async ({ page }) => {
  await page.clock.install()
  await openStudio(page)
  await page.getByLabel('Session duration').selectOption('30')
  await page.getByLabel('Typing input', { exact: true }).focus()
  await page.keyboard.type('l')
  await expect(page.getByLabel('Session duration')).toBeDisabled()
  await page.clock.fastForward(31000)
  await expect(page.getByRole('heading', { name: 'One session stronger.' })).toBeVisible()
  await expect(page.getByTestId('typing-time')).toHaveText('0s')
  await page.clock.fastForward(30000)
  await expect(page.locator('.typing-history tbody tr')).toHaveCount(1)
})

test('custom editing, paste guard, keyboard escape and mobile fit', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await openStudio(page)
  await custom(page, 'hello world')
  await expect(page.getByLabel('Typing input', { exact: true })).toHaveValue('')
  await page.getByLabel('Typing input', { exact: true }).evaluate((el) => {
    const transfer = new DataTransfer()
    transfer.setData('text/plain', 'hello world')
    const event = new ClipboardEvent('paste', {
      clipboardData: transfer,
      bubbles: true,
      cancelable: true,
    })
    el.dispatchEvent(event)
    if (!event.defaultPrevented) throw new Error('Paste not prevented')
  })
  await page.getByLabel('Typing input', { exact: true }).focus()
  await page.keyboard.press('Tab')
  await expect(page.getByLabel('Typing input', { exact: true })).not.toBeFocused()
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy()
  await page.getByRole('button', { name: 'Text', exact: true }).click()
  await page.screenshot({ path: 'test-results/typing-mobile.png', fullPage: true })
})

test('account isolation and malformed history', async ({ page }) => {
  await openStudio(page)
  await custom(page, 'ab')
  await page.keyboard.type('ab')
  await expect(page.locator('.typing-history tbody tr')).toHaveCount(1)
  await page.route('**/api/v1/auth/me', (route) =>
    route.fulfill({
      json: {
        id: 'typing-b',
        email: 'b@example.test',
        username: 'b',
        role: 'student',
        is_active: true,
      },
    }),
  )
  await page.reload()
  await expect(page.getByRole('heading', { name: 'Find your typing rhythm.' })).toBeVisible()
  await expect(page.locator('.typing-history tbody tr')).toHaveCount(0)
  await page.evaluate(() =>
    localStorage.setItem('jr:typing:v1:typing-b', '[null,{"id":"invalid"}]'),
  )
  await page.reload()
  await expect(page.getByRole('heading', { name: 'Find your typing rhythm.' })).toBeVisible()
  await expect(page.locator('.typing-history tbody tr')).toHaveCount(0)
})

test('storage failure still allows results; light and dark screenshots', async ({ page }) => {
  await openStudio(page)
  await page.screenshot({ path: 'test-results/typing-desktop.png', fullPage: true })
  await page.getByRole('button', { name: 'Use dark practice theme' }).click()
  await page.screenshot({ path: 'test-results/typing-dark.png', fullPage: true })
  await custom(page, 'ab')
  await page.evaluate(() => {
    Storage.prototype.setItem = () => {
      throw new Error('quota')
    }
  })
  await page.keyboard.type('ab')
  await expect(page.getByRole('heading', { name: 'One session stronger.' })).toBeVisible()
  await expect(page.getByText('Browser storage is unavailable.', { exact: false })).toBeVisible()
})

test('typing route requires authentication', async ({ page }) => {
  await page.goto('/practice/typing')
  await expect(page).toHaveURL(/\/login/)
})

test('history storage: ownership, retry idempotency, retention, corruption and quota failure', async () => {
  const { readHistory, saveResult, clearHistory } = await import('../src/features/typing/history')
  const values = new Map<string, string>()
  const storage = {
    getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, value: string) => {
      values.set(key, value)
    },
    removeItem: (key: string) => {
      values.delete(key)
    },
  }
  Object.defineProperty(globalThis, 'localStorage', { configurable: true, value: storage })
  try {
    const result = {
      id: 'run-1',
      date: '2026-09-15T00:00:00Z',
      mode: 'text' as const,
      label: 'Foundation',
      seconds: 60,
      wpm: 45,
      accuracy: 95,
      errors: 3,
      elapsedMs: 60000,
    }
    expect(saveResult('a', result)).toBe(true)
    expect(saveResult('a', result)).toBe(true)
    expect(readHistory('a')).toHaveLength(1)
    expect(readHistory('b')).toEqual([])
    for (let i = 0; i < 60; i++) saveResult('a', { ...result, id: `run-${i}` })
    expect(readHistory('a')).toHaveLength(50)
    expect(readHistory('a')[0].id).toBe('run-59')
    values.set('jr:typing:v1:b', '[null, {"id":"bad"}]')
    expect(readHistory('b')).toEqual([])
    values.set('jr:typing:v1:b', 'broken-json')
    expect(readHistory('b')).toEqual([])
    expect(clearHistory('a')).toBe(true)
    storage.setItem = () => {
      throw new Error('quota')
    }
    expect(saveResult('a', result)).toBe(false)
  } finally {
    Reflect.deleteProperty(globalThis, 'localStorage')
  }
})
