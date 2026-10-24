import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
  type MutableRefObject,
} from 'react'
import { RotateCcw, ZoomIn, ZoomOut } from 'lucide-react'
import {
  Background,
  BackgroundVariant,
  MiniMap,
  Panel,
  ReactFlow,
  useEdgesState,
  useNodesInitialized,
  useNodesState,
  useReactFlow,
  type Edge,
  type FitViewOptions,
  type Node,
  type Viewport,
} from '@xyflow/react'

import { applyNodesDraggable, cloneGraph, type NodeData } from './graph'
import { flowDuration } from './roadmapMotion'
import { nodeTypes } from './roadmapNodes'
import { internalRoadmapPath } from './roadmapShLinks'

const layoutSessions = new Map<string, { nodes: Node[]; edges: Edge[] }>()

const LAYOUT_SPACER_TYPES = new Set(['vertical', 'horizontal'])

function contentNodesForFit(nodes: Node[]) {
  return nodes.filter((node) => !LAYOUT_SPACER_TYPES.has((node.data as NodeData).nodeType))
}

function roadmapOverviewFitOptions(reduceMotion: boolean, durationMs = 220): FitViewOptions {
  return {
    padding: 0.22,
    duration: flowDuration(reduceMotion, durationMs),
    minZoom: 0.55,
    maxZoom: 1,
  }
}

function layoutGuardActive(
  guard: { until: number; snapshot: Viewport } | null,
  userNavigating: boolean,
) {
  return Boolean(guard && !userNavigating && Date.now() < guard.until)
}

function RoadmapViewportFit({
  graphKey,
  focusNodeId,
  reduceMotion,
  resetToken,
  articlePanelOpen,
  layoutGuardRef,
  userNavigatingRef,
}: {
  graphKey: string
  focusNodeId?: string | null
  reduceMotion: boolean
  resetToken: number
  articlePanelOpen: boolean
  layoutGuardRef: MutableRefObject<{ until: number; snapshot: Viewport } | null>
  userNavigatingRef: MutableRefObject<boolean>
}) {
  const { fitView, getNodes } = useReactFlow()
  const nodesInitialized = useNodesInitialized()
  const fitScopeRef = useRef('')

  const fitOverview = useCallback(() => {
    if (articlePanelOpen || layoutGuardActive(layoutGuardRef.current, userNavigatingRef.current)) {
      return
    }
    const content = contentNodesForFit(getNodes())
    if (content.length === 0) return
    fitView({
      nodes: content.map((node) => ({ id: node.id })),
      ...roadmapOverviewFitOptions(reduceMotion),
    })
  }, [articlePanelOpen, fitView, getNodes, reduceMotion, layoutGuardRef, userNavigatingRef])

  useEffect(() => {
    if (!nodesInitialized) return
    if (fitScopeRef.current === graphKey) return
    fitScopeRef.current = graphKey
    const run = () => fitOverview()
    requestAnimationFrame(() => requestAnimationFrame(run))
  }, [graphKey, nodesInitialized, fitOverview])

  useEffect(() => {
    if (!nodesInitialized || resetToken === 0 || articlePanelOpen) return
    requestAnimationFrame(() => fitOverview())
  }, [resetToken, nodesInitialized, fitOverview, articlePanelOpen])

  useEffect(() => {
    if (!focusNodeId || !nodesInitialized) return
    fitView({
      nodes: [{ id: focusNodeId }],
      padding: 0.3,
      duration: flowDuration(reduceMotion, 280),
      minZoom: 0.65,
      maxZoom: 1.15,
    })
  }, [focusNodeId, fitView, reduceMotion, nodesInitialized])

  return null
}

