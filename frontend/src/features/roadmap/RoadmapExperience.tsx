import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { configStorageKey, nodeByKey } from './adapter'
import { buildRoadmapLayout } from './layout'
import type { RoadmapFixturePayload } from './types'
import { RoadmapDetailsPanel, RoadmapList } from './components/RoadmapList'
import { RoadmapMap } from './components/RoadmapMap'
import './roadmap.css'

type ViewMode = 'map' | 'list'

function preferListDefault(): boolean {
  if (typeof window === 'undefined') return false
  return window.matchMedia('(max-width: 900px)').matches
}

function readStored(key: string): { node?: string; view?: ViewMode } {
  try {
    const raw = sessionStorage.getItem(key)
    if (!raw) return {}
    return JSON.parse(raw) as { node?: string; view?: ViewMode }
  } catch {
    return {}
  }
}

interface RoadmapExperienceProps {
  payload: RoadmapFixturePayload
  title?: string
}

export function RoadmapExperience({ payload, title }: RoadmapExperienceProps) {
  const assembly = payload.assembly
  const [searchParams, setSearchParams] = useSearchParams()
  const [view, setView] = useState<ViewMode>(() => (preferListDefault() ? 'list' : 'map'))
  const [scale, setScale] = useState(1)
  const [offset, setOffset] = useState({ x: 0, y: 0 })
  const [panning, setPanning] = useState(false)
  const panOrigin = useRef<{ x: number; y: number; ox: number; oy: number } | null>(null)
  const viewportRef = useRef<HTMLDivElement | null>(null)
  const panelRef = useRef<HTMLElement | null>(null)
  const lastFocusRef = useRef<HTMLElement | null>(null)
  const searchRef = useRef<HTMLInputElement | null>(null)

  const storageKey = configStorageKey(assembly)

  useEffect(() => {
    const stored = readStored(storageKey)
    if (stored.view) setView(stored.view)
    if (stored.node && !searchParams.get('node')) {
      setSearchParams({ node: stored.node }, { replace: true })
    }
  }, [storageKey]) // eslint-disable-line react-hooks/exhaustive-deps

  const selectedKey = searchParams.get('node')
  const startHereKey =
    payload.fixture_meta.start_here?.intended_start_node_key ??
    assembly.recommended_next_node_key ??
    null

  const layout = useMemo(() => buildRoadmapLayout(assembly), [assembly])

  const selectNode = useCallback(
    (key: string) => {
      lastFocusRef.current = document.activeElement as HTMLElement
      setSearchParams({ node: key })
      sessionStorage.setItem(storageKey, JSON.stringify({ node: key, view }))
      requestAnimationFrame(() => panelRef.current?.focus())
    },
    [setSearchParams, storageKey, view],
  )

  const clearSelection = useCallback(() => {
    setSearchParams({})
    sessionStorage.setItem(storageKey, JSON.stringify({ view }))
    lastFocusRef.current?.focus?.()
  }, [setSearchParams, storageKey, view])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') clearSelection()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [clearSelection])

  const setViewMode = (mode: ViewMode) => {
    setView(mode)
    sessionStorage.setItem(storageKey, JSON.stringify({ node: selectedKey ?? undefined, view: mode }))
  }

  const fitView = () => {
    const vp = viewportRef.current
    if (!vp || !layout) return
    const pad = 24
    const sx = (vp.clientWidth - pad * 2) / layout.width
    const sy = (vp.clientHeight - pad * 2) / layout.height
    const next = Math.min(1, Math.max(0.45, Math.min(sx, sy)))
    setScale(next)
    setOffset({
      x: (vp.clientWidth - layout.width * next) / 2,
      y: Math.max(12, (vp.clientHeight - layout.height * next) / 4),
    })
  }

  const resetView = () => {
    setScale(1)
    setOffset({ x: 24, y: 16 })
  }

  useEffect(() => {
    if (view === 'map' && layout) {
      const t = window.setTimeout(fitView, 0)
      return () => window.clearTimeout(t)
    }
  }, [view, layout.width]) // eslint-disable-line react-hooks/exhaustive-deps

  const onPointerDown = (e: React.PointerEvent) => {
    if (view !== 'map') return
    if ((e.target as HTMLElement).closest('.rm-node')) return
    setPanning(true)
    panOrigin.current = { x: e.clientX, y: e.clientY, ox: offset.x, oy: offset.y }
    ;(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId)
  }

  const onPointerMove = (e: React.PointerEvent) => {
    if (!panning || !panOrigin.current) return
    setOffset({
      x: panOrigin.current.ox + (e.clientX - panOrigin.current.x),
      y: panOrigin.current.oy + (e.clientY - panOrigin.current.y),
    })
  }

  const onPointerUp = () => {
    setPanning(false)
    panOrigin.current = null
  }

  const onWheel = (e: React.WheelEvent) => {
    if (view !== 'map') return
    if (!e.ctrlKey && !e.metaKey) return
    e.preventDefault()
    const delta = e.deltaY > 0 ? -0.08 : 0.08
    setScale((s) => Math.min(1.6, Math.max(0.4, s + delta)))
  }

  const jumpStart = () => {
    if (startHereKey) selectNode(startHereKey)
  }

  const runSearch = () => {
    if (!searchRef.current) return
    const q = searchRef.current.value.trim().toLowerCase()
    if (!q) return
    const match = assembly.nodes.find(
      (n) =>
        n.node_key.toLowerCase().includes(q) ||
        n.title.toLowerCase().includes(q) ||
        (n.skill_slug ?? '').includes(q),
    )
    if (match) selectNode(match.node_key)
  }

  const selected = selectedKey ? nodeByKey(assembly, selectedKey) ?? null : null
  const displayTitle = title ?? assembly.family_slug.replace(/-/g, ' ')

  return (
    <div className="rm-page">
      <header className="rm-banner" role="status">
        <div className="rm-banner__brand">
          <div>
            <p className="rm-banner__kicker">Career roadmap</p>
            <h1 className="rm-banner__title">{displayTitle}</h1>
          </div>
        </div>
        {assembly.preview_only || !assembly.student_eligible ? (
          <p className="rm-banner__note">
            Draft curriculum ({assembly.config_version}). Planned order is guidance only — opening a
            resource does not mark a node complete.
            {payload.fixture_meta.warning ? ` ${payload.fixture_meta.warning}` : ''}
          </p>
        ) : (
          <p className="rm-banner__note">
            Follow the map or list. Use Start here for the recommended next step on this platform.
          </p>
        )}
        <Link to="/roadmaps" className="rm-btn rm-btn--ghost">
          All roadmaps
        </Link>
      </header>

      <div className="rm-toolbar" role="toolbar" aria-label="Roadmap controls">
        <div className="rm-toolbar__group">
          <button
            type="button"
            className={view === 'map' ? 'rm-btn rm-btn--accent' : 'rm-btn'}
            onClick={() => setViewMode('map')}
            aria-pressed={view === 'map'}
          >
            Map
          </button>
          <button
            type="button"
            className={view === 'list' ? 'rm-btn rm-btn--accent' : 'rm-btn'}
            onClick={() => setViewMode('list')}
            aria-pressed={view === 'list'}
          >
            List
          </button>
        </div>
        <div className="rm-toolbar__group">
          <button type="button" className="rm-btn rm-btn--accent" onClick={jumpStart}>
            Start here
          </button>
          {view === 'map' ? (
            <>
              <button type="button" className="rm-btn" onClick={fitView}>
                Fit
              </button>
              <button type="button" className="rm-btn" onClick={resetView}>
                Reset
              </button>
              <button
                type="button"
                className="rm-btn"
                onClick={() => setScale((s) => Math.min(1.6, s + 0.1))}
              >
                Zoom in
              </button>
              <button
                type="button"
                className="rm-btn"
                onClick={() => setScale((s) => Math.max(0.4, s - 0.1))}
              >
                Zoom out
              </button>
            </>
          ) : null}
        </div>
        <div className="rm-toolbar__search">
          <label className="sr-only" htmlFor="rm-search">
            Search nodes
          </label>
          <input
            id="rm-search"
            ref={searchRef}
            type="search"
            placeholder="Search nodes"
            className="rm-input"
            onKeyDown={(e) => {
              if (e.key === 'Enter') runSearch()
            }}
          />
          <button type="button" className="rm-btn" onClick={runSearch}>
            Focus
          </button>
        </div>
      </div>

      <div className="rm-legend" aria-label="Connection legend">
        <span>
          <i className="rm-swatch rm-swatch--hard" /> Required prerequisite
        </span>
        <span>
          <i className="rm-swatch rm-swatch--soft" /> Recommended before
        </span>
        <span>
          <i className="rm-swatch rm-swatch--next" /> Next (navigation)
        </span>
        <span>
          <i className="rm-swatch rm-swatch--related" /> Related
        </span>
        <span className="rm-legend__hint">Optional nodes use a dashed outline</span>
      </div>

      <div className="rm-workspace">
        <div
          className="rm-stage"
          onPointerDown={onPointerDown}
          onPointerMove={onPointerMove}
          onPointerUp={onPointerUp}
          onPointerCancel={onPointerUp}
          onWheel={onWheel}
        >
          {view === 'map' ? (
            <RoadmapMap
              layout={layout}
              selectedKey={selectedKey}
              startHereKey={startHereKey}
              onSelect={selectNode}
              scale={scale}
              offset={offset}
              viewportRef={viewportRef}
            />
          ) : (
            <RoadmapList
              assembly={assembly}
              selectedKey={selectedKey}
              startHereKey={startHereKey}
              onSelect={selectNode}
            />
          )}
        </div>
        <RoadmapDetailsPanel
          node={selected}
          assembly={assembly}
          onClose={clearSelection}
          panelRef={panelRef}
        />
      </div>
    </div>
  )
}
