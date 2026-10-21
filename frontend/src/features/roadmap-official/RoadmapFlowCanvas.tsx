import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { RotateCcw, ZoomIn, ZoomOut } from 'lucide-react'
import {
  Background,
  BackgroundVariant,
  MiniMap,
  Panel,
  ReactFlow,
  useEdgesState,
  useNodesState,
  useReactFlow,
  type Edge,
  type Node,
} from '@xyflow/react'

import { applyNodesDraggable, cloneGraph, type NodeData } from './graph'
import { flowDuration } from './roadmapMotion'
import { nodeTypes } from './roadmapNodes'
import { internalRoadmapPath } from './roadmapShLinks'

const layoutSessions = new Map<string, { nodes: Node[]; edges: Edge[] }>()

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
  const { zoomIn, zoomOut, fitView } = useReactFlow()
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
        onClick={() => fitView({ padding: 0.12, duration: duration(280) })}
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
  onTopicSelect,
  onRoadmapNavigate,
  layoutLocked = false,
  allowedSlugs,
}: RoadmapFlowCanvasProps) {
  const [reduceMotion, setReduceMotion] = useState(false)
  const [minimapOpen, setMinimapOpen] = useState(false)
  const snapshotRef = useRef(cloneGraph(initialNodes, initialEdges))
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)
  const { fitView } = useReactFlow()
  const fittedGraphKeyRef = useRef<string | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const dragMovedRef = useRef(false)
  const loadedKeyRef = useRef<string | null>(null)

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
    fittedGraphKeyRef.current = null
  }, [graphKey, initialNodes, initialEdges, setNodes, setEdges, layoutLocked])

  useEffect(() => {
    setNodes((current) => applyNodesDraggable(current, layoutLocked))
  }, [layoutLocked, setNodes])

  const persistLayout = useCallback(() => {
    layoutSessions.set(graphKey, cloneGraph(nodes, edges))
  }, [graphKey, nodes, edges])

  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const runFitIfReady = () => {
      const { width, height } = el.getBoundingClientRect()
      if (width < 8 || height < 8) return false
      if (fittedGraphKeyRef.current === graphKey) return true
      if (nodes.length === 0) return false
      fittedGraphKeyRef.current = graphKey
      fitView({ padding: 0.14, duration: flowDuration(reduceMotion, 220), maxZoom: 1.05 })
      return true
    }
    if (runFitIfReady()) return
    const observer = new ResizeObserver(() => {
      runFitIfReady()
    })
    observer.observe(el)
    return () => observer.disconnect()
  }, [graphKey, nodes.length, fitView, reduceMotion])

  useEffect(() => {
    if (!focusNodeId) return
    fitView({
      nodes: [{ id: focusNodeId }],
      padding: 0.35,
      duration: flowDuration(reduceMotion, 280),
      maxZoom: 1.25,
    })
  }, [focusNodeId, fitView, reduceMotion])

  const resetLayout = useCallback(() => {
    const snap = cloneGraph(snapshotRef.current.nodes, snapshotRef.current.edges)
    layoutSessions.set(graphKey, snap)
    setNodes(applyNodesDraggable(snap.nodes, layoutLocked))
    setEdges(snap.edges)
    requestAnimationFrame(() =>
      fitView({ padding: 0.12, duration: flowDuration(reduceMotion, 300) }),
    )
  }, [setNodes, setEdges, fitView, layoutLocked, reduceMotion, graphKey])

  const displayEdges = useMemo(
    () =>
      edges.map((edge) => ({
        ...edge,
        animated: reduceMotion ? false : edge.animated,
      })),
    [edges, reduceMotion],
  )

  const displayNodes = useMemo(
    () =>
      nodes.map((node) => ({
        ...node,
        selected: selectedNodeId ? node.id === selectedNodeId : node.selected,
      })),
    [nodes, selectedNodeId],
  )

  const onNodeDragStart = useCallback(() => {
    dragMovedRef.current = false
  }, [])

  const onNodeDrag = useCallback(() => {
    dragMovedRef.current = true
  }, [])

  const onNodeDragStop = useCallback(() => {
    persistLayout()
    window.setTimeout(() => {
      dragMovedRef.current = false
    }, 0)
  }, [persistLayout])

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
        onTopicSelect(raw)
      }
    },
    [onTopicSelect, onRoadmapNavigate, allowedSlugs],
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
        nodes={displayNodes}
        edges={displayEdges}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChangeWrapped}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        onNodeDragStart={onNodeDragStart}
        onNodeDrag={onNodeDrag}
        onNodeDragStop={onNodeDragStop}
        nodesDraggable={!layoutLocked}
        nodeDragThreshold={6}
        panOnDrag
        panOnScroll
        zoomOnScroll
        nodesConnectable={false}
        elementsSelectable
        deleteKeyCode={null}
        minZoom={0.15}
        maxZoom={2}
        proOptions={{ hideAttribution: true }}
        defaultEdgeOptions={{ type: 'smoothstep' }}
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={20}
          size={1}
          color="var(--ors-paper-dot)"
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
