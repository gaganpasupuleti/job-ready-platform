import { useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Loader2 } from 'lucide-react'

import { Button } from '@/components/common/Button'
import { SqlEditor, type SqlEditorHandle } from '@/features/sql/SqlEditor'
import { useAuth } from '@/hooks/useAuth'
import {
  fetchSqlPlaygroundCatalog,
  fetchSqlPlaygroundDataset,
  runSqlPlaygroundQuery,
  type SqlPlaygroundRunResponse,
} from '@/services/sqlPlaygroundService'
import { cn } from '@/utils/cn'

type MobileTab = 'schema' | 'editor' | 'results'

function draftStorageKey(userId: string, datasetId: string) {
  return `sql-playground-draft:${userId}:${datasetId}`
}

export function SqlPlaygroundPage() {
  const { user } = useAuth()
  const editorRef = useRef<SqlEditorHandle>(null)
  const runEpochRef = useRef(0)
  const [datasetId, setDatasetId] = useState('campus-bookstore')
  const [query, setQuery] = useState('')
  const [draftReady, setDraftReady] = useState(false)
  const [mobileTab, setMobileTab] = useState<MobileTab>('editor')
  const [result, setResult] = useState<SqlPlaygroundRunResponse | null>(null)
  const [expanded, setExpanded] = useState<Record<string, boolean>>({})

  const catalogQuery = useQuery({
    queryKey: ['sql-playground-catalog'],
    queryFn: fetchSqlPlaygroundCatalog,
  })
  const datasetQuery = useQuery({
    queryKey: ['sql-playground-dataset', datasetId],
    queryFn: () => fetchSqlPlaygroundDataset(datasetId),
    enabled: Boolean(datasetId),
  })

  useEffect(() => {
    runEpochRef.current += 1
    setDraftReady(false)
    setResult(null)
  }, [datasetId])

  useEffect(() => {
    if (!datasetQuery.data || !user?.id) return
    const stored = localStorage.getItem(draftStorageKey(user.id, datasetId))
    setQuery(stored ?? datasetQuery.data.starter_query)
    setDraftReady(true)
  }, [datasetQuery.data, datasetId, user?.id])

  useEffect(() => {
    if (!draftReady || !user?.id) return
    localStorage.setItem(draftStorageKey(user.id, datasetId), query)
  }, [draftReady, datasetId, query, user?.id])

  const runMutation = useMutation({
    mutationFn: async () => {
      const epoch = runEpochRef.current
      const data = await runSqlPlaygroundQuery(datasetId, query)
      return { epoch, data }
    },
    onSuccess: ({ epoch, data }) => {
      // Ignore late responses from a previous dataset after the student switches.
      if (epoch !== runEpochRef.current) return
      setResult(data)
      setMobileTab('results')
    },
    onError: (_error, _variables, onMutateResult) => {
      void onMutateResult
    },
  })

  const handleRun = () => {
    const epoch = runEpochRef.current
    runMutation.mutate(undefined, {
      onError: () => {
        if (epoch !== runEpochRef.current) return
        setResult({
          columns: [],
          rows: [],
          row_count: 0,
          truncated: false,
          error: 'Unable to run this query right now.',
          status: 'sql_error',
          assessed: false,
          row_limit: catalogQuery.data?.row_limit ?? 500,
          timeout_ms: catalogQuery.data?.timeout_ms ?? 3000,
          note: catalogQuery.data?.note ?? '',
        })
        setMobileTab('results')
      },
    })
  }

  const schemaTables = useMemo(
    () =>
      (datasetQuery.data?.tables ?? []).map((table) => ({
        table_name: table.table_name,
        display_name: table.display_name,
        description: table.description,
        columns: table.columns,
      })),
    [datasetQuery.data],
  )

  function resetQuery() {
    if (!datasetQuery.data) return
    const confirmed = window.confirm('Discard the current draft and restore the starter query?')
    if (!confirmed) return
    setQuery(datasetQuery.data.starter_query)
    setResult(null)
    editorRef.current?.replaceSql(datasetQuery.data.starter_query)
  }

  return (
    <div className="module-page flex min-h-0 flex-1 flex-col gap-3">
      <header className="module-heading">
        <div>
          <p className="eyebrow">
            <Link to="/practice/playground" className="text-[var(--color-accent)] hover:underline">
              Playground
            </Link>
            {' / '}
            SQL
          </p>
          <h1 data-testid="sql-playground-heading">SQL Playground</h1>
          <p>
            Explore a sample dataset without opening an assessed problem. Runs are not graded and do
            not create submissions.
          </p>
        </div>
      </header>

      <div className="flex flex-wrap items-end gap-3">
        <label className="text-sm">
          Dataset
          <select
            className="ml-2 rounded-[5px] border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1"
            value={datasetId}
            onChange={(event) => setDatasetId(event.target.value)}
          >
            {(catalogQuery.data?.datasets ?? []).map((item) => (
              <option key={item.id} value={item.id}>
                {item.title}
              </option>
            ))}
          </select>
        </label>
        <span className="rounded-[5px] border border-[var(--color-border)] px-2 py-1 text-xs text-[var(--color-text-muted)]">
          Language: SQL
        </span>
        <Link to="/practice/sql" className="text-sm text-[var(--color-accent)] hover:underline">
          Assessed SQL Practice
        </Link>
      </div>

      {datasetQuery.isLoading ? (
        <p>Loading dataset...</p>
      ) : datasetQuery.isError || !datasetQuery.data ? (
        <p role="alert">Unable to load this dataset.</p>
      ) : (
        <>
          <p className="text-sm text-[var(--color-text-muted)]">{datasetQuery.data.documentation}</p>
          <div className="mb-1 flex gap-1 md:hidden" role="tablist" aria-label="Playground panels">
            {([
              ['schema', 'Schema'],
              ['editor', 'Editor'],
              ['results', 'Results'],
            ] as const).map(([id, label]) => (
              <button
                key={id}
                type="button"
                role="tab"
                aria-selected={mobileTab === id}
                className={cn(
                  'flex-1 rounded-[5px] border px-2 py-1.5 text-sm',
                  mobileTab === id
                    ? 'border-[var(--color-accent)] text-[var(--color-accent)]'
                    : 'border-[var(--color-border)] text-[var(--color-text-muted)]',
                )}
                onClick={() => setMobileTab(id)}
              >
                {label}
              </button>
            ))}
          </div>

          <div className="grid min-h-0 flex-1 gap-3 md:grid-cols-[240px_minmax(0,1fr)]">
            <aside
              className={cn(
                'min-h-0 overflow-auto rounded-[5px] border border-[var(--color-border)] bg-[var(--color-surface)] p-3',
                mobileTab === 'schema' ? 'block' : 'hidden md:block',
              )}
            >
              <h2 className="text-sm font-semibold">Schema</h2>
              <ul className="mt-2 space-y-2 text-sm">
                {datasetQuery.data.tables.map((table) => {
                  const open = expanded[table.table_name] ?? false
                  return (
                    <li key={table.table_name}>
                      <button
                        type="button"
                        className="flex w-full items-center justify-between text-left font-medium"
                        onClick={() =>
                          setExpanded((current) => ({
                            ...current,
                            [table.table_name]: !open,
                          }))
                        }
                      >
                        <span>{table.table_name}</span>
                        <span aria-hidden>{open ? '−' : '+'}</span>
                      </button>
                      <p className="text-xs text-[var(--color-text-muted)]">{table.description}</p>
                      {open && (
                        <div className="mt-2 space-y-2">
                          <ul className="space-y-1 text-xs">
                            {table.columns.map((column) => (
                              <li key={column.column_name}>
                                <code>{column.column_name}</code> · {column.data_type}
                                {column.is_nullable ? '' : ' · not null'}
                              </li>
                            ))}
                          </ul>
                          <div className="overflow-x-auto">
                            <table className="min-w-full text-xs">
                              <thead>
                                <tr>
                                  {table.sample_columns.map((column) => (
                                    <th key={column} className="border-b px-1 py-0.5 text-left">
                                      {column}
                                    </th>
                                  ))}
                                </tr>
                              </thead>
                              <tbody>
                                {table.sample_rows.map((row, index) => (
                                  <tr key={`${table.table_name}-${index}`}>
                                    {row.map((cell, cellIndex) => (
                                      <td key={cellIndex} className="px-1 py-0.5">
                                        {cell == null ? 'NULL' : String(cell)}
                                      </td>
                                    ))}
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      )}
                    </li>
                  )
                })}
              </ul>
            </aside>

            <section className="flex min-h-0 flex-col gap-3">
              <div
                className={cn(
                  'min-h-[240px] rounded-[5px] border border-[var(--color-border)] bg-[var(--color-surface)]',
                  mobileTab === 'editor' ? 'block' : 'hidden md:block',
                )}
              >
                <div className="flex flex-wrap items-center gap-2 border-b border-[var(--color-border)] p-2">
                  <Button
                    type="button"
                    variant="primary"
                    onClick={handleRun}
                    disabled={runMutation.isPending || !query.trim()}
                  >
                    {runMutation.isPending ? (
                      <span className="inline-flex items-center gap-2">
                        <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
                        Running
                      </span>
                    ) : (
                      'Run query'
                    )}
                  </Button>
                  <Button type="button" variant="secondary" onClick={resetQuery}>
                    Reset query
                  </Button>
                  <span className="text-xs text-[var(--color-text-muted)]">
                    Drafts stay in this browser. Row limit {datasetQuery.data.row_limit}. Timeout{' '}
                    {datasetQuery.data.timeout_ms} ms.
                  </span>
                </div>
                <SqlEditor
                  ref={editorRef}
                  value={query}
                  onChange={setQuery}
                  height="280px"
                  schemaTables={schemaTables}
                  onRun={handleRun}
                  showHeader={false}
                />
              </div>

              <div
                className={cn(
                  'min-h-[180px] rounded-[5px] border border-[var(--color-border)] bg-[var(--color-surface)] p-3',
                  mobileTab === 'results' ? 'block' : 'hidden md:block',
                )}
              >
                <h2 className="text-sm font-semibold">Results</h2>
                {runMutation.isPending && (
                  <p role="status" className="mt-2 text-sm">
                    Running query…
                  </p>
                )}
                {!runMutation.isPending && !result && (
                  <p className="mt-2 text-sm text-[var(--color-text-muted)]">
                    Run a query to see rows here. This panel never creates a grade.
                  </p>
                )}
                {result?.error && (
                  <p role="alert" className="mt-2 text-sm text-[var(--color-danger)]">
                    {result.error}
                  </p>
                )}
                {result && !result.error && (
                  <div className="mt-2 space-y-2 text-sm">
                    <p>
                      {result.row_count} row{result.row_count === 1 ? '' : 's'}
                      {result.execution_time_ms != null
                        ? ` · ${result.execution_time_ms.toFixed(1)} ms`
                        : ''}
                      {result.truncated
                        ? ` · showing first ${result.row_limit} rows`
                        : ''}
                    </p>
                    <div className="overflow-x-auto">
                      <table className="min-w-full text-xs">
                        <thead>
                          <tr>
                            {result.columns.map((column) => (
                              <th key={column} className="border-b px-2 py-1 text-left">
                                {column}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {result.rows.map((row, index) => (
                            <tr key={index}>
                              {row.map((cell, cellIndex) => (
                                <td key={cellIndex} className="px-2 py-1">
                                  {cell == null ? 'NULL' : String(cell)}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    <p className="text-xs text-[var(--color-text-muted)]">{result.note}</p>
                  </div>
                )}
              </div>
            </section>
          </div>
        </>
      )}
    </div>
  )
}
