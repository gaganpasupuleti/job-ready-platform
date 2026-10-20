import type { CSSProperties } from 'react'
import { Link } from 'react-router-dom'
import { type NodeProps, type NodeTypes } from '@xyflow/react'

import type { OfficialRoadmapNode } from '@/services/roadmapOfficialService'

import type { NodeData } from './graph'
import { RoadmapHandles } from './roadmapHandles'
import { internalRoadmapPath } from './roadmapShLinks'

function inlineFromRaw(raw: OfficialRoadmapNode, kind: string): CSSProperties {
  const s = raw.data?.style ?? {}
  const style: CSSProperties = {}

  if (typeof s.fontSize === 'number') style.fontSize = `${s.fontSize}px`
  if (typeof s.textAlign === 'string') style.textAlign = s.textAlign as CSSProperties['textAlign']
  if (typeof s.justifyContent === 'string') {
    style.justifyContent = s.justifyContent as CSSProperties['justifyContent']
  }
  if (typeof s.color === 'string') style.color = s.color
  if (raw.data?.color) style.color = raw.data.color
  if (typeof s.backgroundColor === 'string') style.background = s.backgroundColor
  if (typeof s.borderColor === 'string') style.borderColor = s.borderColor
  if (typeof s.padding === 'number') style.padding = `${s.padding}px`

  if (kind === 'button' && raw.data?.backgroundColor) {
    style.background = raw.data.backgroundColor
  }

  return style
}

function connectorLineStyle(
  raw: OfficialRoadmapNode,
  axis: 'vertical' | 'horizontal',
): CSSProperties {
  const style = raw.data?.style ?? {}
  const stroke = (style.stroke as string) ?? '#2B78E4'
  const width = Number(style.strokeWidth ?? 3.5)
  const dash = style.strokeDasharray as string | undefined
  const lineStyle = dash && dash !== '0' ? 'dashed' : 'solid'

  if (axis === 'vertical') {
    return {
      position: 'absolute',
      top: 0,
      bottom: 0,
      left: `calc(50% - ${width / 2}px)`,
      borderLeft: `${width}px ${lineStyle} ${stroke}`,
    }
  }

  return {
    position: 'absolute',
    left: 0,
    right: 0,
    top: `calc(50% - ${width / 2}px)`,
    borderTop: `${width}px ${lineStyle} ${stroke}`,
  }
}

function VerticalConnector({ data }: NodeProps) {
  const raw = (data as NodeData).raw
  return (
    <div className="ors-connector ors-connector--vertical">
      <span style={connectorLineStyle(raw, 'vertical')} />
    </div>
  )
}

function HorizontalConnector({ data }: NodeProps) {
  const raw = (data as NodeData).raw
  return (
    <div className="ors-connector ors-connector--horizontal">
      <span style={connectorLineStyle(raw, 'horizontal')} />
    </div>
  )
}

function SectionGroup({ data }: NodeProps) {
  const raw = (data as NodeData).raw
  const style = raw.data?.style ?? {}
  const border = (style.borderColor as string) ?? '#0a0a0a'
  const bg = (style.backgroundColor as string) ?? '#fffef8'
  const label = raw.data?.label?.trim()
  return (
    <div className="ors-section" style={{ background: bg, borderColor: border }}>
      {label ? <span className="ors-section-label">{label}</span> : null}
    </div>
  )
}

function classForKind(kind: string): string {
  switch (kind) {
    case 'subtopic':
      return 'ors-node ors-node--subtopic'
    case 'topic':
      return 'ors-node ors-node--topic'
    case 'title':
      return 'ors-node ors-node--title'
    case 'button':
      return 'ors-node ors-node--button'
    case 'paragraph':
      return 'ors-node ors-node ors-node--paragraph'
    case 'label':
      return 'ors-node ors-node--label'
    default:
      return 'ors-node ors-node--other'
  }
}

function RoadmapNodeCard({ data }: NodeProps) {
  const payload = data as NodeData
  const kind = payload.nodeType
  const raw = payload.raw
  const className = classForKind(kind)
  const needsHandles = ['subtopic', 'topic', 'button', 'label', 'paragraph'].includes(kind)
  const inline = inlineFromRaw(raw, kind)

  return (
    <div className={className} style={inline}>
      {needsHandles ? <RoadmapHandles /> : null}
      <span className="ors-node-text">{payload.label}</span>
    </div>
  )
}

function LinksGroupNode({ data }: NodeProps) {
  const raw = (data as NodeData).raw
  const title = raw.data?.label?.trim() ?? 'Related paths'
  const links = raw.data?.links ?? []

  return (
    <div className="ors-linksgroup">
      <RoadmapHandles />
      <p className="ors-linksgroup-title">{title}</p>
      <ul className="ors-linksgroup-list">
        {links.map((link) => {
          const target = internalRoadmapPath(link.url ?? link.href ?? '')
          if (!target) return null
          return (
            <li key={link.id ?? link.label}>
              <Link
                to={target}
                className="ors-linksgroup-link"
                onClick={(event) => event.stopPropagation()}
              >
                {link.label}
              </Link>
            </li>
          )
        })}
      </ul>
    </div>
  )
}

export const nodeTypes: NodeTypes = {
  roadmap: RoadmapNodeCard,
  linksgroup: LinksGroupNode,
  vertical: VerticalConnector,
  horizontal: HorizontalConnector,
  section: SectionGroup,
}
