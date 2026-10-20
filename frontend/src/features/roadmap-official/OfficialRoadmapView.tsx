import { useCallback, useEffect, useMemo, useState } from 'react'
import axios from 'axios'
import { Link, useNavigate } from 'react-router-dom'
import { ReactFlowProvider } from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { useQuery } from '@tanstack/react-query'

import { Button } from '@/components/common/Button'
import {
  fetchOfficialRoadmapGraph,
  fetchOfficialTopic,
  RoadmapGraphError,
  type OfficialRoadmapNode,
} from '@/services/roadmapOfficialService'
import { fetchRoadmapCatalog } from '@/services/roadmapService'

import { buildFlowGraph } from './graph'
import { RoadmapFlowCanvas } from './RoadmapFlowCanvas'
import { RoadmapOutline } from './RoadmapOutline'
import { RoadmapTopicPanel } from './RoadmapTopicPanel'
import './official-roadmap.css'

interface OfficialRoadmapViewProps {
  slug: string
  title?: string
}

export function OfficialRoadmapView({ slug, title }: OfficialRoadmapViewProps) {
  const navigate = useNavigate()
  const [selected, setSelected] = useState<OfficialRoadmapNode | null>(null)
  const [editLayout, setEditLayout] = useState(false)
  const [outlineOpen, setOutlineOpen] = useState(true)
  const [mobileTopicOpen, setMobileTopicOpen] = useState(false)

  const catalogQuery = useQuery({
    queryKey: ['roadmap-catalog'],
    queryFn: fetchRoadmapCatalog,
    staleTime: 60_000,
  })

  const allowedSlugs = useMemo(
    () => new Set((catalogQuery.data?.roadmaps ?? []).map((row) => row.family_slug)),
    [catalogQuery.data],
  )

  useEffect(() => {
    setSelected(null)
    setMobileTopicOpen(false)
  }, [slug])

  const graphQuery = useQuery({
    queryKey: ['official-roadmap-graph', slug],
    queryFn: () => fetchOfficialRoadmapGraph(slug),
    retry: 1,
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
    setMobileTopicOpen(true)
  }, [])

  const pageTitle =
    title ??
    graphQuery.data?.title?.page ??
    graphQuery.data?.title?.card ??
    slug.replace(/-/g, ' ')

  const topicErrorKind = useMemo((): 'none' | 'missing' | 'network' | 'session' => {
    if (!selected || topicQuery.isLoading || topicQuery.data) return 'none'
    if (!topicQuery.isError) return 'none'
    if (axios.isAxiosError(topicQuery.error)) {
      if (topicQuery.error.response?.status === 401) return 'session'
      if (topicQuery.error.response?.status === 404) return 'missing'
    }
    return 'network'
  }, [selected, topicQuery.isLoading, topicQuery.data, topicQuery.isError, topicQuery.error])

  if (graphQuery.isLoading) {
    return <p className="text-sm text-[var(--color-text-muted)] p-4">Loading roadmap…</p>
  }

  if (graphQuery.isError || !graphQuery.data) {
    const message =
      graphQuery.error instanceof RoadmapGraphError
        ? graphQuery.error.message
        : 'Could not load this roadmap. Check your connection or try again.'
    return (
      <div className="module-page space-y-3 p-4">
        <p className="text-sm text-[var(--color-danger)]" role="alert">{message}</p>
        <div className="flex flex-wrap gap-2">
          <Button type="button" variant="secondary" onClick={() => graphQuery.refetch()}>
            Retry
          </Button>
          <Link to="/roadmaps" className="text-sm text-[var(--color-accent)]">All roadmaps</Link>
        </div>
      </div>
    )
  }

  return (
    <div className="ors-page">
      <header className="ors-header">
        <div>
          <p className="ors-kicker">JobReady career path</p>
          <h1 className="ors-title">{pageTitle}</h1>
          <p className="ors-sub">
            Pan and zoom to explore. Pick a topic on the map or in the outline. Layout editing is
            optional.
          </p>
        </div>
        <div className="ors-header-actions">
          <label className="ors-toggle">
            <input
              type="checkbox"
              checked={editLayout}
              onChange={(event) => setEditLayout(event.target.checked)}
            />
            Rearrange layout
          </label>
          <Link to="/roadmaps" className="ors-back">All roadmaps</Link>
        </div>
      </header>

      <div className="ors-toolbar">
        <button
          type="button"
          className="ors-toolbar-btn"
          aria-expanded={outlineOpen}
          onClick={() => setOutlineOpen((open) => !open)}
        >
          {outlineOpen ? 'Hide outline' : 'Show outline'}
        </button>
      </div>

      <div className="ors-layout">
        {outlineOpen ? (
          <aside className="ors-outline-panel" aria-label="Topic outline">
            <RoadmapOutline
              nodes={graphQuery.data.nodes}
              selectedId={selected?.id ?? null}
              onSelect={onTopicSelect}
            />
          </aside>
        ) : null}

        <div className="ors-canvas">
          <ReactFlowProvider>
            <RoadmapFlowCanvas
              initialNodes={flow.nodes}
              initialEdges={flow.edges}
              onTopicSelect={onTopicSelect}
              onRoadmapNavigate={(path) => navigate(path)}
              nodesDraggable={editLayout}
              allowedSlugs={allowedSlugs}
            />
          </ReactFlowProvider>
        </div>

        <aside className="ors-panel ors-panel--desktop" aria-label="Topic details">
          <RoadmapTopicPanel
            selected={selected}
            topicMarkdown={topicQuery.data?.markdown}
            topicAttribution={topicQuery.data?.attribution}
            isLoading={topicQuery.isLoading}
            errorKind={topicErrorKind}
          />
        </aside>
      </div>

      {mobileTopicOpen && selected ? (
        <div className="ors-mobile-sheet" role="dialog" aria-modal="true" aria-label="Topic details">
          <div className="ors-mobile-sheet-backdrop" onClick={() => setMobileTopicOpen(false)} />
          <div className="ors-mobile-sheet-panel">
            <RoadmapTopicPanel
              selected={selected}
              topicMarkdown={topicQuery.data?.markdown}
              topicAttribution={topicQuery.data?.attribution}
              isLoading={topicQuery.isLoading}
              errorKind={topicErrorKind}
              onClose={() => setMobileTopicOpen(false)}
            />
          </div>
        </div>
      ) : null}
    </div>
  )
}
