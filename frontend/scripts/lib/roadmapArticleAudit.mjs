/** Official roadmap topic article classification (audit CLI + unit tests). */

const READABLE_NODE_TYPES = new Set(['topic', 'subtopic'])

/** Minimum markdown body length for a readable article (excludes title-only stubs). */
const MIN_MARKDOWN_CHARS = 48

/**
 * @param {unknown} body
 * @returns {{ status: string, reason?: string }}
 */
export function classifyArticlePayload(body) {
  if (body == null || typeof body !== 'object') {
    return { status: 'empty_content', reason: 'response was not an object' }
  }
  const markdown = typeof body.markdown === 'string' ? body.markdown.trim() : ''
  if (!markdown) {
    const hasTitle = Boolean(typeof body.title === 'string' && body.title.trim())
    return {
      status: 'empty_content',
      reason: hasTitle ? 'markdown missing (title alone is insufficient)' : 'markdown missing',
    }
  }
  if (markdown.length < MIN_MARKDOWN_CHARS) {
    return { status: 'empty_content', reason: `markdown too short (${markdown.length} chars)` }
  }
  return { status: 'ok' }
}

/**
 * @param {number} httpStatus
 * @param {unknown} body
 * @returns {{ articleStatus: string, httpStatus: number, reason?: string }}
 */
export function classifyArticleHttpResponse(httpStatus, body) {
  if (httpStatus === 401 || httpStatus === 403) {
    return { articleStatus: 'auth', httpStatus, reason: `HTTP ${httpStatus}` }
  }
  if (httpStatus === 404) {
    return { articleStatus: 'missing', httpStatus, reason: 'topic article not found' }
  }
  if (httpStatus >= 500) {
    return { articleStatus: 'server_error', httpStatus, reason: `HTTP ${httpStatus}` }
  }
  if (!httpStatus || httpStatus < 200 || httpStatus >= 300) {
    return { articleStatus: 'http_error', httpStatus, reason: `HTTP ${httpStatus}` }
  }
  const classified = classifyArticlePayload(body)
  if (classified.status !== 'ok') {
    return { articleStatus: classified.status, httpStatus, reason: classified.reason }
  }
  return { articleStatus: 'ok', httpStatus }
}

/**
 * @param {Array<{ id?: string, type?: string }>} nodes
 */
export function listReadableTopicNodeIds(nodes) {
  if (!Array.isArray(nodes)) return []
  return nodes
    .filter((n) => n?.id && READABLE_NODE_TYPES.has(n.type ?? ''))
    .map((n) => n.id)
}

/**
 * Pick one node id for per-slug sampling (first topic, else first subtopic).
 */
export function pickSampleTopicNodeId(nodes) {
  const ids = listReadableTopicNodeIds(nodes)
  if (ids.length === 0) return null
  return ids[0]
}
