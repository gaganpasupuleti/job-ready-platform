/**
 * Catalog-wide graph audit (Node). Requires backend on DEV_API or fetches bundled JSON only.
 * Usage: node scripts/audit-roadmap-catalog.mjs [--api http://127.0.0.1:8000]
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const catalogPath = path.resolve(__dirname, '../../backend/app/data/official-roadmap-catalog.json')
const apiBase = process.argv.includes('--api')
  ? process.argv[process.argv.indexOf('--api') + 1]
  : process.env.DEV_API ?? 'http://127.0.0.1:8000'

const HANDLE_SLOTS = new Set(['x1', 'w1', 'x2', 'w2', 'y1', 'z1', 'y2', 'z2'])
const TOPIC_TYPES = new Set(['topic', 'subtopic', 'button', 'label', 'paragraph', 'linksgroup'])

function flowHandle(handle, role) {
  if (!handle) return null
  return `${handle}-${role === 'source' ? 's' : 't'}`
}

function auditGraph(slug, payload) {
  const nodes = payload?.nodes ?? []
  const edges = payload?.edges ?? []
  const nodeById = new Map(nodes.map((n) => [n.id, n]))
  const issues = []
  let dangling = 0
  let handleMiss = 0

  for (const edge of edges) {
    if (!nodeById.has(edge.source) || !nodeById.has(edge.target)) {
      dangling++
      issues.push(`dangling edge ${edge.id}`)
      continue
    }
    const src = nodeById.get(edge.source)
    const tgt = nodeById.get(edge.target)
    const srcType = src.type ?? 'default'
    const tgtType = tgt.type ?? 'default'
    if (edge.sourceHandle) {
      if (!HANDLE_SLOTS.has(edge.sourceHandle)) {
        issues.push(`unknown source handle ${edge.sourceHandle} on ${edge.id}`)
      } else if (!TOPIC_TYPES.has(srcType)) {
        issues.push(`source ${edge.source} type ${srcType} has handle edge ${edge.id}`)
      }
    }
    if (edge.targetHandle) {
      if (!HANDLE_SLOTS.has(edge.targetHandle)) {
        issues.push(`unknown target handle ${edge.targetHandle} on ${edge.id}`)
      } else if (!TOPIC_TYPES.has(tgtType)) {
        handleMiss++
        issues.push(`target ${edge.target} type ${tgtType} missing handles for ${edge.id}`)
      }
    }
    if (edge.sourceHandle) flowHandle(edge.sourceHandle, 'source')
    if (edge.targetHandle) flowHandle(edge.targetHandle, 'target')
  }

  return {
    slug,
    nodeCount: nodes.length,
    edgeCount: edges.length,
    dangling,
    handleMiss,
    issueCount: issues.length,
    sampleIssues: issues.slice(0, 5),
  }
}

async function fetchGraph(slug) {
  const res = await fetch(`${apiBase}/api/v1/roadmaps/${slug}/graph`, {
    headers: { Accept: 'application/json' },
  })
  if (res.status === 401 || res.status === 403) return { status: 'auth', slug }
  if (!res.ok) return { status: 'fail', slug, code: res.status }
  const data = await res.json()
  return { status: 'ok', slug, audit: auditGraph(slug, data) }
}

async function main() {
  const catalog = JSON.parse(fs.readFileSync(catalogPath, 'utf8'))
  const slugs = (catalog.roadmaps ?? catalog.items ?? []).map((r) => r.family_slug ?? r.slug).filter(Boolean)
  const results = { pass: 0, fail: 0, auth: 0, unverified: 0, rows: [] }

  const concurrency = 4
  let i = 0
  async function worker() {
    while (i < slugs.length) {
      const slug = slugs[i++]
      try {
        const row = await fetchGraph(slug)
        results.rows.push(row)
        if (row.status === 'ok') results.pass++
        else if (row.status === 'auth') results.auth++
        else results.fail++
      } catch {
        results.unverified++
        results.rows.push({ status: 'error', slug })
      }
    }
  }
  await Promise.all(Array.from({ length: concurrency }, () => worker()))

  const outPath = path.resolve(__dirname, '../e2e/artifacts/roadmap-catalog-audit.json')
  fs.mkdirSync(path.dirname(outPath), { recursive: true })
  fs.writeFileSync(outPath, JSON.stringify({ apiBase, at: new Date().toISOString(), totals: results, rows: results.rows }, null, 2))
  console.log(JSON.stringify({ totals: { pass: results.pass, fail: results.fail, auth: results.auth, unverified: results.unverified }, outPath }))
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
