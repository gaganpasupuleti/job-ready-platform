/**
 * Catalog-wide official roadmap graph + sampled article audit.
 *
 * Usage:
 *   node scripts/audit-roadmap-catalog.mjs --api http://127.0.0.1:8000
 *   ROADMAP_AUDIT_TOKEN=<jwt> node scripts/audit-roadmap-catalog.mjs
 *   ROADMAP_AUDIT_EMAIL=... ROADMAP_AUDIT_PASSWORD=... node scripts/audit-roadmap-catalog.mjs
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import {
  classifyArticleHttpResponse,
  listReadableTopicNodeIds,
  pickSampleTopicNodeId,
} from './lib/roadmapArticleAudit.mjs'
import { resolveAuthHeaders } from './lib/roadmapAuditAuth.mjs'
import { validateOfficialGraph } from './lib/roadmapGraphAudit.mjs'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const catalogPath = path.resolve(__dirname, '../../backend/app/data/official-roadmap-catalog.json')
const apiBase = process.argv.includes('--api')
  ? process.argv[process.argv.indexOf('--api') + 1]
  : process.env.DEV_API ?? 'http://127.0.0.1:8000'

async function probeArticle(slug, nodeId, authHeaders) {
  const articleUrl = `${apiBase}/api/v1/roadmap/official/${encodeURIComponent(slug)}/topics/${encodeURIComponent(nodeId)}`
  try {
    const res = await fetch(articleUrl, { headers: { Accept: 'application/json', ...authHeaders } })
    let body = null
    const text = await res.text()
    if (text) {
      try {
        body = JSON.parse(text)
      } catch {
        body = null
      }
    }
    const classified = classifyArticleHttpResponse(res.status, body)
    return {
      ...classified,
      articleUrl,
      sampledNodeId: nodeId,
      sampling: 'one_topic_per_slug',
    }
  } catch (err) {
    return {
      articleStatus: 'transport_error',
      httpStatus: 0,
      articleUrl,
      sampledNodeId: nodeId,
      sampling: 'one_topic_per_slug',
      reason: String(err),
    }
  }
}

async function fetchGraphRow(slug, authHeaders) {
  const graphUrl = `${apiBase}/api/v1/roadmap/official/${encodeURIComponent(slug)}/graph`
  let res
  try {
    res = await fetch(graphUrl, {
      headers: { Accept: 'application/json', ...authHeaders },
    })
  } catch (err) {
    return {
      slug,
      graphUrl,
      graphStatus: 'transport_error',
      graphAvailable: false,
      errors: [String(err)],
      article: { articleStatus: 'unverified', reason: 'graph transport failed' },
    }
  }

  if (res.status === 401 || res.status === 403) {
    return {
      slug,
      graphUrl,
      graphStatus: 'auth',
      httpStatus: res.status,
      graphAvailable: false,
      errors: [`HTTP ${res.status} on graph`],
      article: { articleStatus: 'unverified', reason: 'graph auth failure' },
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
      article: { articleStatus: 'unverified', reason: 'graph unavailable' },
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
      article: { articleStatus: 'unverified', reason: 'graph JSON invalid' },
    }
  }

  const validation = validateOfficialGraph(payload)
  const readableIds = listReadableTopicNodeIds(payload?.nodes ?? [])
  const sampleId = pickSampleTopicNodeId(payload?.nodes ?? [])
  const articleInventory = {
    readableTopicNodes: readableIds.length,
    sampledNodes: sampleId ? 1 : 0,
    uncheckedReadableNodes: sampleId ? Math.max(0, readableIds.length - 1) : readableIds.length,
    note: 'Article audit samples one readable node per slug; full topic coverage is not claimed.',
  }

  const article =
    sampleId != null
      ? await probeArticle(slug, sampleId, authHeaders)
      : {
          articleStatus: 'no_readable_topic',
          sampling: 'one_topic_per_slug',
          reason: 'no topic/subtopic nodes in graph',
        }

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
    articleInventory,
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
  let articleSampleOk = 0
  let articleSampleFail = 0
  let articleUnverified = 0

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

        const aStatus = row.article?.articleStatus
        if (aStatus === 'ok') articleSampleOk++
        else if (aStatus === 'unverified' || aStatus === 'no_readable_topic') articleUnverified++
        else articleSampleFail++
      } catch (err) {
        graphFail++
        articleSampleFail++
        rows.push({
          slug,
          graphStatus: 'error',
          graphAvailable: false,
          errors: [String(err)],
          article: { articleStatus: 'transport_error', reason: String(err) },
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
      articleSampleOk,
      articleSampleFail,
      articleUnverified,
    },
    rows,
  }
  fs.writeFileSync(outPath, JSON.stringify(report, null, 2))

  console.log(JSON.stringify({ totals: report.totals, outPath }))

  if (graphAuth > 0) process.exit(3)
  if (graphFail > 0) process.exit(1)
  if (articleSampleFail > 0) process.exit(4)
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
