import type { OfficialRoadmapEdge, OfficialRoadmapNode } from '@/services/roadmapOfficialService'

function isFiniteNumber(value: unknown): boolean {
  return typeof value === 'number' && Number.isFinite(value)
}

export function assertValidGraphShape(
  nodes: OfficialRoadmapNode[],
  edges: OfficialRoadmapEdge[],
): void {
  if (!Array.isArray(nodes) || nodes.length === 0) {
    throw new Error('Graph response was empty')
  }
  if (!Array.isArray(edges)) {
    throw new Error('Graph response was missing edges')
  }
  if (edges.length === 0) {
    return
  }
  const nodeIds = new Set<string>()
  for (const node of nodes) {
    if (!node?.id || typeof node.id !== 'string') {
      throw new Error('Graph response had invalid nodes')
    }
    if (nodeIds.has(node.id)) {
      throw new Error('Graph response had duplicate node ids')
    }
    nodeIds.add(node.id)
    const pos = node.position
    if (!pos || !isFiniteNumber(pos.x) || !isFiniteNumber(pos.y)) {
      throw new Error('Graph response had invalid node positions')
    }
  }
  const edgeIds = new Set<string>()
  for (const edge of edges) {
    if (!edge?.id || typeof edge.id !== 'string') {
      throw new Error('Graph response had invalid edges')
    }
    if (edgeIds.has(edge.id)) {
      throw new Error('Graph response had duplicate edge ids')
    }
    edgeIds.add(edge.id)
    if (!edge.source || !edge.target || !nodeIds.has(edge.source) || !nodeIds.has(edge.target)) {
      throw new Error('Graph response had invalid edge references')
    }
  }
}

export function filterOutlineNodes(nodes: OfficialRoadmapNode[], filter: string) {
  const needle = filter.trim().toLowerCase()
  return nodes.filter((node) => {
    const t = node.type
    if (t !== 'topic' && t !== 'subtopic') return false
    const label = node.data?.label?.trim() ?? ''
    if (!label) return false
    return !needle || label.toLowerCase().includes(needle)
  })
}