function RoadmapControls({
  onReset,
  reduceMotion,
  minimapOpen,
  onToggleMinimap,
}: {
  onReset: () => void
  reduceMotion: boolean
  minimapOpen: boolean
  onToggleMinimap: () => void
}) {
  const { zoomIn, zoomOut, fitView, getNodes } = useReactFlow()
  const duration = (ms: number) => flowDuration(reduceMotion, ms)

  return (
    <Panel position="bottom-left" className="ors-controls">
      <button
        type="button"
        className="ors-controls-btn"
        onClick={() => zoomIn({ duration: duration(200) })}
        aria-label="Zoom in"
      >
        <ZoomIn size={16} />
      </button>
      <button
        type="button"
        className="ors-controls-btn"
        onClick={onReset}
        aria-label="Reset layout to original"
        title="Reset layout"
      >
        <RotateCcw size={16} />
      </button>
      <button
        type="button"
        className="ors-controls-btn"
        onClick={() => zoomOut({ duration: duration(200) })}
        aria-label="Zoom out"
      >
        <ZoomOut size={16} />
      </button>
      <button
        type="button"
        className="ors-controls-btn"
        onClick={() => {
          const content = contentNodesForFit(getNodes())
          fitView({
            nodes: content.map((node) => ({ id: node.id })),
            ...roadmapOverviewFitOptions(reduceMotion, 280),
          })
        }}
        aria-label="Fit overview"
        title="Fit overview"
      >
        ⛶
      </button>
      <button
        type="button"
        className="ors-controls-btn"
        onClick={onToggleMinimap}
        aria-label={minimapOpen ? 'Hide minimap' : 'Show minimap'}
        title={minimapOpen ? 'Hide minimap' : 'Show minimap'}
      >
        ◫
      </button>
    </Panel>
  )
}

interface RoadmapFlowCanvasProps {
  graphKey: string
  initialNodes: Node[]
  initialEdges: Edge[]
  focusNodeId?: string | null
  selectedNodeId?: string | null
  articlePanelOpen?: boolean
  onTopicSelect: (raw: import('@/services/roadmapOfficialService').OfficialRoadmapNode) => void
  onRoadmapNavigate: (path: string) => void
  layoutLocked?: boolean
  allowedSlugs?: ReadonlySet<string>
}

