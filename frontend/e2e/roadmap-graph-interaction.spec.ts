/**
 * Live roadmap graph interactions (drag, edges, lock, reset, viewport stability).
 */
import { expect, test } from '@playwright/test'

import { loadManifest, loginAs } from './helpers'
import { parseViewportTransform, viewportTransformsClose } from './roadmap-viewport'

const fixtures = loadManifest()
const SAMPLE_SLUG = 'api-design'

async function viewportTransform(page: import('@playwright/test').Page) {
  return page.locator('.ors-canvas .react-flow__viewport').getAttribute('style')
}

async function firstEdgePath(page: import('@playwright/test').Page) {
  return page.locator('.ors-canvas .react-flow__edge-path').first().getAttribute('d')
}

async function draggableTopicNode(page: import('@playwright/test').Page) {
  const node = page.locator('.ors-canvas .react-flow__node.draggable').filter({
    has: page.locator('.ors-node--topic'),
  }).first()
  await expect(node).toBeVisible({ timeout: 30_000 })
  return node
}

async function expectViewportStable(page: import('@playwright/test').Page, baseline: string | null) {
  const during = await viewportTransform(page)
  expect(
    viewportTransformsClose(baseline, during),
    `viewport moved: before=${baseline} during=${during}`,
  ).toBe(true)
}

test.describe('Roadmap graph interaction (live)', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, fixtures.users.student)
    await page.setViewportSize({ width: 1366, height: 900 })
    await page.goto(`/roadmaps/${SAMPLE_SLUG}`)
    await expect(page.getByRole('heading', { name: /api design/i })).toBeVisible({ timeout: 30_000 })
    await expect(page.locator('.ors-canvas .react-flow')).toBeVisible({ timeout: 60_000 })
    await expect
      .poll(async () => page.locator('.ors-canvas .react-flow__node').count(), { timeout: 60_000 })
      .toBeGreaterThan(0)
    await expect(page.locator('.ors-canvas .react-flow__edge-path').first()).toBeVisible({
      timeout: 30_000,
    })
  })

  test('topic drag moves node and attached edge geometry', async ({ page }) => {
    const node = await draggableTopicNode(page)
    const edgeBefore = await firstEdgePath(page)
    expect(edgeBefore).toBeTruthy()

    const box = await node.boundingBox()
    expect(box).toBeTruthy()
    if (!box) return

    const startX = box.x + box.width / 2
    const startY = box.y + box.height / 2
    await page.mouse.move(startX, startY)
    await page.mouse.down()
    await page.mouse.move(startX + 72, startY + 48, { steps: 12 })
    await page.mouse.up()

    const boxAfter = await node.boundingBox()
    expect(boxAfter).toBeTruthy()
    if (!boxAfter) return
    expect(Math.abs(boxAfter.x - box.x) + Math.abs(boxAfter.y - box.y)).toBeGreaterThan(8)

    await expect
      .poll(async () => firstEdgePath(page), { timeout: 10_000 })
      .not.toBe(edgeBefore)
  })

  test('lock layout blocks drag; reset restores layout', async ({ page }) => {
    const node = await draggableTopicNode(page)
    const boxOrig = await node.boundingBox()
    expect(boxOrig).toBeTruthy()
    if (!boxOrig) return

    await page.getByLabel('Lock layout').check()
    await expect(page.locator('.ors-canvas--locked')).toBeVisible()

    const startX = boxOrig.x + boxOrig.width / 2
    const startY = boxOrig.y + boxOrig.height / 2
    await page.mouse.move(startX, startY)
    await page.mouse.down()
    await page.mouse.move(startX + 80, startY + 60, { steps: 10 })
    await page.mouse.up()

    const boxLocked = await node.boundingBox()
    expect(boxLocked).toBeTruthy()
    if (!boxLocked) return
    expect(Math.abs(boxLocked.x - boxOrig.x)).toBeLessThan(4)
    expect(Math.abs(boxLocked.y - boxOrig.y)).toBeLessThan(4)

    await page.getByLabel('Lock layout').uncheck()
    await page.mouse.move(startX, startY)
    await page.mouse.down()
    await page.mouse.move(startX + 72, startY + 48, { steps: 12 })
    await page.mouse.up()
    const boxDragged = await node.boundingBox()
    expect(boxDragged).toBeTruthy()
    if (!boxDragged) return
    expect(Math.abs(boxDragged.x - boxOrig.x) + Math.abs(boxDragged.y - boxOrig.y)).toBeGreaterThan(8)

    await page.getByRole('button', { name: 'Reset layout to original' }).click()
    await expect
      .poll(async () => {
        const b = await node.boundingBox()
        if (!b) return 999
        return Math.abs(b.x - boxOrig.x) + Math.abs(b.y - boxOrig.y)
      }, { timeout: 15_000 })
      .toBeLessThan(6)
  })

  test('viewport transform stable when article panel opens', async ({ page }) => {
    const before = await viewportTransform(page)
    expect(before).toBeTruthy()
    const beforeParsed = parseViewportTransform(before)
    expect(beforeParsed).toBeTruthy()

    const topicNode = page.locator('.ors-canvas .react-flow__node.draggable').filter({
      has: page.locator('.ors-node--topic'),
    }).first()
    await expect(topicNode).toBeVisible({ timeout: 20_000 })
    await topicNode.click()
    await expect(page.getByRole('heading', { level: 2 })).toBeVisible({ timeout: 20_000 })

    await expectViewportStable(page, before)

    await page.locator('.ors-panel--desktop').getByRole('button', { name: 'Close' }).click()
    await expect(page.getByRole('heading', { level: 2 })).toBeHidden({ timeout: 10_000 })
    await expectViewportStable(page, before)
  })
})
