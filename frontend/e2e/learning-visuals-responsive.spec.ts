import fs from 'node:fs'
import path from 'node:path'

import { expect, test, type Page } from '@playwright/test'

const shotDir = path.resolve('e2e-artifacts/learning-visuals')
const articles = path.resolve('../backend/content/batches/2026-09-14-syllabus-001/articles')

function article(name: string) {
  return fs.readFileSync(path.join(articles, name), 'utf8')
}

function lesson(
  key: string,
  title: string,
  body: string,
  questionKey: string,
  place: { track: string; track_title: string; unit: string; unit_title: string } = {
    track: 'crt',
    track_title: 'CRT / Aptitude',
    unit: 'quantitative',
    unit_title: 'Quantitative Aptitude',
  },
) {
  return {
    key,
    title,
    track: place.track,
    track_title: place.track_title,
    unit: place.unit,
    unit_title: place.unit_title,
    position: 1,
    status: 'published',
    minutes: 12,
    prerequisites: [],
    material_key: key,
    video: null,
    syllabus_position: 1,
    syllabus_total: 6,
    previous: null,
    next: null,
    material: {
      key,
      title,
      summary: 'A reviewed diagram sits with the worked example.',
      kind: 'article',
      level: 'beginner',
      audience: 'Fresher',
      minutes: 12,
      objectives: ['Read the diagram', 'Check the worked example'],
      prerequisites: [],
      body_md: body,
      examples: [],
      exercises: [],
      summary_md: 'Use the diagram, then the worked example.',
      sources: [],
      families: [],
      skills: [],
      version: 2,
      updated_at: '2026-10-10T00:00:00Z',
      has_download: false,
      read: false,
      related_pack: null,
    },
    practice: [
      {
        key: questionKey,
        stem: 'Which published practice item belongs with this lesson?',
        options: [{ key: '0', text: 'The existing checked question' }],
      },
    ],
  }
}

async function shot(page: Page, name: string) {
  fs.mkdirSync(shotDir, { recursive: true })
  const file = path.join(shotDir, `${name}.png`)
  await page.screenshot({ path: file, fullPage: true })
  return file
}

async function openAsStudent(page: Page) {
  await page.addInitScript(() => {
    localStorage.setItem('jrp_access_token', 'visual-learning-test')
    localStorage.setItem('jrp-theme', 'light')
  })
  await page.route('**/api/v1/**', (route) => route.fulfill({ status: 200, contentType: 'application/json', body: '{}' }))
  await page.route('**/api/v1/auth/me', (route) =>
    route.fulfill({
      json: {
        id: '11111111-1111-1111-1111-111111111111',
        email: 'visual@example.com',
        username: 'visual',
        full_name: 'Visual Student',
        role: 'student',
        is_active: true,
        created_at: '2026-09-20T00:00:00Z',
      },
    }),
  )
  await page.route('**/api/v1/studio/syllabus/**', (route) => {
    const url = route.request().url()
    if (url.includes('/practice/')) {
      return route.fulfill({
        json: {
          correct: true,
          selected: ['0'],
          correct_keys: ['0'],
          explanation: 'The published question stays attached to this lesson.',
          options: [],
          competence: false,
          note: 'Reading practice only.',
        },
      })
    }
    if (url.endsWith('/syl-dsa-arrays-strings')) {
      return route.fulfill({
        json: lesson(
          'syl-dsa-arrays-strings',
          'Arrays and strings',
          article('dsa-arrays-strings.md'),
          'syl-dsa-q02',
          {
            track: 'dsa',
            track_title: 'DSA Foundations',
            unit: 'arrays-strings',
            unit_title: 'Arrays and Strings',
          },
        ),
      })
    }
    if (url.endsWith('/syl-visual-safety')) {
      return route.fulfill({
        json: lesson(
          'syl-visual-safety',
          'Renderer checks',
          [
            '## Understand',
            '',
            'Unsafe image syntax stays text.',
            '',
            '## Visualize',
            '',
            '![Format check png](/learning-visuals/crt/format-check.png "PNG caption")',
            '',
            '![Format check webp](/learning-visuals/crt/format-check.webp "WebP caption")',
            '',
            '![Missing diagram of a quarter](/learning-visuals/crt/missing-diagram.svg "Missing caption")',
            '',
            '![Blocked script image](javascript:alert(1))',
            '',
            '![Blocked data image](data:image/svg+xml,x)',
            '',
            '| Step | Result |',
            '| --- | --- |',
            '| Sale | 180 |',
            '',
            '```text',
            '240 - 60 = 180',
            '```',
          ].join('\n'),
          'syl-crt-q01',
        ),
      })
    }
    return route.fulfill({
      json: lesson(
        'syl-crt-quant-percentages',
        'Percentages for placement aptitude',
        article('crt-quant-percentages.md'),
        'syl-crt-q01',
      ),
    })
  })
}

