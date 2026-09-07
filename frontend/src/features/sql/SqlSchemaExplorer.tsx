import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ChevronDown, ChevronRight, Plus, Table2 } from 'lucide-react'

import { Card } from '@/components/common/Card'
import { SqlPaneCollapseButton } from '@/features/sql/workbench/SqlPaneChrome'
import { SqlTablePreview } from '@/features/sql/SqlTablePreview'
import { buildSelectTemplate } from '@/features/sql/utils/sqlEditorInsert'
import { fetchSqlTablePreview } from '@/services/sqlService'
import type { SqlTableSchemaPublic } from '@/types/sql'
import { cn } from '@/utils/cn'

interface SqlSchemaExplorerProps {
  problemId: string
  tables: SqlTableSchemaPublic[]
  onInsertSnippet?: (snippet: string) => void
  onCollapse?: () => void
  compact?: boolean
}

export function SqlSchemaExplorer({
  problemId,
  tables,
  onInsertSnippet,
  onCollapse,
  compact = false,
}: SqlSchemaExplorerProps) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({})
  const [selectedTable, setSelectedTable] = useState<string | null>(null)

  const { data: preview, isLoading: previewLoading } = useQuery({
    queryKey: ['sql-table-preview', problemId, selectedTable],
    queryFn: () => fetchSqlTablePreview(problemId, selectedTable!),
    enabled: Boolean(selectedTable),
  })

  if (!tables.length) {
    return (
      <div className="p-3 text-sm text-[var(--color-text-muted)]">No schema tables defined.</div>
    )
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex items-center justify-between border-b border-[var(--color-border)] px-3 py-2">
        <div className="flex items-center gap-2 text-sm font-medium text-[var(--color-text)]">
          <Table2 className="h-4 w-4 text-[var(--color-text-muted)]" />
          Schema
        </div>
        {onCollapse && (
          <SqlPaneCollapseButton side="left" onClick={onCollapse} label="Schema explorer" />
        )}
      </div>
      <div className="min-h-0 flex-1 space-y-1 overflow-auto p-2">
        {tables.map((table) => {
          const isOpen = expanded[table.table_name]
          const isSelected = selectedTable === table.table_name
          return (
            <div key={table.table_name} className="rounded-md border border-[var(--color-border)]">
              <div
                className={cn(
                  'flex items-center gap-1 px-2 py-1.5',
                  isSelected && 'bg-[var(--color-surface-muted)]',
                )}
              >
                <button
                  type="button"
                  className="rounded p-0.5 text-[var(--color-text-muted)] hover:bg-[var(--color-surface)]"
                  onClick={() =>
                    setExpanded((prev) => ({
                      ...prev,
                      [table.table_name]: !prev[table.table_name],
                    }))
                  }
                  aria-label={isOpen ? 'Collapse table' : 'Expand table'}
                >
                  {isOpen ? (
                    <ChevronDown className="h-3.5 w-3.5" />
                  ) : (
                    <ChevronRight className="h-3.5 w-3.5" />
                  )}
                </button>
                <button
                  type="button"
                  className="min-w-0 flex-1 truncate text-left text-xs font-medium text-[var(--color-text)]"
                  onClick={() => setSelectedTable(table.table_name)}
                >
                  {table.display_name || table.table_name}
                </button>
                {onInsertSnippet && (
                  <button
                    type="button"
                    title="Insert SELECT *"
                    className="rounded px-1.5 py-0.5 text-[10px] text-[var(--color-accent)] hover:bg-[var(--color-surface)]"
                    onClick={() => onInsertSnippet(buildSelectTemplate(table.table_name))}
                  >
                    SELECT
                  </button>
                )}
              </div>
              {isOpen && (
                <ul className="space-y-0.5 border-t border-[var(--color-border)] px-2 py-1.5">
                  {table.columns.map((col) => (
                    <li
                      key={col.column_name}
                      className="flex items-center justify-between gap-1 font-mono text-[11px] text-[var(--color-text-muted)]"
                    >
                      <span className="truncate">
                        {col.column_name}
                        <span className="ml-1 text-[var(--color-text-subtle)]">
                          {col.data_type}
                          {!col.is_nullable ? ' NOT NULL' : ''}
                        </span>
                      </span>
                      {onInsertSnippet && (
                        <button
                          type="button"
                          title="Insert column"
                          className="rounded p-0.5 hover:bg-[var(--color-surface)]"
                          onClick={() => onInsertSnippet(col.column_name)}
                        >
                          <Plus className="h-3 w-3" />
                        </button>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )
        })}
        {!compact && (
          <Card padding="sm" className="mt-2">
            <SqlTablePreview
              preview={selectedTable ? (preview ?? null) : null}
              isLoading={previewLoading}
            />
          </Card>
        )}
      </div>
    </div>
  )
}
