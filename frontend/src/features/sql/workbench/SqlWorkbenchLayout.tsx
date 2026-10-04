import type { ReactNode } from 'react'

import {
  SqlExpandRail,
  SqlPaneResizeHandle,
} from '@/features/sql/workbench/SqlPaneChrome'
import type { ResizableSqlLayout } from '@/features/sql/workbench/useResizableSqlLayout'
import { cn } from '@/utils/cn'

interface SqlWorkbenchLayoutProps {
  topBar: ReactNode
  objectExplorer: ReactNode
  editorPanel: ReactNode
  questionPanel: ReactNode
  bottomPanel: ReactNode
  statusBar?: ReactNode
  layout: ResizableSqlLayout
  mobileTab: 'problem' | 'schema' | 'code' | 'output'
  onMobileTab: (tab: 'problem' | 'schema' | 'code' | 'output') => void
}

export function SqlWorkbenchLayout({
  topBar,
  objectExplorer,
  editorPanel,
  questionPanel,
  bottomPanel,
  statusBar,
  layout,
  mobileTab,
  onMobileTab,
}: SqlWorkbenchLayoutProps) {
  const {
    layout: state,
    desktopLayout,
    startResizeLeft,
    startResizeRight,
    startResizeBottom,
    toggleLeftCollapsed,
    toggleRightCollapsed,
    toggleBottomCollapsed,
  } = layout

  if (!desktopLayout) {
    return (
      <div className="sql-workbench flex min-h-0 flex-1 flex-col overflow-hidden">
        {topBar}
        <div className="mb-2 flex gap-1 px-1" role="tablist" aria-label="Workspace">
          {(
            [
              ['problem', 'Problem'],
              ['schema', 'Schema'],
              ['code', 'Editor'],
              ['output', 'Output'],
            ] as const
          ).map(([tab, label]) => (
            <button
              key={tab}
              type="button"
              role="tab"
              aria-selected={mobileTab === tab}
              className={cn(
                'flex-1 rounded-md border px-2 py-1.5 text-sm',
                mobileTab === tab
                  ? 'border-[var(--color-accent)] text-[var(--color-accent)]'
                  : 'border-[var(--color-border)] text-[var(--color-text-muted)]',
              )}
              onClick={() => onMobileTab(tab)}
            >
              {label}
            </button>
          ))}
        </div>
        <div className="min-h-0 flex-1 overflow-hidden">
          {mobileTab === 'problem' && (
            <div className="h-full overflow-auto p-1">{questionPanel}</div>
          )}
          {mobileTab === 'schema' && (
            <div className="h-full overflow-auto p-1">{objectExplorer}</div>
          )}
          {mobileTab === 'code' && <div className="h-full overflow-hidden p-1">{editorPanel}</div>}
          {mobileTab === 'output' && <div className="h-full overflow-auto p-1">{bottomPanel}</div>}
        </div>
        {statusBar}
      </div>
    )
  }

  return (
    <div className="sql-workbench flex min-h-0 flex-1 flex-col overflow-hidden">
      {topBar}
      <div className="flex min-h-0 flex-1 overflow-hidden">
        {state.isLeftCollapsed ? (
          <SqlExpandRail side="left" label="Schema explorer" onExpand={toggleLeftCollapsed} />
        ) : (
          <>
            <div
              className="flex min-h-0 shrink-0 flex-col overflow-hidden border-r border-[var(--color-border)]"
              style={{ width: state.leftWidth }}
            >
              {objectExplorer}
            </div>
            <SqlPaneResizeHandle direction="horizontal" onMouseDown={startResizeLeft} />
          </>
        )}

        <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
          <div className="min-h-0 flex-1 overflow-hidden">{editorPanel}</div>
          {state.isBottomCollapsed ? (
            <SqlExpandRail side="bottom" label="Results" onExpand={toggleBottomCollapsed} />
          ) : (
            <>
              <SqlPaneResizeHandle direction="vertical" onMouseDown={startResizeBottom} />
              <div
                className="min-h-0 shrink-0 overflow-hidden border-t border-[var(--color-border)]"
                style={{ height: state.bottomHeight }}
              >
                {bottomPanel}
              </div>
            </>
          )}
        </div>

        {state.isRightCollapsed ? (
          <SqlExpandRail side="right" label="Problem" onExpand={toggleRightCollapsed} />
        ) : (
          <>
            <SqlPaneResizeHandle direction="horizontal" onMouseDown={startResizeRight} />
            <div
              className="flex min-h-0 shrink-0 flex-col overflow-hidden border-l border-[var(--color-border)]"
              style={{ width: state.rightWidth }}
            >
              {questionPanel}
            </div>
          </>
        )}
      </div>
      {statusBar}
    </div>
  )
}
