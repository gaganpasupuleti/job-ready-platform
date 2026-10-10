import fs from 'node:fs'
import path from 'node:path'

import { expect, test, type Page } from '@playwright/test'

const articles = path.resolve('../backend/content/batches/2026-10-10-visual-learning-001/articles')

const lessons = [
  {
    key: 'syl-crt-quant-percentages',
    title: 'Percentages for placement aptitude',
    article: 'crt-quant-percentages.md',
    question: 'syl-crt-q01',
    place: { track: 'crt', track_title: 'CRT / Aptitude', unit: 'quantitative', unit_title: 'Quantitative Aptitude' },
  },
  {
    key: 'syl-crt-logical-patterns',
    title: 'Number patterns in logical reasoning',
    article: 'crt-logical-patterns.md',
    question: 'syl-crt-q02',
    place: { track: 'crt', track_title: 'CRT / Aptitude', unit: 'logical', unit_title: 'Logical Reasoning' },
  },
  {
    key: 'syl-crt-verbal-meaning',
    title: 'Reading for meaning in verbal ability',
    article: 'crt-verbal-meaning.md',
    question: 'syl-crt-q03',
    place: { track: 'crt', track_title: 'CRT / Aptitude', unit: 'verbal', unit_title: 'Verbal Ability' },
  },
  {
    key: 'syl-crt-di-tables',
    title: 'Reading a simple data table',
    article: 'crt-di-tables.md',
    question: 'syl-crt-q04',
    place: { track: 'crt', track_title: 'CRT / Aptitude', unit: 'data-interpretation', unit_title: 'Data Interpretation' },
  },
  {
    key: 'syl-dsa-complexity',
    title: 'Time complexity with big-O',
    article: 'dsa-complexity.md',
    question: 'syl-dsa-q01',
    place: { track: 'dsa', track_title: 'DSA Foundations', unit: 'complexity', unit_title: 'Complexity' },
  },
  {
    key: 'syl-dsa-arrays-strings',
    title: 'Arrays and strings',
    article: 'dsa-arrays-strings.md',
    question: 'syl-dsa-q02',
    place: { track: 'dsa', track_title: 'DSA Foundations', unit: 'arrays-strings', unit_title: 'Arrays and Strings' },
  },
]

function articleParts(name: string) {
  const body = fs.readFileSync(path.join(articles, name), 'utf8')
  const image = /!\[([^\]]+)\]\(([^)\s]+) "([^"]+)"\)/.exec(body)
  if (!image) throw new Error(`missing diagram in ${name}`)
  return { body, alt: image[1], src: image[2], caption: image[3] }
}

function lessonPayload(entry: (typeof lessons)[number]) {
  const visual = articleParts(entry.article)
  return {
    key: entry.key,
    title: entry.title,
    ...entry.place,
    position: 1,
    status: 'published',
    minutes: 12,
    prerequisites: [],
    material_key: entry.article.replace(/\.md$/, ''),
    video: null,
    syllabus_position: 1,
    syllabus_total: 6,
    previous: null,
    next: null,
    material: {
      key: entry.key,
      title: entry.title,
      summary: 'A reviewed diagram sits with the worked example.',
      kind: 'article',
      level: 'beginner',
      audience: 'Fresher',
      minutes: 12,
      objectives: ['Read the diagram', 'Check the worked example'],
      prerequisites: [],
      body_md: visual.body,
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
        key: entry.question,
        stem: `Published practice ${entry.question} stays with this lesson.`,
        options: [{ key: '0', text: 'The existing checked question' }],
      },
    ],
  }
}

async function openAsStudent(page: Page) {
  await page.addInitScript(() => {
    localStorage.setItem('jrp_access_token', 'visual-learning-acceptance')
    localStorage.setItem('jrp-theme', 'light')
  })
  await page.route('**/api/v1/**', (route) => route.fulfill({ status: 200, contentType: 'application/json', body: '{}' }))
  await page.route('**/api/v1/auth/me', (route) =>
    route.fulfill({
      json: {
        id: '22222222-2222-2222-2222-222222222222',
        email: 'acceptance@example.com',
        username: 'acceptance',
        full_name: 'Acceptance Student',
        role: 'student',
        is_active: true,
        created_at: '2026-09-20T00:00:00Z',
      },
    }),
  )
  await page.route('**/api/v1/studio/syllabus/**', (route) => {
    const url = route.request().url()
    const entry = lessons.find((lesson) => url.endsWith(`/${lesson.key}`))
    if (!entry) return route.fulfill({ status: 404, body: 'missing lesson' })
    return route.fulfill({ json: lessonPayload(entry) })
  })
}

test.describe('Visual learning acceptance', () => {
  test('a signed-in student can read all six diagram lessons', async ({ page }) => {
    await openAsStudent(page)
    for (const [index, entry] of lessons.entries()) {
      const visual = articleParts(entry.article)
      await page.goto(`/learn/syllabus/${entry.key}`)
      const diagram = page.getByRole('img', { name: visual.alt })
      await expect(diagram).toBeVisible({ timeout: 20_000 })
      await expect.poll(async () => diagram.evaluate((node: HTMLImageElement) => node.naturalWidth)).toBeGreaterThan(0)
      await expect(page.getByText(visual.caption)).toBeVisible()
      await expect(diagram.locator('xpath=ancestor::p')).toHaveCount(0)
      await expect(page.getByText(`Published practice ${entry.question} stays with this lesson.`)).toBeVisible()
      await expect(page.getByRole('button', { name: 'View larger' })).toBeVisible()
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)
      expect(overflow).toBeLessThanOrEqual(1)
      if (index === 0) {
        await page.getByRole('button', { name: 'Switch to dark mode' }).first().click()
        await expect(page.locator('html')).toHaveClass(/dark/)
        await expect(diagram).toBeVisible()
        await page.getByRole('button', { name: 'Switch to light mode' }).first().click()
      }
    }
  })
})
