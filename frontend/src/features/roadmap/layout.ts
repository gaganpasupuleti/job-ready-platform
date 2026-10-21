/** Deterministic FE layout coordinates from planned phases (not backend). */

import type { RoadmapAssembly, RoadmapEdge, RoadmapNode } from './types'
import { orderedPhases } from './adapter'

export interface LayoutNode {
  node: RoadmapNode
  x: number
  y: number
  width: number
  height: number
  phaseKey: string
}

export interface LayoutEdge {
  edge: RoadmapEdge
  points: { x: number; y: number }[]
}

export interface RoadmapLayout {
  nodes: LayoutNode[]
  edges: LayoutEdge[]
  width: number
  height: number
  phaseBands: { phaseKey: string; label: string; x: number; width: number }[]
}

const NODE_W = 168
const NODE_H = 56
const COL_GAP = 56
const ROW_GAP = 28
const PAD_X = 48
const PAD_Y = 56

export function buildRoadmapLayout(assembly: RoadmapAssembly): RoadmapLayout {
  const phases = orderedPhases(assembly)
  const byKey = new Map(assembly.nodes.map((n) => [n.node_key, n]))
  const layoutNodes: LayoutNode[] = []
  const phaseBands: RoadmapLayout['phaseBands'] = []

  let maxRows = 1
  phases.forEach((phase, col) => {
    const keys = [...phase.node_keys].sort((a, b) => {
      const na = byKey.get(a)
      const nb = byKey.get(b)
      return (na?.planned_index ?? 0) - (nb?.planned_index ?? 0)
    })
    maxRows = Math.max(maxRows, keys.length)
    const x = PAD_X + col * (NODE_W + COL_GAP)
    phaseBands.push({
      phaseKey: phase.phase_key,
      label: phase.label,
      x,
      width: NODE_W,
    })
    keys.forEach((key, row) => {
      const node = byKey.get(key)
      if (!node) return
      layoutNodes.push({
        node,
        x,
        y: PAD_Y + row * (NODE_H + ROW_GAP),
        width: NODE_W,
        height: NODE_H,
        phaseKey: phase.phase_key,
      })
    })
  })

  const pos = new Map(layoutNodes.map((n) => [n.node.node_key, n]))
  const layoutEdges: LayoutEdge[] = assembly.edges.map((edge) => {
    const from = pos.get(edge.from_node_key)
    const to = pos.get(edge.to_node_key)
    if (!from || !to) {
      return { edge, points: [] }
    }
    const x1 = from.x + from.width
    const y1 = from.y + from.height / 2
    const x2 = to.x
    const y2 = to.y + to.height / 2
    const mx = (x1 + x2) / 2
    return {
      edge,
      points: [
        { x: x1, y: y1 },
        { x: mx, y: y1 },
        { x: mx, y: y2 },
        { x: x2, y: y2 },
      ],
    }
  })

  return {
    nodes: layoutNodes,
    edges: layoutEdges,
    width: PAD_X * 2 + phases.length * NODE_W + Math.max(0, phases.length - 1) * COL_GAP,
    height: PAD_Y + maxRows * NODE_H + Math.max(0, maxRows - 1) * ROW_GAP + PAD_Y,
    phaseBands,
  }
}

export function pointsToPath(points: { x: number; y: number }[]): string {
  if (points.length < 2) return ''
  const [p0, ...rest] = points
  return `M ${p0.x} ${p0.y} ` + rest.map((p) => `L ${p.x} ${p.y}`).join(' ')
}
