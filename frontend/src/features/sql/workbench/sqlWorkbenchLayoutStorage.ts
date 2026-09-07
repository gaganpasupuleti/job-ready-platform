export const SQL_WORKBENCH_LAYOUT_KEY = 'jrp-sql-workbench-layout-v1'

export interface SqlWorkbenchLayoutState {
  leftWidth: number
  rightWidth: number
  bottomHeight: number
  isLeftCollapsed: boolean
  isRightCollapsed: boolean
  isBottomCollapsed: boolean
}

/** Tuned for ~1024–1440px: narrower side panes, more editor width. */
export const DEFAULT_SQL_WORKBENCH_LAYOUT: SqlWorkbenchLayoutState = {
  leftWidth: 240,
  rightWidth: 300,
  bottomHeight: 200,
  isLeftCollapsed: false,
  isRightCollapsed: false,
  isBottomCollapsed: false,
}

export const SQL_LAYOUT_LIMITS = {
  left: { min: 200, max: 360, default: 240 },
  right: { min: 260, max: 400, default: 300 },
  bottom: { min: 120, default: 200, maxViewportRatio: 0.4 },
} as const

function readJson<T>(key: string, fallback: T): T {
  if (typeof window === 'undefined') return fallback
  try {
    const raw = window.localStorage.getItem(key)
    if (!raw) return fallback
    return JSON.parse(raw) as T
  } catch {
    return fallback
  }
}

export function maxBottomHeightPx(
  viewportHeight = typeof window !== 'undefined' ? window.innerHeight : 800,
): number {
  return Math.max(
    SQL_LAYOUT_LIMITS.bottom.min,
    Math.floor(viewportHeight * SQL_LAYOUT_LIMITS.bottom.maxViewportRatio),
  )
}

export function clampSqlWorkbenchLayout(
  state: SqlWorkbenchLayoutState,
  viewportHeight?: number,
): SqlWorkbenchLayoutState {
  const maxBottom = maxBottomHeightPx(viewportHeight)
  return {
    ...state,
    leftWidth: Math.min(
      SQL_LAYOUT_LIMITS.left.max,
      Math.max(SQL_LAYOUT_LIMITS.left.min, state.leftWidth),
    ),
    rightWidth: Math.min(
      SQL_LAYOUT_LIMITS.right.max,
      Math.max(SQL_LAYOUT_LIMITS.right.min, state.rightWidth),
    ),
    bottomHeight: Math.min(maxBottom, Math.max(SQL_LAYOUT_LIMITS.bottom.min, state.bottomHeight)),
  }
}

export function loadSqlWorkbenchLayout(viewportHeight?: number): SqlWorkbenchLayoutState {
  const stored = readJson<Partial<SqlWorkbenchLayoutState>>(SQL_WORKBENCH_LAYOUT_KEY, {})
  return clampSqlWorkbenchLayout(
    {
      ...DEFAULT_SQL_WORKBENCH_LAYOUT,
      ...stored,
    },
    viewportHeight,
  )
}

export function saveSqlWorkbenchLayout(state: SqlWorkbenchLayoutState): void {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(SQL_WORKBENCH_LAYOUT_KEY, JSON.stringify(state))
}

export function resetSqlWorkbenchLayoutStorage(): SqlWorkbenchLayoutState {
  saveSqlWorkbenchLayout(DEFAULT_SQL_WORKBENCH_LAYOUT)
  return { ...DEFAULT_SQL_WORKBENCH_LAYOUT }
}
