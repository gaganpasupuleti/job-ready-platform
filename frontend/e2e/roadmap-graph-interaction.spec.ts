/**
 * Live roadmap graph interactions (drag, edges, lock, reset, viewport stability).
 */
import { expect, test } from '@playwright/test'

import { loadManifest, loginAs } from './helpers'
import {
  edgePathD,
  expectViewportStableThroughPanelResize,
  nodeTranslate,
  pickTopicWithOutgoingEdge,
  topicNodeLocator,
  viewportTransform,
  waitForNodeTranslateChange,
  waitForRoadmapViewportSettled,
} from './roadmap-graph-helpers'
import { viewportTransformsClose } from './roadmap-viewport'

const fixtures = loadManifest()
const SAMPLE_SLUG = 'api-design'

test.describe('Roadmap graph interaction (live)', () => {
  test.beforeEach(async ({ page, request }) => {
    await loginAs(page, fixtures.users.student)
    await page.setViewportSize({ width: 1366, height: 900 })
    await page.goto(`/roadmaps/${SAMPLE_SLUG}`)
    await expect(page.getByRole('heading', { name: /api design/i })).toBeVisible({ timeout: 30_000 })
    await expect(page.locator('.ors-canvas .react-flow')).toBeVisible({ timeout: 60_000 })
    await expect
      .poll(async () => page.locator('.ors-canvas .react-flow__node').count(), { timeout: 60_000 })
      .toBeGreaterThan(0)
    const pick = await pickTopicWithOutgoingEdge(request, SAMPLE_SLUG, fixtures.users.student)
    await expect(topicNodeLocator(page, pick.topicId)).toBeVisible({ timeout: 30_000 })
    await expect(
      page.locator(
        `.ors-canvas .react-flow__edge[data-id="${pick.edgeId}"] .react-flow__edge-path`,
      ),
    ).toBeVisible({ timeout: 30_000 })
  })

  test('topic drag moves node and attached edge geometry', async ({ page, request }) => {
    const pick = await pickTopicWithOutgoingEdge(request, SAMPLE_SLUG, fixtures.users.student)
    const node = topicNodeLocator(page, pick.topicId)
    const viewportBeforeDrag = await viewportTransform(page)
    const translateBefore = await nodeTranslate(page, pick.topicId)
    expect(translateBefore).toBeTruthy()
    const edgeBefore = await edgePathD(page, pick.edgeId)
    expect(edgeBefore).toBeTruthy()

    const box = await node.boundingBox()
    expect(box).toBeTruthy()
    if (!box || !translateBefore) return

    const startX = box.x + box.width / 2
    const startY = box.y + box.height / 2
    await page.mouse.move(startX, startY)
    await page.mouse.down()
    await page.mouse.move(startX + 72, startY + 48, { steps: 12 })
    await page.mouse.up()

    await waitForNodeTranslateChange(page, pick.topicId, translateBefore)
    const viewportAfterDrag = await viewportTransform(page)
    expect(
      viewportTransformsClose(viewportBeforeDrag, viewportAfterDrag),
      `camera moved during drag: before=${viewportBeforeDrag} after=${viewportAfterDrag}`,
    ).toBe(true)

    await expect
      .poll(async () => edgePathD(page, pick.edgeId), { timeout: 10_000 })
      .not.toBe(edgeBefore)
  })

  test('click without drag opens article', async ({ page, request }) => {
    const pick = await pickTopicWithOutgoingEdge(request, SAMPLE_SLUG, fixtures.users.student)
    const node = topicNodeLocator(page, pick.topicId)
    await node.click()
    await expect(page.getByRole('heading', { level: 2 })).toBeVisible({ timeout: 20_000 })
  })

  test('lock layout blocks drag; reset restores layout', async ({ page, request }) => {
    const pick = await pickTopicWithOutgoingEdge(request, SAMPLE_SLUG, fixtures.users.student)
    const nodeId = pick.topicId
    const node = topicNodeLocator(page, nodeId)
    const translateOrig = await nodeTranslate(page, nodeId)
    expect(translateOrig).toBeTruthy()
    if (!translateOrig) return

    await page.getByLabel('Lock layout').check()
    await expect(page.locator('.ors-canvas--locked')).toBeVisible()

    const box = await node.boundingBox()
    expect(box).toBeTruthy()
    if (!box) return
    const startX = box.x + box.width / 2
    const startY = box.y + box.height / 2
    await page.mouse.move(startX, startY)
    await page.mouse.down()
    await page.mouse.move(startX + 80, startY + 60, { steps: 10 })
    await page.mouse.up()

    const translateLocked = await nodeTranslate(page, nodeId)
    expect(translateLocked).toBeTruthy()
    if (!translateLocked) return
    expect(Math.abs(translateLocked.x - translateOrig.x)).toBeLessThan(2)
    expect(Math.abs(translateLocked.y - translateOrig.y)).toBeLessThan(2)

    await page.getByLabel('Lock layout').uncheck()
    await page.mouse.move(startX, startY)
    await page.mouse.down()
    await page.mouse.move(startX + 72, startY + 48, { steps: 12 })
    await page.mouse.up()
    await waitForNodeTranslateChange(page, nodeId, translateOrig)

    await page.getByRole('button', { name: 'Reset layout to original' }).click()
    await expect
      .poll(async () => {
        const t = await nodeTranslate(page, nodeId)
        if (!t) return 999
        return Math.abs(t.x - translateOrig.x) + Math.abs(t.y - translateOrig.y)
      }, { timeout: 15_000 })
      .toBeLessThan(3)
  })

  test('viewport transform stable when article panel opens', async ({ page, request }) => {
    const pick = await pickTopicWithOutgoingEdge(request, SAMPLE_SLUG, fixtures.users.student)
    const before = await waitForRoadmapViewportSettled(page)
    expect(before).toBeTruthy()

    const topicNode = topicNodeLocator(page, pick.topicId)
    await topicNode.click()
    await expect(page.getByRole('heading', { level: 2 })).toBeVisible({ timeout: 20_000 })
    await expectViewportStableThroughPanelResize(page, before)

    await page.locator('.ors-panel--desktop').getByRole('button', { name: 'Close' }).click()
    await expect(page.getByRole('heading', { level: 2 })).toBeHidden({ timeout: 10_000 })
    await expectViewportStableThroughPanelResize(page, before)
  })
})
