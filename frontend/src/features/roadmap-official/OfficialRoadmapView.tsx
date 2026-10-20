import { useCallback, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ReactFlowProvider } from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { useQuery } from '@tanstack/react-query'
import { marked } from 'marked'

import {
  fetchOfficialRoadmapGraph,
  fetchOfficialTopic,
  type OfficialRoadmapNode,
} from '@/services/roadmapOfficialService'

import { buildFlowGraph } from './graph'
import { RoadmapFlowCanvas } from './RoadmapFlowCanvas'
import { rewriteRoadmapShMarkdown } from './roadmapShLinks'
import './official-roadmap.css'

interface OfficialRoadmapViewProps {
  slug: string
  title?: string
}

export function OfficialRoadmapView({ slug, title }: OfficialRoadmapViewProps) {
  const navigate = useNavigate()
  const [selected, setSelected] = useState<OfficialRoadmapNode | null>(null)

  const graphQuery = useQuery({
    queryKey: ['official-roadmap-graph', slug],
    queryFn: () => fetchOfficialRoadmapGraph(slug),
  })

  const topicQuery = useQuery({
    queryKey: ['official-roadmap-topic', slug, selected?.id, selected?.data?.oldId],
    queryFn: () =>
      fetchOfficialTopic(slug, selected!.id, selected?.data?.oldId ?? undefined),
    enabled: Boolean(selected?.id),
    retry: false,
  })

  const flow = useMemo(() => {
    if (!graphQuery.data) return { nodes: [], edges: [] }
    return buildFlowGraph(graphQuery.data.nodes, graphQuery.data.edges)
  }, [graphQuery.data])

  const onTopicSelect = useCallback((raw: OfficialRoadmapNode) => {
    setSelected(raw)
  }, [])

  const pageTitle =
    title ??
    graphQuery.data?.title?.page ??
    graphQuery.data?.title?.card ??
    slug.replace(/-/g, ' ')

  if (graphQuery.isLoading) {
    return <p className="text-sm text-[var(--color-text-muted)] p-4">Loading roadmap…</p>
  }

  if (graphQuery.isError || !graphQuery.data) {
    return (
      <div className="module-page space-y-2 p-4">
        <p className="text-sm text-[var(--color-danger)]" role="alert">
          Could not load this roadmap. Check your connection or try again in a moment.
        </p>
        <Link to="/roadmaps" className="text-sm text-[var(--color-accent)]">Back</Link>
      </div>
    )
  }

  const topicHtml = topicQuery.data?.markdown
    ? marked.parse(rewriteRoadmapShMarkdown(topicQuery.data.markdown), { async: false })
    : ''

  return (
    <div className="ors-page">
      <header className="ors-header">
        <div>
          <p className="ors-kicker">JobReady career path</p>
          <h1 className="ors-title">{pageTitle}</h1>
          <p className="ors-sub">
            Drag boxes to explore. Reset (under +) restores the original layout. Click a yellow or
            peach topic for notes on the right.
          </p>
        </div>
        <Link to="/roadmaps" className="ors-back">All roadmaps</Link>
      </header>

      <div className="ors-layout">
        <div className="ors-canvas">
          <ReactFlowProvider>
            <RoadmapFlowCanvas
              initialNodes={flow.nodes}
              initialEdges={flow.edges}
              onTopicSelect={onTopicSelect}
              onRoadmapNavigate={(path) => navigate(path)}
            />
          </ReactFlowProvider>
        </div>

        <aside className="ors-panel" aria-label="Topic details">
          {!selected ? (
            <p className="ors-panel-empty">Select a topic or subtopic on the map.</p>
          ) : (
            <>
              <h2 className="ors-panel-title">{selected.data?.label ?? 'Topic'}</h2>
              {topicQuery.isLoading ? <p className="text-sm">Loading topic…</p> : null}
              {topicQuery.isError ? (
                <p className="text-sm text-[var(--color-text-muted)]">
                  Topic text needs the JobReady backend running (local markdown). The map still works
                  without it.
                </p>
              ) : null}
              {topicQuery.data ? (
                <article
                  className="ors-markdown prose prose-sm max-w-none"
                  dangerouslySetInnerHTML={{ __html: topicHtml }}
                />
              ) : null}
            </>
          )}
        </aside>
      </div>
    </div>
  )
}
