import type { Edge, Node } from '@xyflow/react'

import type { OfficialRoadmapEdge, OfficialRoadmapNode } from '@/services/roadmapOfficialService'

import { shouldHideOfficialNode } from './roadmapShLinks.ts'

export type NodeData = { label: string; nodeType: string; raw: OfficialRoadmapNode }

function nodeDimensions(
  raw: OfficialRoadmapNode,
  nodeType: string,
  label: string,
): { width?: number; height?: number } {
  const width = raw.width ?? raw.measured?.width
  const height = raw.height ?? raw.measured?.height
  if (width && height) return { width, height }
  if (nodeType !== 'topic' && nodeType !== 'subtopic' && nodeType !== 'button') {
    return { width: width ?? undefined, height: height ?? undefined }
  }
  const chars = Math.max(label.length, 8)
  const estWidth = Math.min(280, Math.max(120, Math.ceil(chars * 7.2)))
  const lines = Math.ceil((chars * 7.2) / estWidth)
  const estHeight = Math.max(36, 28 + lines * 16)
  return {
    width: width ?? estWidth,
    height: height ?? estHeight,
  }
}

export function toFlowNode(raw: OfficialRoadmapNode): Node | null {
  if (!raw.position) return null
  const nodeType = raw.type ?? 'default'
  const width = raw.width ?? raw.measured?.width
  const height = raw.height ?? raw.measured?.height

  if (nodeType === 'vertical' || nodeType === 'horizontal') {
    return {
      id: raw.id,
      type: nodeType,
      position: { ...raw.position },
      data: { label: '', nodeType, raw },
      width: width ?? 20,
      height: height ?? 40,
      draggable: false,
      selectable: false,
      focusable: false,
      zIndex: 10,
    }
  }

  if (nodeType === 'linksgroup') {
    const groupLabel = raw.data?.label?.trim() ?? 'Related paths'
    return {
      id: raw.id,
      type: 'linksgroup',
      position: { ...raw.position },
      data: { label: groupLabel, nodeType, raw },
      width: width ?? 280,
      height: height ?? 180,
      draggable: false,
      selectable: true,
    }
  }

  if (nodeType === 'section') {
    return {
      id: raw.id,
      type: 'section',
      position: { ...raw.position },
      data: { label: raw.data?.label ?? '', nodeType, raw },
      width: width ?? 200,
      height: height ?? 120,
      draggable: false,
      selectable: false,
      zIndex: -1,
    }
  }

  const label = raw.data?.label?.trim()
  if (!label && nodeType !== 'paragraph') return null

  const size = nodeDimensions(raw, nodeType, label ?? '')

  return {
    id: raw.id,
    type: 'roadmap',
    position: { ...raw.position },
    data: { label: label ?? '', nodeType, raw },
    width: size.width,
    height: size.height,
    draggable: false,
    selectable: true,
  }
}

const TOPIC_DRAG_TYPES = new Set(['topic', 'subtopic'])

/** When layout is locked, topic pills cannot move. */
export function applyNodesDraggable(nodes: Node[], layoutLocked: boolean): Node[] {
  return nodes.map((node) => {
    const nodeType = (node.data as NodeData).nodeType
    const draggable = !layoutLocked && TOPIC_DRAG_TYPES.has(nodeType)
    return { ...node, draggable }
  })
}

export function assertFlowGraphShape(nodes: OfficialRoadmapNode[], edges: OfficialRoadmapEdge[]) {
  if (!Array.isArray(nodes) || nodes.length === 0) {
    throw new Error('Roadmap graph is missing nodes.')
  }
  if (!Array.isArray(edges)) {
    throw new Error('Roadmap graph is missing edges.')
  }
}

export function toFlowEdge(raw: OfficialRoadmapEdge): Edge {
  const style = raw.style ?? {}
  const dash = style.strokeDasharray as string | undefined
  const isDashed = Boolean(dash && dash !== '0')

  return {
    id: raw.id,
    source: raw.source,
    target: raw.target,
    sourceHandle: raw.sourceHandle ? `${raw.sourceHandle}-s` : undefined,
    targetHandle: raw.targetHandle ? `${raw.targetHandle}-t` : undefined,
    type: 'smoothstep',
    animated: isDashed,
    style: {
      stroke: (style.stroke as string) ?? '#5a6f7f',
      strokeWidth: Number(style.strokeWidth ?? 2),
      strokeDasharray: isDashed ? dash : undefined,
      strokeLinecap: (style.strokeLinecap as 'round' | 'butt') ?? 'round',
      strokeLinejoin: 'round',
    },
    selectable: false,
  }
}

export function buildFlowGraph(nodes: OfficialRoadmapNode[], edges: OfficialRoadmapEdge[]) {
  const visible = nodes.filter((node) => !shouldHideOfficialNode(node))
  const nodeIds = new Set<string>()
  const flowNodes = visible.map(toFlowNode).filter((node): node is Node => {
    if (!node) return false
    nodeIds.add(node.id)
    return true
  })
  const flowEdges = edges
    .map(toFlowEdge)
    .filter((edge) => nodeIds.has(edge.source) && nodeIds.has(edge.target))
  return { nodes: flowNodes, edges: flowEdges }
}

export function cloneGraph(nodes: Node[], edges: Edge[]) {
  return {
    nodes: nodes.map((node) => ({
      ...node,
      position: { ...node.position },
      data: { ...node.data },
    })),
    edges: edges.map((edge) => ({ ...edge })),
  }
}
