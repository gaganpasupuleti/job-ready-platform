import type { OfficialRoadmapNode } from '@/services/roadmapOfficialService'

interface RoadmapOutlineProps {
  nodes: OfficialRoadmapNode[]
  selectedId: string | null
  onSelect: (node: OfficialRoadmapNode) => void
}

function outlineEntries(nodes: OfficialRoadmapNode[]) {
  return nodes
    .filter((node) => {
      const t = node.type
      return t === 'topic' || t === 'subtopic'
    })
    .map((node) => ({
      id: node.id,
      label: node.data?.label?.trim() ?? 'Topic',
      kind: node.type === 'topic' ? 'topic' : 'subtopic',
      raw: node,
    }))
    .filter((row) => row.label.length > 0)
}

export function RoadmapOutline({ nodes, selectedId, onSelect }: RoadmapOutlineProps) {
  const entries = outlineEntries(nodes)

  if (entries.length === 0) {
    return <p className="ors-outline-empty">No topics listed for this roadmap.</p>
  }

  return (
    <nav className="ors-outline" aria-label="Topic outline">
      <ul>
        {entries.map((entry) => (
          <li key={entry.id}>
            <button
              type="button"
              className={
                entry.kind === 'topic' ? 'ors-outline-btn ors-outline-btn--topic' : 'ors-outline-btn'
              }
              aria-current={selectedId === entry.id ? 'true' : undefined}
              onClick={() => onSelect(entry.raw)}
            >
              {entry.label}
            </button>
          </li>
        ))}
      </ul>
    </nav>
  )
}
