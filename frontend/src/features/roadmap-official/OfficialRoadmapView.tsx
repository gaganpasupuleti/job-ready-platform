import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
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
import { filterOutlineNodes } from './graphValidation'
import { RoadmapFlowCanvas } from './RoadmapFlowCanvas'
import { RoadmapMobileTopicDialog } from './RoadmapMobileTopicDialog'
import { RoadmapOutline } from './RoadmapOutline'
import { RoadmapTopicPanel } from './RoadmapTopicPanel'
import './official-roadmap.css'

interface OfficialRoadmapViewProps {
  slug: string
  title?: string
  description?: string
}

function isMobileViewport() {
  return window.matchMedia('(max-width: 900px)').matches
}

export function OfficialRoadmapView({ slug, title, description }: OfficialRoadmapViewProps) {
  const navigate = useNavigate()
  const [selected, setSelected] = useState<OfficialRoadmapNode | null>(null)
  const [layoutLocked, setLayoutLocked] = useState(false)
  const [outlineOpen, setOutlineOpen] = useState(true)
  const [mobileTopicOpen, setMobileTopicOpen] = useState(false)
  const [outlineQuery, setOutlineQuery] = useState('')
  const [cameraFocusId, setCameraFocusId] = useState<string | null>(null)
  const freezeRoadmapViewportRef = useRef<(() => void) | null>(null)

  const catalogQuery = useQuery({
    queryKey: ['roadmap-catalog'],
    queryFn: fetchRoadmapCatalog,
    staleTime: 60_000,
  })

  const allowedSlugs = useMemo(
    () => new Set((catalogQuery.data?.roadmaps ?? []).map((row) => row.family_slug)),
    [catalogQuery.data],
  )

  const catalogRow = useMemo(
    () => catalogQuery.data?.roadmaps.find((row) => row.family_slug === slug),
    [catalogQuery.data, slug],
  )

  useEffect(() => {
    setSelected(null)
    setMobileTopicOpen(false)
    setOutlineQuery('')
    setCameraFocusId(null)
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

  const onTopicSelect = useCallback((raw: OfficialRoadmapNode, focusCamera = false) => {
    if (!focusCamera) {
      freezeRoadmapViewportRef.current?.()
    }
    setSelected(raw)
    if (focusCamera) setCameraFocusId(raw.id)
    if (isMobileViewport()) setMobileTopicOpen(true)
  }, [])

  const closeArticle = useCallback(() => {
    setSelected(null)
    setMobileTopicOpen(false)
  }, [])

  useEffect(() => {
    if (!cameraFocusId) return
    const timer = window.setTimeout(() => setCameraFocusId(null), 450)
    return () => window.clearTimeout(timer)
  }, [cameraFocusId])

  const pageTitle =
    title ??
    catalogRow?.title ??
    graphQuery.data?.title?.page ??
    graphQuery.data?.title?.card ??
    slug.replace(/-/g, ' ')

  const pageDescription =
    description ??
    catalogRow?.description ??
    'Explore topics on the map. Select any topic to read notes when available.'

  const topicErrorKind = useMemo((): 'none' | 'missing' | 'network' | 'session' => {
    if (!selected || topicQuery.isLoading || topicQuery.data) return 'none'
    if (!topicQuery.isError) return 'none'
    if (axios.isAxiosError(topicQuery.error)) {
      if (topicQuery.error.response?.status === 401) return 'session'
      if (topicQuery.error.response?.status === 403) return 'session'
      if (topicQuery.error.response?.status === 404) return 'missing'
    }
    return 'network'
  }, [selected, topicQuery.isLoading, topicQuery.data, topicQuery.isError, topicQuery.error])

  const searchMatches = useMemo(
    () => filterOutlineNodes(graphQuery.data?.nodes ?? [], outlineQuery),
    [graphQuery.data, outlineQuery],
  )

  const articleOpen = Boolean(selected)
  const layoutClass = [
    'ors-layout',
    outlineOpen ? 'ors-layout--outline-open' : 'ors-layout--outline-closed',
    articleOpen ? 'ors-layout--article-open' : 'ors-layout--article-closed',
  ].join(' ')

  if (graphQuery.isLoading) {
    return <p className="ors-status">Loading roadmap…</p>
  }

  if (graphQuery.isError || !graphQuery.data) {
    const message =
      graphQuery.error instanceof RoadmapGraphError
        ? graphQuery.error.message
        : 'Could not load this roadmap. Check your connection or try again.'
    return (
      <div className="ors-page ors-page--centered">
        <p className="ors-alert" role="alert">{message}</p>
        <div className="ors-inline-actions">
          <Button type="button" variant="secondary" onClick={() => graphQuery.refetch()}>
            Retry
          </Button>
          <Link to="/roadmaps" className="ors-text-link">All roadmaps</Link>
        </div>
      </div>
    )
  }

  return (
    <div className="ors-page">
      <header className="ors-header">
        <nav className="ors-breadcrumb" aria-label="Breadcrumb">
          <Link to="/roadmaps">Roadmaps</Link>
          <span aria-hidden="true">/</span>
          <span>{pageTitle}</span>
        </nav>
        <h1 className="ors-title">{pageTitle}</h1>
        <p className="ors-sub">{pageDescription}</p>
      </header>

      <div className="ors-toolbar" role="toolbar" aria-label="Roadmap tools">
        <button
          type="button"
          className="ors-toolbar-btn"
          aria-expanded={outlineOpen}
          onClick={() => setOutlineOpen((open) => !open)}
        >
          {outlineOpen ? 'Hide outline' : 'Show outline'}
        </button>
        <input
          type="search"
          className="ors-toolbar-search"
          placeholder="Find topic"
          value={outlineQuery}
          onChange={(event) => setOutlineQuery(event.target.value)}
          aria-label="Find topic in outline"
        />
        <label className="ors-toggle">
          <input
            type="checkbox"
            checked={layoutLocked}
            onChange={(event) => setLayoutLocked(event.target.checked)}
          />
          Lock layout
        </label>
      </div>

      {outlineQuery.trim() ? (
        <div className="ors-topic-search-results" role="region" aria-label="Topic search results">
          {searchMatches.length === 0 ? (
            <p className="ors-muted">No topics match your search.</p>
          ) : (
            <ul className="ors-topic-search-list">
              {searchMatches.slice(0, 15).map((node) => (
                <li key={node.id}>
                  <button
                    type="button"
                    className="ors-topic-search-item"
                    onClick={() => onTopicSelect(node, true)}
                  >
                    {node.data?.label}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      ) : null}

      <div className={layoutClass}>
        {outlineOpen ? (
          <aside className="ors-outline-panel" aria-label="Topic outline">
            <RoadmapOutline
              nodes={graphQuery.data.nodes}
              selectedId={selected?.id ?? null}
              filter={outlineQuery}
              onSelect={(raw) => onTopicSelect(raw, true)}
            />
          </aside>
        ) : null}

        <div className={layoutLocked ? 'ors-canvas ors-canvas--locked' : 'ors-canvas ors-canvas--explore'}>
          <ReactFlowProvider>
            <RoadmapFlowCanvas
              graphKey={slug}
              initialNodes={flow.nodes}
              initialEdges={flow.edges}
              focusNodeId={cameraFocusId}
              selectedNodeId={selected?.id ?? null}
              articlePanelOpen={articleOpen}
              freezeViewportRef={freezeRoadmapViewportRef}
              onTopicSelect={onTopicSelect}
              onRoadmapNavigate={(path) => navigate(path)}
              layoutLocked={layoutLocked}
              allowedSlugs={allowedSlugs}
            />
          </ReactFlowProvider>
        </div>

        {articleOpen ? (
          <aside className="ors-panel ors-panel--desktop" aria-label="Topic details">
            <RoadmapTopicPanel
              selected={selected}
              topicMarkdown={topicQuery.data?.markdown}
              topicAttribution={topicQuery.data?.attribution}
              isLoading={topicQuery.isLoading}
              errorKind={topicErrorKind}
              allowedSlugs={allowedSlugs}
              onRetry={() => topicQuery.refetch()}
              onClose={closeArticle}
            />
          </aside>
        ) : null}
      </div>

      <RoadmapMobileTopicDialog
        open={mobileTopicOpen && Boolean(selected)}
        onClose={() => setMobileTopicOpen(false)}
        label="Topic details"
      >
        <RoadmapTopicPanel
          selected={selected}
          topicMarkdown={topicQuery.data?.markdown}
          topicAttribution={topicQuery.data?.attribution}
          isLoading={topicQuery.isLoading}
          errorKind={topicErrorKind}
          allowedSlugs={allowedSlugs}
          onRetry={() => topicQuery.refetch()}
          onClose={() => setMobileTopicOpen(false)}
          closeButtonDataAttr
        />
      </RoadmapMobileTopicDialog>
    </div>
  )
}
