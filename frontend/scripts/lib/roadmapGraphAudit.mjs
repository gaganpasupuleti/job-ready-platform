/** Shared official roadmap graph validation (audit CLI + unit tests). */

export const HANDLE_SLOTS = new Set(['x1', 'w1', 'x2', 'w2', 'y1', 'z1', 'y2', 'z2'])

/** Node types that render React Flow handles (see roadmapNodes.tsx). */
export const HANDLE_NODE_TYPES = new Set([
  'topic',
  'subtopic',
  'button',
  'label',
  'paragraph',
  'linksgroup',
])

function isFiniteNumber(value) {
  return typeof value === 'number' && Number.isFinite(value)
}

function isNonEmptyId(value) {
  return typeof value === 'string' && value.trim().length > 0
}

/**
 * @returns {{ ok: boolean, issues: string[], nodeCount: number, edgeCount: number }}
 */
export function validateOfficialGraph(payload) {
  const issues = []
  const nodes = payload?.nodes
  const edges = payload?.edges

  if (!Array.isArray(nodes) || nodes.length === 0) {
    issues.push('nodes must be a nonempty array')
    return { ok: false, issues, nodeCount: 0, edgeCount: 0 }
  }
  if (!Array.isArray(edges)) {
    issues.push('edges must be an array')
    return { ok: false, issues, nodeCount: nodes.length, edgeCount: 0 }
  }

  const nodeById = new Map()
  for (const node of nodes) {
    if (!isNonEmptyId(node?.id)) {
      issues.push('node missing string id')
      continue
    }
    if (nodeById.has(node.id)) {
      issues.push(`duplicate node id ${node.id}`)
    }
    nodeById.set(node.id, node)
    const pos = node.position
    if (!pos || !isFiniteNumber(pos.x) || !isFiniteNumber(pos.y)) {
      issues.push(`node ${node.id} has invalid position`)
    }
  }

  const edgeIds = new Set()
  for (const edge of edges) {
    if (!isNonEmptyId(edge?.id)) {
      issues.push('edge missing string id')
      continue
    }
    if (edgeIds.has(edge.id)) {
      issues.push(`duplicate edge id ${edge.id}`)
    }
    edgeIds.add(edge.id)
    if (!isNonEmptyId(edge.source) || !isNonEmptyId(edge.target)) {
      issues.push(`edge ${edge.id} missing source/target`)
      continue
    }
    if (!nodeById.has(edge.source) || !nodeById.has(edge.target)) {
      issues.push(`edge ${edge.id} references missing node`)
      continue
    }
    const srcType = nodeById.get(edge.source).type ?? 'default'
    const tgtType = nodeById.get(edge.target).type ?? 'default'
    if (edge.sourceHandle) {
      if (!HANDLE_SLOTS.has(edge.sourceHandle)) {
        issues.push(`edge ${edge.id} unknown source handle ${edge.sourceHandle}`)
      } else if (!HANDLE_NODE_TYPES.has(srcType)) {
        issues.push(`edge ${edge.id} source ${edge.source} type ${srcType} cannot emit handles`)
      }
    }
    if (edge.targetHandle) {
      if (!HANDLE_SLOTS.has(edge.targetHandle)) {
        issues.push(`edge ${edge.id} unknown target handle ${edge.targetHandle}`)
      } else if (!HANDLE_NODE_TYPES.has(tgtType)) {
        issues.push(`edge ${edge.id} target ${edge.target} type ${tgtType} cannot receive handles`)
      }
    }
  }

  return {
    ok: issues.length === 0,
    issues,
    nodeCount: nodes.length,
    edgeCount: edges.length,
  }
}
