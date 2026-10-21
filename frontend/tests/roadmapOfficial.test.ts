import assert from 'node:assert/strict'
import test from 'node:test'

import { toFlowEdge } from '../src/features/roadmap-official/graph.ts'
import { assertValidGraphShape } from '../src/features/roadmap-official/graphValidation.ts'
import { flowDuration } from '../src/features/roadmap-official/roadmapMotion.ts'
import {
  internalRoadmapPath,
  rewriteRoadmapShMarkdown,
} from '../src/features/roadmap-official/roadmapShLinks.ts'
test('toFlowEdge maps roadmap.sh handle ids to unique React Flow handles', () => {
  const edge = toFlowEdge({
    id: 'e1',
    source: 'a',
    target: 'b',
    sourceHandle: 'x2',
    targetHandle: 'w1',
  })
  assert.equal(edge.sourceHandle, 'x2-s')
  assert.equal(edge.targetHandle, 'w1-t')
})

test('assertValidGraphShape rejects bad edge references', () => {
  assert.throws(() =>
    assertValidGraphShape(
      [{ id: 'a', position: { x: 0, y: 0 } }],
      [{ id: 'e1', source: 'a', target: 'missing' }],
    ),
  )
})

test('rewriteRoadmapShMarkdown keeps unknown slugs external', () => {
  const allowed = new Set(['api-design'])
  const md = 'See [other](https://roadmap.sh/devops) and [api](https://roadmap.sh/api-design).'
  const out = rewriteRoadmapShMarkdown(md, allowed)
  assert.match(out, /roadmap\.sh\/devops/)
  assert.match(out, /\]\(\/roadmaps\/api-design\)/)
})

test('internalRoadmapPath respects allowed slugs', () => {
  const allowed = new Set(['python'])
  assert.equal(internalRoadmapPath('https://roadmap.sh/python', allowed), '/roadmaps/python')
  assert.equal(internalRoadmapPath('https://roadmap.sh/devops', allowed), null)
})

test('flowDuration returns zero when reduced motion is on', () => {
  assert.equal(flowDuration(true, 280), 0)
  assert.equal(flowDuration(false, 280), 280)
})
