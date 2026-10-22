import assert from 'node:assert/strict'
import test from 'node:test'

import {
  classifyArticleHttpResponse,
  classifyArticlePayload,
} from '../scripts/lib/roadmapArticleAudit.mjs'
import { verifyAuthHeaders } from '../scripts/lib/roadmapAuditAuth.mjs'
import { validateOfficialGraph } from '../scripts/lib/roadmapGraphAudit.mjs'

test('validateOfficialGraph rejects malformed graphs', () => {
  const empty = validateOfficialGraph({ nodes: [], edges: [] })
  assert.equal(empty.ok, false)

  const badEdge = validateOfficialGraph({
    nodes: [{ id: 'a', type: 'topic', position: { x: 0, y: 0 } }],
    edges: [{ id: 'e1', source: 'a', target: 'missing' }],
  })
  assert.equal(badEdge.ok, false)
  assert.ok(badEdge.issues.some((line) => line.includes('missing node')))

  const badHandle = validateOfficialGraph({
    nodes: [
      { id: 'a', type: 'vertical', position: { x: 0, y: 0 } },
      { id: 'b', type: 'topic', position: { x: 10, y: 0 } },
    ],
    edges: [{ id: 'e1', source: 'a', target: 'b', sourceHandle: 'x2' }],
  })
  assert.equal(badHandle.ok, false)
})

test('verifyAuthHeaders rejects invalid bearer tokens', async () => {
  const originalFetch = globalThis.fetch
  globalThis.fetch = async () => ({ ok: false, status: 401 }) as Response
  const result = await verifyAuthHeaders('http://127.0.0.1:8000', {
    Authorization: 'Bearer invalid',
  })
  assert.equal(result.ok, false)
  assert.equal(result.status, 401)
  globalThis.fetch = originalFetch
})

test('classifyArticlePayload rejects title-only stubs', () => {
  const titleOnly = classifyArticlePayload({ title: 'REST', markdown: '' })
  assert.equal(titleOnly.status, 'empty_content')

  const short = classifyArticlePayload({ title: 'REST', markdown: '# Hi\n\nshort' })
  assert.equal(short.status, 'empty_content')

  const ok = classifyArticlePayload({
    title: 'REST',
    markdown: '# REST\n\n'.padEnd(60, 'x'),
  })
  assert.equal(ok.status, 'ok')
})

test('classifyArticleHttpResponse maps auth and server errors', () => {
  assert.equal(classifyArticleHttpResponse(401, null).articleStatus, 'auth')
  assert.equal(classifyArticleHttpResponse(404, null).articleStatus, 'missing')
  assert.equal(classifyArticleHttpResponse(500, null).articleStatus, 'server_error')
})

test('validateOfficialGraph accepts minimal valid graph', () => {
  const ok = validateOfficialGraph({
    nodes: [
      { id: 'a', type: 'topic', position: { x: 0, y: 0 } },
      { id: 'b', type: 'subtopic', position: { x: 40, y: 0 } },
    ],
    edges: [{ id: 'e1', source: 'a', target: 'b', sourceHandle: 'x2', targetHandle: 'w1' }],
  })
  assert.equal(ok.ok, true)
  assert.equal(ok.nodeCount, 2)
})
