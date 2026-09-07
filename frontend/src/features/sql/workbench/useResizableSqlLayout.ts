import {
  useCallback,
  useEffect,
  useRef,
  useState,
  useSyncExternalStore,
  type MouseEvent as ReactMouseEvent,
} from 'react'

import {
  clampSqlWorkbenchLayout,
  DEFAULT_SQL_WORKBENCH_LAYOUT,
  loadSqlWorkbenchLayout,
  maxBottomHeightPx,
  resetSqlWorkbenchLayoutStorage,
  saveSqlWorkbenchLayout,
  type SqlWorkbenchLayoutState,
} from '@/features/sql/workbench/sqlWorkbenchLayoutStorage'

type ResizeEdge = 'left' | 'right' | 'bottom'

/** Match existing PracticeWorkspace mobile breakpoint (1024px). */
function useDesktopLayoutEnabled(): boolean {
  return useSyncExternalStore(
    (onStoreChange) => {
      if (typeof window === 'undefined') return () => undefined
      const mq = window.matchMedia('(min-width: 1024px)')
      mq.addEventListener('change', onStoreChange)
      return () => mq.removeEventListener('change', onStoreChange)
    },
    () => (typeof window !== 'undefined' ? window.matchMedia('(min-width: 1024px)').matches : true),
    () => true,
  )
}

function notifyMonacoLayout(): void {
  window.dispatchEvent(new Event('resize'))
}

export function useResizableSqlLayout() {
  const desktopLayout = useDesktopLayoutEnabled()
  const [layout, setLayout] = useState<SqlWorkbenchLayoutState>(() => loadSqlWorkbenchLayout())
  const layoutRef = useRef(layout)
  const dragRef = useRef<{
    edge: ResizeEdge
    startX: number
    startY: number
    startValue: number
  } | null>(null)

  useEffect(() => {
    layoutRef.current = layout
  }, [layout])

  const persist = useCallback((next: SqlWorkbenchLayoutState) => {
    const clamped = clampSqlWorkbenchLayout(next)
    layoutRef.current = clamped
    setLayout(clamped)
    saveSqlWorkbenchLayout(clamped)
  }, [])

  useEffect(() => {
    const onViewportResize = () => {
      const clamped = clampSqlWorkbenchLayout(layoutRef.current)
      if (JSON.stringify(clamped) !== JSON.stringify(layoutRef.current)) {
        persist(clamped)
      }
      notifyMonacoLayout()
    }
    window.addEventListener('resize', onViewportResize)
    return () => window.removeEventListener('resize', onViewportResize)
  }, [persist])

  const startResize = useCallback(
    (edge: ResizeEdge, event: ReactMouseEvent) => {
      if (!desktopLayout) return
      event.preventDefault()
      const current = layoutRef.current
      dragRef.current = {
        edge,
        startX: event.clientX,
        startY: event.clientY,
        startValue:
          edge === 'left'
            ? current.leftWidth
            : edge === 'right'
              ? current.rightWidth
              : current.bottomHeight,
      }
      document.body.style.cursor = edge === 'bottom' ? 'row-resize' : 'col-resize'
      document.body.style.userSelect = 'none'
    },
    [desktopLayout],
  )

  useEffect(() => {
    const onMove = (event: MouseEvent) => {
      const drag = dragRef.current
      if (!drag) return

      const current = layoutRef.current
      if (drag.edge === 'left') {
        const delta = event.clientX - drag.startX
        persist({ ...current, leftWidth: drag.startValue + delta })
      } else if (drag.edge === 'right') {
        const delta = drag.startX - event.clientX
        persist({ ...current, rightWidth: drag.startValue + delta })
      } else {
        const delta = drag.startY - event.clientY
        persist({ ...current, bottomHeight: drag.startValue + delta })
      }
    }

    const onUp = () => {
      if (!dragRef.current) return
      dragRef.current = null
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
      notifyMonacoLayout()
    }

    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
    return () => {
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseup', onUp)
    }
  }, [persist])

  const toggleLeftCollapsed = useCallback(() => {
    persist({ ...layoutRef.current, isLeftCollapsed: !layoutRef.current.isLeftCollapsed })
    notifyMonacoLayout()
  }, [persist])

  const toggleRightCollapsed = useCallback(() => {
    persist({ ...layoutRef.current, isRightCollapsed: !layoutRef.current.isRightCollapsed })
    notifyMonacoLayout()
  }, [persist])

  const toggleBottomCollapsed = useCallback(() => {
    persist({ ...layoutRef.current, isBottomCollapsed: !layoutRef.current.isBottomCollapsed })
    notifyMonacoLayout()
  }, [persist])

  const resetLayout = useCallback(() => {
    const defaults = resetSqlWorkbenchLayoutStorage()
    setLayout(defaults)
    layoutRef.current = defaults
    notifyMonacoLayout()
  }, [])

  return {
    layout: desktopLayout ? layout : DEFAULT_SQL_WORKBENCH_LAYOUT,
    desktopLayout,
    maxBottomHeight: maxBottomHeightPx(),
    startResizeLeft: (event: ReactMouseEvent) => startResize('left', event),
    startResizeRight: (event: ReactMouseEvent) => startResize('right', event),
    startResizeBottom: (event: ReactMouseEvent) => startResize('bottom', event),
    toggleLeftCollapsed,
    toggleRightCollapsed,
    toggleBottomCollapsed,
    resetLayout,
  }
}

export type ResizableSqlLayout = ReturnType<typeof useResizableSqlLayout>
