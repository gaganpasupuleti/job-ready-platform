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

function RoadmapControls({
  onReset,
  reduceMotion,
}: {
  onReset: () => void
  reduceMotion: boolean
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
        onClick={() => fitView({ padding: 0.1, duration: duration(280) })}
        aria-label="Fit overview"
        title="Fit overview"
      >
        ⛶
      </button>
    </Panel>
  )
}

interface RoadmapFlowCanvasProps {
  graphKey: string
  initialNodes: Node[]
  initialEdges: Edge[]
  focusNodeId?: string | null
  onTopicSelect: (raw: import('@/services/roadmapOfficialService').OfficialRoadmapNode) => void
  onRoadmapNavigate: (path: string) => void
  nodesDraggable?: boolean
  allowedSlugs?: ReadonlySet<string>
}

export function RoadmapFlowCanvas({
  graphKey,
  initialNodes,
  initialEdges,
  focusNodeId,
  onTopicSelect,
  onRoadmapNavigate,
  nodesDraggable = false,
  allowedSlugs,
}: RoadmapFlowCanvasProps) {
  const [reduceMotion, setReduceMotion] = useState(false)
  const snapshotRef = useRef(cloneGraph(initialNodes, initialEdges))
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)
  const { fitView } = useReactFlow()
  const lastGraphKeyRef = useRef(graphKey)

  useEffect(() => {
    const media = window.matchMedia('(prefers-reduced-motion: reduce)')
    const update = () => setReduceMotion(media.matches)
    update()
    media.addEventListener('change', update)
    return () => media.removeEventListener('change', update)
  }, [])

  useEffect(() => {
    const snap = cloneGraph(initialNodes, initialEdges)
    snapshotRef.current = snap
    setNodes(applyNodesDraggable(snap.nodes, nodesDraggable))
    setEdges(snap.edges)
  }, [initialNodes, initialEdges, setNodes, setEdges, nodesDraggable])

  useEffect(() => {
    setNodes((current) => applyNodesDraggable(current, nodesDraggable))
  }, [nodesDraggable, setNodes])

  useEffect(() => {
    if (lastGraphKeyRef.current === graphKey) return
    lastGraphKeyRef.current = graphKey
    const timer = window.setTimeout(
      () => fitView({ padding: 0.1, duration: flowDuration(reduceMotion, 200) }),
      80,
    )
    return () => window.clearTimeout(timer)
  }, [graphKey, fitView, reduceMotion])

  useEffect(() => {
    if (!focusNodeId) return
    const timer = window.setTimeout(() => {
      fitView({
        nodes: [{ id: focusNodeId }],
        padding: 0.35,
        duration: flowDuration(reduceMotion, 280),
        maxZoom: 1.25,
      })
    }, 40)
    return () => window.clearTimeout(timer)
  }, [focusNodeId, fitView, reduceMotion])

  const resetLayout = useCallback(() => {
    const snap = cloneGraph(snapshotRef.current.nodes, snapshotRef.current.edges)
    setNodes(applyNodesDraggable(snap.nodes, nodesDraggable))
    setEdges(snap.edges)
    window.setTimeout(
      () => fitView({ padding: 0.1, duration: flowDuration(reduceMotion, 300) }),
      40,
    )
  }, [setNodes, setEdges, fitView, nodesDraggable, reduceMotion])

  const displayEdges = useMemo(
    () =>
      edges.map((edge) => ({
        ...edge,
        animated: reduceMotion ? false : edge.animated,
      })),
    [edges, reduceMotion],
  )

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
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

  return (
    <ReactFlow
      nodes={nodes}
      edges={displayEdges}
      nodeTypes={nodeTypes}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onNodeClick={onNodeClick}
      nodesDraggable={nodesDraggable}
      panOnDrag
      zoomOnScroll
      nodesConnectable={false}
      elementsSelectable
      deleteKeyCode={null}
      minZoom={0.2}
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
      <RoadmapControls onReset={resetLayout} reduceMotion={reduceMotion} />
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
    </ReactFlow>
  )
}
