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

import { cloneGraph, type NodeData } from './graph'
import { nodeTypes } from './roadmapNodes'
import { internalRoadmapPath } from './roadmapShLinks'

function RoadmapControls({ onReset }: { onReset: () => void }) {
  const { zoomIn, zoomOut, fitView } = useReactFlow()

  return (
    <Panel position="bottom-left" className="ors-controls">
      <button type="button" className="ors-controls-btn" onClick={() => zoomIn()} aria-label="Zoom in">
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
      <button type="button" className="ors-controls-btn" onClick={() => zoomOut()} aria-label="Zoom out">
        <ZoomOut size={16} />
      </button>
      <button
        type="button"
        className="ors-controls-btn"
        onClick={() => fitView({ padding: 0.12, duration: 280 })}
        aria-label="Fit view"
      >
        ⛶
      </button>
    </Panel>
  )
}

interface RoadmapFlowCanvasProps {
  initialNodes: Node[]
  initialEdges: Edge[]
  onTopicSelect: (raw: import('@/services/roadmapOfficialService').OfficialRoadmapNode) => void
  onRoadmapNavigate: (path: string) => void
  nodesDraggable?: boolean
  allowedSlugs?: ReadonlySet<string>
}

export function RoadmapFlowCanvas({
  initialNodes,
  initialEdges,
  onTopicSelect,
  onRoadmapNavigate,
  nodesDraggable = false,
  allowedSlugs,
}: RoadmapFlowCanvasProps) {
  const [reduceMotion, setReduceMotion] = useState(false)

  useEffect(() => {
    const media = window.matchMedia('(prefers-reduced-motion: reduce)')
    const update = () => setReduceMotion(media.matches)
    update()
    media.addEventListener('change', update)
    return () => media.removeEventListener('change', update)
  }, [])
  const snapshotRef = useRef(cloneGraph(initialNodes, initialEdges))
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)
  const { fitView } = useReactFlow()

  useEffect(() => {
    const snap = cloneGraph(initialNodes, initialEdges)
    snapshotRef.current = snap
    setNodes(snap.nodes)
    setEdges(snap.edges)
    const timer = window.setTimeout(() => fitView({ padding: 0.12, duration: 200 }), 60)
    return () => window.clearTimeout(timer)
  }, [initialNodes, initialEdges, setNodes, setEdges, fitView])

  const resetLayout = useCallback(() => {
    const snap = cloneGraph(snapshotRef.current.nodes, snapshotRef.current.edges)
    setNodes(snap.nodes)
    setEdges(snap.edges)
    window.setTimeout(() => fitView({ padding: 0.12, duration: 300 }), 40)
  }, [setNodes, setEdges, fitView])

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
    [onTopicSelect, onRoadmapNavigate],
  )

  return (
    <>
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
        minZoom={0.12}
        maxZoom={2}
        proOptions={{ hideAttribution: true }}
        defaultEdgeOptions={{ type: 'smoothstep' }}
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={20}
          size={1.25}
          color="var(--ors-paper-dot)"
        />
        <RoadmapControls onReset={resetLayout} />
        <MiniMap
          pannable
          zoomable
          className="ors-minimap"
          maskColor="rgb(243 234 211 / 0.75)"
          nodeColor={(node) => {
            const kind = (node.data as NodeData).nodeType
            if (kind === 'topic') return '#fff200'
            if (kind === 'subtopic') return '#ffdba8'
            if (kind === 'button') return '#d6d3d1'
            return '#a8a29e'
          }}
        />
      </ReactFlow>
    </>
  )
}
