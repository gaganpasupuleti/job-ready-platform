/**
 * Catalog-wide official roadmap graph audit.
 *
 * Usage:
 *   node scripts/audit-roadmap-catalog.mjs --api http://127.0.0.1:8000
 *   ROADMAP_AUDIT_TOKEN=<jwt> node scripts/audit-roadmap-catalog.mjs
 *   ROADMAP_AUDIT_EMAIL=... ROADMAP_AUDIT_PASSWORD=... node scripts/audit-roadmap-catalog.mjs
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { resolveAuthHeaders } from './lib/roadmapAuditAuth.mjs'
import { validateOfficialGraph } from './lib/roadmapGraphAudit.mjs'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const catalogPath = path.resolve(__dirname, '../../backend/app/data/official-roadmap-catalog.json')
const apiBase = process.argv.includes('--api')
  ? process.argv[process.argv.indexOf('--api') + 1]
  : process.env.DEV_API ?? 'http://127.0.0.1:8000'

function pickTopicNodeId(nodes) {
  for (const node of nodes) {
    const t = node?.type
    if (t === 'topic' || t === 'subtopic') return node.id
  }
  return null
}

async function probeArticle(slug, nodeId, authHeaders) {
  const url = `${apiBase}/api/v1/roadmap/official/${encodeURIComponent(slug)}/topics/${encodeURIComponent(nodeId)}`
  const res = await fetch(url, { headers: { Accept: 'application/json', ...authHeaders } })
  if (res.status === 401 || res.status === 403) {
    return { articleStatus: 'auth', httpStatus: res.status, articleUrl: url }
  }
  if (!res.ok) {
    return { articleStatus: 'missing', httpStatus: res.status, articleUrl: url }
  }
  const body = await res.json()
  const hasBody = Boolean(body?.markdown?.trim() || body?.title?.trim())
  return {
    articleStatus: hasBody ? 'ok' : 'empty',
    httpStatus: res.status,
    articleUrl: url,
  }
}

async function fetchGraphRow(slug, authHeaders) {
  const graphUrl = `${apiBase}/api/v1/roadmap/official/${encodeURIComponent(slug)}/graph`
  const res = await fetch(graphUrl, {
    headers: { Accept: 'application/json', ...authHeaders },
  })

  if (res.status === 401 || res.status === 403) {
    return {
      slug,
      graphUrl,
      graphStatus: 'auth',
      httpStatus: res.status,
      graphAvailable: false,
      errors: [`HTTP ${res.status} on graph`],
    }
  }
  if (!res.ok) {
    return {
      slug,
      graphUrl,
      graphStatus: 'fail',
      httpStatus: res.status,
      graphAvailable: false,
      errors: [`HTTP ${res.status} on graph`],
    }
  }

  let payload
  try {
    payload = await res.json()
  } catch {
    return {
      slug,
      graphUrl,
      graphStatus: 'fail',
      httpStatus: res.status,
      graphAvailable: false,
      errors: ['graph response was not JSON'],
    }
  }

  const validation = validateOfficialGraph(payload)
  const topicId = pickTopicNodeId(payload?.nodes ?? [])
  const article =
    topicId != null ? await probeArticle(slug, topicId, authHeaders) : { articleStatus: 'no_topic_node' }

  const errors = [...validation.issues]
  if (!validation.ok) {
    errors.unshift('graph validation failed')
  }

  return {
    slug,
    graphUrl,
    graphStatus: validation.ok ? 'ok' : 'fail',
    httpStatus: res.status,
    graphAvailable: validation.ok,
    nodeCount: validation.nodeCount,
    edgeCount: validation.edgeCount,
    article,
    errors,
  }
}

async function main() {
  if (!fs.existsSync(catalogPath)) {
    console.error('catalog file missing:', catalogPath)
    process.exit(2)
  }

  const catalog = JSON.parse(fs.readFileSync(catalogPath, 'utf8'))
  const slugs = (catalog.roadmaps ?? catalog.items ?? [])
    .map((r) => r.family_slug ?? r.slug)
    .filter(Boolean)

  if (slugs.length === 0) {
    console.error('catalog contained zero slugs')
    process.exit(1)
  }

  let authHeaders
  try {
    authHeaders = await resolveAuthHeaders(apiBase)
  } catch (err) {
    console.error(err.message)
    process.exit(err.code === 'AUTH_MISSING' ? 2 : 3)
  }

  const rows = []
  let graphPass = 0
  let graphFail = 0
  let graphAuth = 0

  const concurrency = 4
  let i = 0
  async function worker() {
    while (i < slugs.length) {
      const slug = slugs[i++]
      try {
        const row = await fetchGraphRow(slug, authHeaders)
        rows.push(row)
        if (row.graphStatus === 'ok') graphPass++
        else if (row.graphStatus === 'auth') graphAuth++
        else graphFail++
      } catch (err) {
        graphFail++
        rows.push({
          slug,
          graphStatus: 'error',
          graphAvailable: false,
          errors: [String(err)],
        })
      }
    }
  }
  await Promise.all(Array.from({ length: concurrency }, () => worker()))

  const outPath = path.resolve(__dirname, '../e2e/artifacts/roadmap-catalog-audit.json')
  fs.mkdirSync(path.dirname(outPath), { recursive: true })
  const report = {
    apiBase,
    authenticated: true,
    at: new Date().toISOString(),
    totals: {
      slugs: slugs.length,
      graphPass,
      graphFail,
      graphAuth,
    },
    rows,
  }
  fs.writeFileSync(outPath, JSON.stringify(report, null, 2))

  console.log(JSON.stringify({ totals: report.totals, outPath }))

  if (graphAuth > 0) process.exit(3)
  if (graphFail > 0) process.exit(1)
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
