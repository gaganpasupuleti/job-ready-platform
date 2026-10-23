import { expect, type APIRequestContext, type Page } from '@playwright/test'

import { apiBaseUrl, loginAccessToken } from './helpers'
import { parseViewportTransform, viewportTransformsClose } from './roadmap-viewport'

export function parseNodeTranslate(transform: string | null) {
  if (!transform) return null
  const match = transform.match(/translate\(\s*([-\d.]+)px,\s*([-\d.]+)px\s*\)/)
  if (!match) return null
  return { x: Number.parseFloat(match[1]), y: Number.parseFloat(match[2]) }
}

export async function viewportTransform(page: Page) {
  return page.locator('.ors-canvas .react-flow__viewport').getAttribute('style')
}

export async function nodeTranslate(page: Page, nodeId: string) {
  const style = await page
    .locator(`.ors-canvas .react-flow__node[data-id="${nodeId}"]`)
    .getAttribute('style')
  return parseNodeTranslate(style)
}

export async function edgePathD(page: Page, edgeId: string) {
  return page
    .locator(`.ors-canvas .react-flow__edge[data-id="${edgeId}"] .react-flow__edge-path`)
    .getAttribute('d')
}

export type TopicEdgePick = { topicId: string; edgeId: string; targetId: string }

export async function pickTopicWithOutgoingEdge(
  request: APIRequestContext,
  slug: string,
  credentials: { email: string; password: string },
): Promise<TopicEdgePick> {
  const token = await loginAccessToken(request, credentials)
  const url = `${apiBaseUrl()}/roadmap/official/${slug}/graph`
  const res = await request.get(url, { headers: { Authorization: `Bearer ${token}` } })
  expect(res.ok(), `graph HTTP ${res.status()} for ${url}`).toBeTruthy()
  const body = (await res.json()) as {
    nodes: Array<{ id: string; type: string }>
    edges: Array<{ id: string; source: string; target: string }>
  }
  const topic =
    body.nodes.find(
      (node) =>
        node.type === 'topic' && body.edges.some((edge) => edge.source === node.id),
    ) ??
    body.nodes.find(
      (node) =>
        (node.type === 'subtopic' || node.type === 'topic') &&
        body.edges.some((edge) => edge.source === node.id),
    )
  expect(topic, `no topic with outgoing edge in ${slug} graph`).toBeTruthy()
  const edge = body.edges.find((e) => e.source === topic!.id)
  expect(edge).toBeTruthy()
  return { topicId: topic!.id, edgeId: edge!.id, targetId: edge!.target }
}

export function topicNodeLocator(page: Page, topicId: string) {
  return page.locator(`.ors-canvas .react-flow__node[data-id="${topicId}"]`)
}

/** Wait until initial fit animation settles before viewport baselines. */
export async function waitForRoadmapViewportSettled(page: Page, timeoutMs = 45_000) {
  let last: string | null = null
  let stableMs = 0
  const started = Date.now()
  while (Date.now() - started < timeoutMs) {
    const current = await viewportTransform(page)
    if (current && viewportTransformsClose(last, current, { translatePx: 0.75, zoom: 0.008 })) {
      stableMs += 120
      if (stableMs >= 480) return current
    } else {
      stableMs = 0
    }
    last = current
    await page.waitForTimeout(120)
  }
  return last
}

export async function expectViewportStableThroughPanelResize(
  page: Page,
  baseline: string | null,
  timeoutMs = 12_000,
) {
  const started = Date.now()
  while (Date.now() - started < timeoutMs) {
    const during = await viewportTransform(page)
    expect(
      viewportTransformsClose(baseline, during),
      `viewport moved: before=${baseline} during=${during}`,
    ).toBe(true)
    await page.waitForTimeout(150)
  }
}

export async function waitForNodeTranslateChange(
  page: Page,
  nodeId: string,
  before: { x: number; y: number },
  minDelta = 6,
  timeoutMs = 10_000,
) {
  await expect
    .poll(
      async () => {
        const after = await nodeTranslate(page, nodeId)
        if (!after) return 0
        return Math.abs(after.x - before.x) + Math.abs(after.y - before.y)
      },
      { timeout: timeoutMs },
    )
    .toBeGreaterThan(minDelta)
}
