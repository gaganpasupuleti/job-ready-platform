import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { Card } from '@/components/common/Card'
import { SqlTablePreview } from '@/features/sql/SqlTablePreview'
import { fetchSqlTablePreview } from '@/services/sqlService'
import type { SqlTableSchemaPublic } from '@/types/sql'

interface SqlSchemaExplorerProps {
  problemId: string
  tables: SqlTableSchemaPublic[]
}

export function SqlSchemaExplorer({ problemId, tables }: SqlSchemaExplorerProps) {
  const [selectedTable, setSelectedTable] = useState<string | null>(null)

  const { data: preview, isLoading: previewLoading } = useQuery({
    queryKey: ['sql-table-preview', problemId, selectedTable],
    queryFn: () => fetchSqlTablePreview(problemId, selectedTable!),
    enabled: Boolean(selectedTable),
  })

  if (!tables.length) {
    return <p className="text-sm text-[var(--color-text-muted)]">No schema tables defined.</p>
  }

  return (
    <div className="space-y-4">
      <div className="space-y-3">
        {tables.map((table) => {
          const isSelected = selectedTable === table.table_name
          return (
            <button
              key={table.table_name}
              type="button"
              onClick={() => setSelectedTable(table.table_name)}
              className="w-full text-left"
            >
              <Card
                padding="md"
                className={`transition-colors ${
                  isSelected ? 'border-[var(--color-accent)]' : ''
                }`}
              >
                <p className="text-sm font-medium text-[var(--color-text)]">
                  {table.display_name || table.table_name}
                </p>
                {table.description && (
                  <p className="mt-1 text-xs text-[var(--color-text-muted)]">{table.description}</p>
                )}
                <ul className="mt-2 space-y-1">
                  {table.columns.map((col) => (
                    <li
                      key={col.column_name}
                      className="flex justify-between gap-2 font-mono text-xs text-[var(--color-text-muted)]"
                    >
                      <span>{col.column_name}</span>
                      <span className="text-[var(--color-text-subtle)]">
                        {col.data_type}
                        {!col.is_nullable ? ' NOT NULL' : ''}
                      </span>
                    </li>
                  ))}
                </ul>
              </Card>
            </button>
          )
        })}
      </div>
      <SqlTablePreview preview={selectedTable ? (preview ?? null) : null} isLoading={previewLoading} />
    </div>
  )
}