export function RoadmapFlowCanvas({
  graphKey,
  initialNodes,
  initialEdges,
  focusNodeId,
  selectedNodeId,
  articlePanelOpen = false,
  onTopicSelect,
  onRoadmapNavigate,
  layoutLocked = false,
  allowedSlugs,
}: RoadmapFlowCanvasProps) {
  const [reduceMotion, setReduceMotion] = useState(false)
  const [minimapOpen, setMinimapOpen] = useState(false)
  const [resetToken, setResetToken] = useState(0)
  const snapshotRef = useRef(cloneGraph(initialNodes, initialEdges))
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)
  const { getNodes, getEdges, getViewport, setViewport } = useReactFlow()
  const containerRef = useRef<HTMLDivElement>(null)
  const dragMovedRef = useRef(false)
  const loadedKeyRef = useRef<string | null>(null)
  const layoutGuardRef = useRef<{ until: number; snapshot: Viewport } | null>(null)
  const userNavigatingRef = useRef(false)
  const articlePanelOpenRef = useRef(articlePanelOpen)

  const beginLayoutTransition = useCallback(() => {
    userNavigatingRef.current = false
    layoutGuardRef.current = {
      until: Date.now() + 750,
      snapshot: getViewport(),
    }
  }, [getViewport])

  useLayoutEffect(() => {
    if (articlePanelOpenRef.current === articlePanelOpen) return
    articlePanelOpenRef.current = articlePanelOpen
    beginLayoutTransition()
  }, [articlePanelOpen, beginLayoutTransition])

  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const observer = new ResizeObserver(() => {
      const guard = layoutGuardRef.current
      if (!layoutGuardActive(guard, userNavigatingRef.current) || !guard) return
      setViewport(guard.snapshot)
    })
    observer.observe(el)
    return () => observer.disconnect()
  }, [setViewport])

  const onMoveStart = useCallback(() => {
    userNavigatingRef.current = true
    layoutGuardRef.current = null
  }, [])

  useEffect(() => {
    const media = window.matchMedia('(prefers-reduced-motion: reduce)')
    const update = () => setReduceMotion(media.matches)
    update()
    media.addEventListener('change', update)
    return () => media.removeEventListener('change', update)
  }, [])

  useEffect(() => {
    snapshotRef.current = cloneGraph(initialNodes, initialEdges)
  }, [initialNodes, initialEdges])

  useEffect(() => {
    if (loadedKeyRef.current === graphKey) return
    loadedKeyRef.current = graphKey
    const cached = layoutSessions.get(graphKey)
    const base = cached ?? snapshotRef.current
    if (!cached) {
      layoutSessions.set(graphKey, cloneGraph(base.nodes, base.edges))
    }
    setNodes(applyNodesDraggable(base.nodes, layoutLocked))
    setEdges(base.edges.map((edge) => ({ ...edge })))
  }, [graphKey, initialNodes, initialEdges, layoutLocked, setNodes, setEdges])

  useEffect(() => {
    setNodes((current) => applyNodesDraggable(current, layoutLocked))
  }, [layoutLocked, setNodes])

  useEffect(() => {
    if (!selectedNodeId) {
      setNodes((current) => current.map((node) => (node.selected ? { ...node, selected: false } : node)))
      return
    }
    setNodes((current) =>
      current.map((node) => ({
        ...node,
        selected: node.id === selectedNodeId,
      })),
    )
  }, [selectedNodeId, setNodes])

  const resetLayout = useCallback(() => {
    const snap = cloneGraph(snapshotRef.current.nodes, snapshotRef.current.edges)
    layoutSessions.set(graphKey, snap)
    setNodes(applyNodesDraggable(snap.nodes, layoutLocked))
    setEdges(snap.edges)
    setResetToken((token) => token + 1)
  }, [setNodes, setEdges, layoutLocked, graphKey])

  const displayEdges = useMemo(
    () =>
      edges.map((edge) => ({
        ...edge,
        animated: reduceMotion ? false : edge.animated,
      })),
    [edges, reduceMotion],
  )

  const onNodeDragStart = useCallback(() => {
    dragMovedRef.current = false
  }, [])

  const onNodeDrag = useCallback(() => {
    dragMovedRef.current = true
  }, [])

  const onNodeDragStop = useCallback(() => {
    layoutSessions.set(graphKey, cloneGraph(getNodes(), getEdges()))
    window.setTimeout(() => {
      dragMovedRef.current = false
    }, 0)
  }, [graphKey, getNodes, getEdges])

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      if (dragMovedRef.current) return
      const raw = (node.data as { raw?: import('@/services/roadmapOfficialService').OfficialRoadmapNode })
        .raw
      if (!raw) return
      const t = raw.type
      if (t === 'button') {
        const href = raw.data?.href ?? ''
        const path = internalRoadmapPath(href, allowedSlugs)
        if (path) {
          onRoadmapNavigate(path)
          return
        }
        if (href.startsWith('http')) {
          window.open(href, '_blank', 'noopener,noreferrer')
          return
        }
      }
      if (t === 'subtopic' || t === 'topic') {
        beginLayoutTransition()
        onTopicSelect(raw)
      }
    },
    [onTopicSelect, onRoadmapNavigate, allowedSlugs, beginLayoutTransition],
  )

  const onNodesChangeWrapped = useCallback(
    (changes: import('@xyflow/react').NodeChange[]) => {
      onNodesChange(changes)
    },
    [onNodesChange],
  )

  return (
    <div ref={containerRef} className="ors-flow-host">
      <ReactFlow
        nodes={nodes}
        edges={displayEdges}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChangeWrapped}
        onEdgesChange={onEdgesChange}
        onMoveStart={onMoveStart}
        onNodeClick={onNodeClick}
        onNodeDragStart={onNodeDragStart}
        onNodeDrag={onNodeDrag}
        onNodeDragStop={onNodeDragStop}
        nodesDraggable={!layoutLocked}
        nodeDragThreshold={10}
        autoPanOnNodeDrag={false}
        onlyRenderVisibleElements
        panOnDrag
        panOnScroll
        selectNodesOnDrag={false}
        zoomOnScroll
        zoomOnPinch
        nodesConnectable={false}
        elementsSelectable
        deleteKeyCode={null}
        minZoom={0.35}
        maxZoom={1.75}
        proOptions={{ hideAttribution: true }}
        defaultEdgeOptions={{ type: 'smoothstep' }}
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={20}
          size={1}
          color="var(--ors-paper-dot)"
        />
        <RoadmapViewportFit
          graphKey={graphKey}
          focusNodeId={focusNodeId}
          reduceMotion={reduceMotion}
          resetToken={resetToken}
          articlePanelOpen={articlePanelOpen}
          layoutGuardRef={layoutGuardRef}
          userNavigatingRef={userNavigatingRef}
        />
        <RoadmapControls
          onReset={resetLayout}
          reduceMotion={reduceMotion}
          minimapOpen={minimapOpen}
          onToggleMinimap={() => setMinimapOpen((open) => !open)}
        />
        {minimapOpen ? (
          <MiniMap
            pannable
            zoomable
            className="ors-minimap"
            maskColor="var(--ors-minimap-mask)"
            nodeColor={(node) => {
              const kind = (node.data as NodeData).nodeType
              if (kind === 'topic') return 'var(--ors-milestone)'
              if (kind === 'subtopic') return 'var(--ors-subtopic)'
              if (kind === 'button') return 'var(--color-border)'
              return 'var(--color-text-subtle)'
            }}
          />
        ) : null}
      </ReactFlow>
    </div>
  )
}
