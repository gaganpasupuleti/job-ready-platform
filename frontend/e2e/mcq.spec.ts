import { expect, test } from '@playwright/test'

import { loadManifest, loginAs } from './helpers'

const fixtures = loadManifest()

test.describe('MCQ practice and exam', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, fixtures.users.student)
  })

  test('aptitude practice session starts and shows a question', async ({ page }) => {
    await page.goto('/practice/aptitude')
    await expect(page.getByRole('heading', { name: /aptitude/i }).first()).toBeVisible()
    await page.getByRole('button', { name: fixtures.mcq_topic.name, exact: true }).click()
    await page.getByRole('button', { name: /^easy$/i }).click()
    await page.getByRole('combobox').selectOption('5')
    await page.getByRole('button', { name: /^practice$/i }).click()
    await page.getByRole('button', { name: /start session/i }).click()
    await expect(page.getByText(/no questions found/i)).toHaveCount(0)
    await expect(page).toHaveURL(/\/practice\/sessions\//, { timeout: 20_000 })
    await expect(page.getByText(/question|option|submit|clear/i).first()).toBeVisible({
      timeout: 20_000,
    })
  })

  test('exam mode can be selected from aptitude catalog', async ({ page }) => {
    await page.goto('/practice/aptitude')
    await page.getByRole('button', { name: /^exam$/i }).click()
    await expect(page.getByText(/answers stay hidden|answers and explanations are hidden/i)).toBeVisible()
  })

  test('active exam can be resumed from recent practice', async ({ page }) => {
    await page.goto('/practice/aptitude')
    await page.getByRole('button', { name: fixtures.mcq_topic.name, exact: true }).click()
    await page.getByRole('button', { name: /^easy$/i }).click()
    await page.getByRole('combobox').selectOption('5')
    await page.getByRole('button', { name: /^exam$/i }).click()
    await page.getByRole('button', { name: /start session/i }).click()
    await expect(page).toHaveURL(/\/practice\/sessions\//, { timeout: 20_000 })
    const sessionUrl = page.url()
    await page.goto('/practice/aptitude')
    await expect(page.getByRole('heading', { name: /aptitude/i }).first()).toBeVisible()
    const resume = page.getByRole('link', { name: /^resume$/i }).first()
    await expect(resume).toBeVisible({ timeout: 15_000 })
    await resume.click()
    await expect(page).toHaveURL(/\/practice\/sessions\//, { timeout: 15_000 })
    expect(page.url().replace(/\/$/, '')).toBe(sessionUrl.replace(/\/$/, ''))
    await expect(page.getByText(/exam mode|time left|question navigator/i).first()).toBeVisible({
      timeout: 15_000,
    })
  })

  test('exam selection autosaves and shows answered progress', async ({ page }) => {
    await page.goto('/practice/aptitude')
    await page.getByRole('button', { name: fixtures.mcq_topic.name, exact: true }).click()
    await page.getByRole('button', { name: /^easy$/i }).click()
    await page.getByRole('combobox').selectOption('5')
    await page.getByRole('button', { name: /^exam$/i }).click()
    await page.getByRole('button', { name: /start session/i }).click()
    await expect(page).toHaveURL(/\/practice\/sessions\/[^/]+$/, { timeout: 20_000 })
    await expect(page.getByRole('group', { name: /answer options/i })).toBeVisible({
      timeout: 20_000,
    })
    const option = page.getByRole('group', { name: /answer options/i }).getByRole('button').first()
    await option.click()
    await expect(page.getByText(/^saved$/i)).toBeVisible({ timeout: 10_000 })
    await expect(page.getByText(/% answered/i)).toBeVisible()
    await expect(page.getByText(/time left:/i)).toBeVisible()
    await page.getByRole('button', { name: /submit exam/i }).click()
    await expect(page.getByRole('button', { name: /confirm submit/i })).toBeVisible()
  })

  test('confirm submit after pending autosave reaches results', async ({ page }) => {
    await page.goto('/practice/aptitude')
    await page.getByRole('button', { name: fixtures.mcq_topic.name, exact: true }).click()
    await page.getByRole('button', { name: /^easy$/i }).click()
    await page.getByRole('combobox').selectOption('5')
    await page.getByRole('button', { name: /^exam$/i }).click()
    await page.getByRole('button', { name: /start session/i }).click()
    await expect(page).toHaveURL(/\/practice\/sessions\/[^/]+$/, { timeout: 20_000 })
    const sessionUrl = page.url()
    const sessionId = sessionUrl.match(/\/practice\/sessions\/([^/]+)/)?.[1]
    expect(sessionId).toBeTruthy()

    await expect(page.getByRole('group', { name: /answer options/i })).toBeVisible({
      timeout: 20_000,
    })
    // Click option then immediately open confirm (pending autosave path)
    await page.getByRole('group', { name: /answer options/i }).getByRole('button').first().click()
    await page.getByRole('button', { name: /submit exam/i }).click()
    await page.getByRole('button', { name: /confirm submit/i }).click()
    await expect(page).toHaveURL(new RegExp(`/practice/sessions/${sessionId}/results`), {
      timeout: 30_000,
    })
    await expect(page.getByRole('heading', { name: /practice complete/i })).toBeVisible({
      timeout: 15_000,
    })
    const scoreCard = page.locator('div').filter({ has: page.getByText(/^score$/i) }).filter({
      has: page.getByText(/^\d+\s*\/\s*\d+$/),
    })
    await expect(scoreCard.first()).toBeVisible()
    await expect(page.getByText(/^accuracy$/i)).toBeVisible()
  })

  test('refresh restores multi-select autosave', async ({ page, request }) => {
    await page.goto('/practice/aptitude')
    const token = await page.evaluate(() => localStorage.getItem('jrp_access_token'))
    expect(token).toBeTruthy()
    const api = process.env.E2E_API_URL || 'http://127.0.0.1:8000/api/v1'
    const headers = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }

    const catalog = await request.get(`${api}/practice/catalog`, { headers })
    expect(catalog.ok()).toBeTruthy()
    const catalogJson = await catalog.json()
    const category = catalogJson.domains[0].categories[0]
    const topic = category.topics[0]
    const created = await request.post(`${api}/practice/sessions`, {
      headers,
      data: {
        category_id: category.id,
        topic_id: topic.id,
        question_count: 2,
        mode: 'exam',
        duration_minutes: 30,
      },
    })
    expect(created.ok()).toBeTruthy()
    const session = await created.json()
    const q = await request.get(`${api}/practice/sessions/${session.id}/questions/1`, { headers })
    expect(q.ok()).toBeTruthy()
    const question = await q.json()
    const options = question.question.options as { id: string }[]
    expect(options.length).toBeGreaterThanOrEqual(2)
    const selected = [options[0].id, options[1].id]
    const autosave = await request.post(
      `${api}/practice/sessions/${session.id}/questions/1/autosave`,
      {
        headers,
        data: {
          selected_option_ids: selected,
          marked_for_review: true,
          time_spent_seconds: 2,
        },
      },
    )
    expect(autosave.ok()).toBeTruthy()

    await page.goto(`/practice/sessions/${session.id}`)
    await expect(page.getByRole('group', { name: /answer options/i })).toBeVisible({
      timeout: 20_000,
    })
    const optionButtons = page.getByRole('group', { name: /answer options/i }).getByRole('button')
    await expect(optionButtons.nth(0)).toHaveAttribute('aria-pressed', 'true')
    await expect(optionButtons.nth(1)).toHaveAttribute('aria-pressed', 'true')
    const optionCount = await optionButtons.count()
    if (optionCount > 2) {
      await expect(optionButtons.nth(2)).toHaveAttribute('aria-pressed', 'false')
    }
    await expect(page.getByText(/% answered/i)).toBeVisible()
  })
})
