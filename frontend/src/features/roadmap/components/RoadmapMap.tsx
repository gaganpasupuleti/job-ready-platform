import type { RefObject } from 'react'

import { cn } from '@/utils/cn'

import type { EdgeRelation } from '../types'
import { pointsToPath, type LayoutEdge, type LayoutNode, type RoadmapLayout } from '../layout'

interface RoadmapMapProps {
  layout: RoadmapLayout
  selectedKey: string | null
  startHereKey: string | null
  onSelect: (nodeKey: string) => void
  scale: number
  offset: { x: number; y: number }
  viewportRef: RefObject<HTMLDivElement | null>
}

function edgeClass(relation: string): string {
  switch (relation as EdgeRelation) {
    case 'prerequisite':
      return 'rm-edge rm-edge--hard'
    case 'recommended_before':
      return 'rm-edge rm-edge--soft'
    case 'next':
      return 'rm-edge rm-edge--next'
    case 'related':
      return 'rm-edge rm-edge--related'
    default:
      return 'rm-edge'
  }
}

function nodeTone(node: LayoutNode['node']): string {
  if (node.is_optional) return 'rm-node--optional'
  if (node.availability === 'available') return 'rm-node--available'
  if (node.availability === 'blocked_prerequisite') return 'rm-node--blocked'
  if (node.availability === 'resource_missing') return 'rm-node--missing'
  return 'rm-node--muted'
}

export function RoadmapMap({
  layout,
  selectedKey,
  startHereKey,
  onSelect,
  scale,
  offset,
  viewportRef,
}: RoadmapMapProps) {
  return (
    <div className="rm-viewport" ref={viewportRef} tabIndex={-1}>
      <div
        className="rm-canvas"
        style={{
          width: layout.width,
          height: layout.height,
          transform: `translate(${offset.x}px, ${offset.y}px) scale(${scale})`,
        }}
      >
        <svg
          className="rm-edges"
          width={layout.width}
          height={layout.height}
          aria-hidden="true"
        >
          {layout.edges.map((e: LayoutEdge, i) =>
            e.points.length ? (
              <path
                key={`${e.edge.from_node_key}-${e.edge.to_node_key}-${e.edge.relation_type}-${i}`}
                d={pointsToPath(e.points)}
                className={edgeClass(e.edge.relation_type)}
              />
            ) : null,
          )}
        </svg>

        {layout.phaseBands.map((band) => (
          <div
            key={band.phaseKey}
            className="rm-phase-label"
            style={{ left: band.x, width: band.width }}
          >
            {band.label}
          </div>
        ))}

        {layout.nodes.map((ln) => {
          const selected = ln.node.node_key === selectedKey
          const isStart = ln.node.node_key === startHereKey
          return (
            <button
              key={ln.node.node_key}
              type="button"
              className={cn(
                'rm-node',
                nodeTone(ln.node),
                selected && 'rm-node--selected',
                isStart && 'rm-node--start',
              )}
              style={{
                left: ln.x,
                top: ln.y,
                width: ln.width,
                height: ln.height,
              }}
              aria-pressed={selected}
              aria-label={`${ln.node.title}. ${ln.node.availability.replaceAll('_', ' ')}.`}
              onClick={() => onSelect(ln.node.node_key)}
            >
              <span className="rm-node__title">{ln.node.title.replace(' — Start here', '')}</span>
              <span className="rm-node__meta">
                {ln.node.is_optional ? 'Optional' : ln.node.importance ?? 'required'}
                {' · '}
                {ln.node.availability.replaceAll('_', ' ')}
              </span>
              {isStart ? <span className="rm-node__start-tag">Start here</span> : null}
            </button>
          )
        })}
      </div>
    </div>
  )
}
