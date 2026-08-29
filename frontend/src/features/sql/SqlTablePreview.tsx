import type { SqlTablePreview as SqlTablePreviewType } from '@/types/sql'

interface SqlTablePreviewProps {
  preview: SqlTablePreviewType | null
  isLoading?: boolean
}

export function SqlTablePreview({ preview, isLoading }: SqlTablePreviewProps) {
  if (isLoading) {
    return <p className="text-sm text-[var(--color-text-muted)]">Loading preview...</p>
  }
  if (!preview) {
    return (
      <p className="text-sm text-[var(--color-text-muted)]">
        Select a table to preview sample rows.
      </p>
    )
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium text-[var(--color-text)]">{preview.table_name}</h4>
        {preview.truncated && (
          <span className="text-xs text-[var(--color-text-subtle)]">Preview truncated</span>
        )}
      </div>
      <div className="overflow-x-auto rounded-md border border-[var(--color-border)]">
        <table className="w-full text-left text-xs">
          <thead className="bg-[var(--color-surface-muted)] text-[var(--color-text-subtle)]">
            <tr>
              {preview.columns.map((col) => (
                <th key={col} className="whitespace-nowrap px-3 py-2 font-medium">
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {preview.rows.length === 0 ? (
              <tr>
                <td
                  colSpan={Math.max(preview.columns.length, 1)}
                  className="px-3 py-3 text-[var(--color-text-muted)]"
                >
                  No rows
                </td>
              </tr>
            ) : (
              preview.rows.map((row, rowIndex) => (
                <tr key={rowIndex} className="border-t border-[var(--color-border)]">
                  {row.map((cell, cellIndex) => (
                    <td key={cellIndex} className="whitespace-nowrap px-3 py-2 font-mono">
                      {cell == null ? 'NULL' : String(cell)}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
