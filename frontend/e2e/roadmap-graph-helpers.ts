import { expect, type APIRequestContext, type Page } from '@playwright/test'

import { apiBaseUrl, loginAccessToken } from './helpers'
import { viewportTransformsClose } from './roadmap-viewport'

export function parseNodeTranslate(transform: string | null) {
  if (!transform) return null
  const match = transform.match(
    /translate(?:3d)?\(\s*([-\d.]+)px,\s*([-\d.]+)px(?:,\s*[-\d.]+px)?\s*\)/,
  )
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

async function loadGraphCandidates(
  request: APIRequestContext,
  slug: string,
  credentials: { email: string; password: string },
) {
  const token = await loginAccessToken(request, credentials)
  const url = `${apiBaseUrl()}/roadmap/official/${slug}/graph`
  const res = await request.get(url, { headers: { Authorization: `Bearer ${token}` } })
  expect(res.ok(), `graph HTTP ${res.status()} for ${url}`).toBeTruthy()
  const body = (await res.json()) as {
    nodes: Array<{ id: string; type: string }>
    edges: Array<{ id: string; source: string; target: string }>
  }
  const candidates: TopicEdgePick[] = []
  for (const node of body.nodes) {
    if (node.type !== 'topic' && node.type !== 'subtopic') continue
    const edge = body.edges.find((e) => e.source === node.id)
    if (edge) {
      candidates.push({ topicId: node.id, edgeId: edge.id, targetId: edge.target })
    }
  }
  candidates.sort((a, b) => {
    const aTopic = body.nodes.find((n) => n.id === a.topicId)?.type === 'topic' ? 0 : 1
    const bTopic = body.nodes.find((n) => n.id === b.topicId)?.type === 'topic' ? 0 : 1
    return aTopic - bTopic
  })
  expect(candidates.length, `no topic/subtopic with outgoing edge in ${slug} graph`).toBeGreaterThan(0)
  return candidates
}

async function pickFromVisibleCandidates(page: Page, candidates: TopicEdgePick[]) {
  for (const pick of candidates) {
    const node = topicNodeLocator(page, pick.topicId)
    if ((await node.count()) === 0) continue
    await node.scrollIntoViewIfNeeded()
    try {
      await expect(node).toBeVisible({ timeout: 8_000 })
      await expect(
        page.locator(
          `.ors-canvas .react-flow__edge[data-id="${pick.edgeId}"] .react-flow__edge-path`,
        ),
      ).toBeVisible({ timeout: 5_000 })
      return pick
    } catch {
      continue
    }
  }
  return null
}

/** Picks a topic+edge that exists in the DOM (onlyRenderVisibleElements). */
export async function pickVisibleTopicWithOutgoingEdge(
  page: Page,
  request: APIRequestContext,
  slug: string,
  credentials: { email: string; password: string },
): Promise<TopicEdgePick> {
  const candidates = await loadGraphCandidates(request, slug, credentials)
  let pick = await pickFromVisibleCandidates(page, candidates)
  if (pick) return pick

  await page.getByRole('button', { name: 'Fit overview' }).click()
  await expect
    .poll(async () => page.locator('.ors-canvas .react-flow__node').count(), { timeout: 15_000 })
    .toBeGreaterThan(0)
  pick = await pickFromVisibleCandidates(page, candidates)
  expect(pick, `no visible topic+edge on ${slug} canvas after fit`).toBeTruthy()
  return pick!
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
