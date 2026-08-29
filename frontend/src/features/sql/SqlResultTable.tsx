interface SqlResultTableProps {
  columns: string[]
  rows: unknown[][]
  truncated?: boolean
  emptyMessage?: string
}

export function SqlResultTable({
  columns,
  rows,
  truncated,
  emptyMessage = 'No rows returned.',
}: SqlResultTableProps) {
  if (!columns.length) {
    return <p className="text-sm text-[var(--color-text-muted)]">{emptyMessage}</p>
  }

  return (
    <div className="space-y-2">
      {truncated && (
        <p className="text-xs text-[var(--color-text-subtle)]">Result truncated</p>
      )}
      <div className="overflow-x-auto rounded-md border border-[var(--color-border)]">
        <table className="w-full text-left text-xs">
          <thead className="bg-[var(--color-surface-muted)] text-[var(--color-text-subtle)]">
            <tr>
              {columns.map((col) => (
                <th key={col} className="whitespace-nowrap px-3 py-2 font-medium">
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-3 py-3 text-[var(--color-text-muted)]"
                >
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              rows.map((row, rowIndex) => (
                <tr key={rowIndex} className="border-t border-[var(--color-border)]">
                  {columns.map((_, cellIndex) => {
                    const cell = row[cellIndex]
                    return (
                      <td key={cellIndex} className="whitespace-nowrap px-3 py-2 font-mono">
                        {cell == null ? 'NULL' : String(cell)}
                      </td>
                    )
                  })}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