test.describe('Learning visuals', () => {
  test('CRT and DSA lessons show diagrams on the published page', async ({ page }) => {
    await openAsStudent(page)
    await page.goto('/learn/syllabus/syl-crt-quant-percentages')
    const diagram = page.getByRole('img', { name: /four equal parts/i })
    await expect(diagram).toBeVisible({ timeout: 20_000 })
    await expect(page.getByText('The sale price is 180.')).toBeVisible()
    await expect(page.getByRole('button', { name: 'View larger' })).toBeVisible()
    const project = test.info().project.name
    await shot(page, `crt-percentages-light-${project}`)

    await page.getByRole('button', { name: 'Switch to dark mode' }).first().click()
    await expect(page.locator('html')).toHaveClass(/dark/)
    await shot(page, `crt-percentages-dark-${project}`)

    await page.getByRole('button', { name: 'View larger' }).click()
    await expect(page.getByRole('dialog')).toBeVisible()
    await page.getByRole('button', { name: 'Close' }).click()
    await expect(page.getByRole('dialog')).toBeHidden()

    await page.getByRole('radio').check()
    await page.getByRole('button', { name: /check answer/i }).click()
    await expect(page.getByText('The published question stays attached to this lesson.')).toBeVisible()

    await page.goto('/learn/syllabus/syl-dsa-arrays-strings')
    await expect(page.getByRole('img', { name: /left on index 1/i })).toBeVisible({ timeout: 20_000 })
    await expect(page.getByRole('cell', { name: '[d, c, b, a]' })).toBeVisible()
    await shot(page, `dsa-arrays-light-${project}`)
  })

  test('approved rasters render and unsafe image URLs do not', async ({ page }) => {
    await openAsStudent(page)
    await page.goto('/learn/syllabus/syl-visual-safety')
    const png = page.getByRole('img', { name: 'Format check png' })
    const webp = page.getByRole('img', { name: 'Format check webp' })
    await expect(png).toBeVisible({ timeout: 20_000 })
    await expect(webp).toBeVisible()
    await expect.poll(async () => png.evaluate((node: HTMLImageElement) => node.naturalWidth)).toBeGreaterThan(0)
    await expect.poll(async () => webp.evaluate((node: HTMLImageElement) => node.naturalWidth)).toBeGreaterThan(0)
    await expect(page.getByRole('status').filter({ hasText: 'Diagram unavailable. Missing diagram of a quarter' })).toBeVisible()
    await expect(page.getByText('Blocked script image')).toBeVisible()
    await expect(page.getByText('Blocked data image')).toBeVisible()
    await expect(page.locator('img[src^="javascript:"], img[src^="data:"]')).toHaveCount(0)
    await expect(page.getByRole('cell', { name: '180' })).toBeVisible()
    await expect(page.locator('pre')).toContainText('240 - 60 = 180')
    await shot(page, `renderer-safety-${test.info().project.name}`)
  })
})
