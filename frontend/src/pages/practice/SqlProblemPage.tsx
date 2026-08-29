import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Bookmark } from 'lucide-react'

import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { Card } from '@/components/common/Card'
import { SqlEditor } from '@/features/sql/SqlEditor'
import { SqlResultTable } from '@/features/sql/SqlResultTable'
import { SqlSchemaExplorer } from '@/features/sql/SqlSchemaExplorer'
import { SqlSolutionViewer } from '@/features/sql/SqlSolutionViewer'
import { useAuth } from '@/hooks/useAuth'
import {
  fetchSqlExecutionStatus,
  fetchSqlProblem,
  fetchSqlProblemSubmissions,
  fetchSqlSolution,
  runSqlQuery,
  submitSqlQuery,
  toggleSqlBookmark,
} from '@/services/sqlService'
import type { SqlRunResponse, SqlSubmitResponse } from '@/types/sql'

type Tab = 'problem' | 'schema' | 'hints' | 'submissions'
type ResultMode = 'run' | 'submit' | null

const STARTER_QUERY = '-- Write your SQL query here\n'

function draftKey(userId: string, problemId: string) {
  return `sql-draft:${userId}:${problemId}`
}

export function SqlProblemPage() {
  const { slug = '' } = useParams()
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [tab, setTab] = useState<Tab>('problem')
  const [query, setQuery] = useState(STARTER_QUERY)
  const [draftReady, setDraftReady] = useState(false)
  const [runResult, setRunResult] = useState<SqlRunResponse | null>(null)
  const [submitResult, setSubmitResult] = useState<SqlSubmitResponse | null>(null)
  const [resultMode, setResultMode] = useState<ResultMode>(null)
  const [showSolution, setShowSolution] = useState(false)
  const skipSaveRef = useRef(false)

  const { data: problem, isLoading } = useQuery({
    queryKey: ['sql-problem', slug],
    queryFn: () => fetchSqlProblem(slug),
    enabled: Boolean(slug),
  })

  const { data: executionStatus } = useQuery({
    queryKey: ['sql-execution-status'],
    queryFn: fetchSqlExecutionStatus,
    refetchInterval: 30000,
  })

  const { data: submissions } = useQuery({
    queryKey: ['sql-problem-submissions', problem?.id],
    queryFn: () => fetchSqlProblemSubmissions(problem!.id, 20),
    enabled: tab === 'submissions' && Boolean(problem?.id),
  })

  const solutionUnlocked =
    problem?.solution_unlocked ||
    submitResult?.solution_unlocked ||
    submitResult?.status === 'accepted'

  const { data: solution } = useQuery({
    queryKey: ['sql-solution', problem?.id],
    queryFn: () => fetchSqlSolution(problem!.id),
    enabled: Boolean(problem?.id) && Boolean(solutionUnlocked) && showSolution,
  })

  useEffect(() => {
    if (!user?.id || !problem?.id) return
    skipSaveRef.current = true
    const stored = localStorage.getItem(draftKey(user.id, problem.id))
    setQuery(stored ?? STARTER_QUERY)
    setDraftReady(true)
    skipSaveRef.current = false
  }, [user?.id, problem?.id])

  useEffect(() => {
    if (!user?.id || !problem?.id || !draftReady || skipSaveRef.current) return
    localStorage.setItem(draftKey(user.id, problem.id), query)
  }, [user?.id, problem?.id, query, draftReady])

  const resetQuery = useCallback(() => {
    if (user?.id && problem?.id) {
      localStorage.removeItem(draftKey(user.id, problem.id))
    }
    skipSaveRef.current = true
    setQuery(STARTER_QUERY)
    skipSaveRef.current = false
  }, [user?.id, problem?.id])

  const executionAvailable =
    problem?.execution_available !== false && executionStatus?.available !== false

  const runMutation = useMutation({
    mutationFn: () => runSqlQuery(problem!.id, query),
    onSuccess: (data) => {
      setRunResult(data)
      setResultMode('run')
    },
  })

  const submitMutation = useMutation({
    mutationFn: () => submitSqlQuery(problem!.id, query),
    onSuccess: (data) => {
      setSubmitResult(data)
      setResultMode('submit')
      if (data.solution_unlocked || data.status === 'accepted') {
        setShowSolution(false)
      }
      queryClient.invalidateQueries({ queryKey: ['sql-progress'] })
      queryClient.invalidateQueries({ queryKey: ['sql-problem', slug] })
      queryClient.invalidateQueries({ queryKey: ['sql-problem-submissions', problem?.id] })
    },
  })

  const bookmarkMutation = useMutation({
    mutationFn: () => toggleSqlBookmark(problem!.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['sql-problem', slug] }),
  })

  const isBusy = runMutation.isPending || submitMutation.isPending

  if (isLoading || !problem || !draftReady) {
    return <p className="text-sm text-[var(--color-text-muted)]">Loading problem...</p>
  }

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Link to="/practice/sql" className="text-xs text-[var(--color-accent)] hover:underline">
            ← Back to problems
          </Link>
          <h2 className="text-lg font-semibold text-[var(--color-text)]">{problem.title}</h2>
          <div className="mt-1 flex flex-wrap gap-2">
            <Badge>{problem.difficulty}</Badge>
            {problem.progress_status && <Badge variant="success">{problem.progress_status}</Badge>}
            {problem.topic_name && <Badge>{problem.topic_name}</Badge>}
            {(problem.role_tags ?? []).map((tag) => (
              <Badge key={tag}>{tag}</Badge>
            ))}
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => bookmarkMutation.mutate()}
            disabled={bookmarkMutation.isPending}
          >
            <Bookmark className="h-4 w-4" />
            {problem.bookmarked ? 'Bookmarked' : 'Bookmark'}
          </Button>
          {solutionUnlocked && (
            <Button variant="secondary" size="sm" onClick={() => setShowSolution((v) => !v)}>
              {showSolution ? 'Hide Solution' : 'View Solution'}
            </Button>
          )}
          <Button variant="secondary" onClick={resetQuery}>
            Reset
          </Button>
          <Button
            variant="secondary"
            disabled={!executionAvailable || isBusy || !query.trim()}
            onClick={() => runMutation.mutate()}
          >
            {runMutation.isPending ? 'Running...' : 'Run'}
          </Button>
          <Button
            variant="primary"
            disabled={!executionAvailable || isBusy || !query.trim()}
            onClick={() => submitMutation.mutate()}
          >
            {submitMutation.isPending ? 'Submitting...' : 'Submit'}
          </Button>
        </div>
      </div>

      {!executionAvailable && (
        <div className="rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-100">
          {executionStatus?.message ??
            'SQL execution is currently unavailable. You can still read the problem, explore the schema, and edit your query.'}
        </div>
      )}

      {showSolution && solution && (
        <Card padding="md" className="overflow-y-auto">
          <SqlSolutionViewer solution={solution} />
        </Card>
      )}

      <div className="grid min-h-0 flex-1 gap-4 lg:grid-cols-2">
        <div className="flex min-h-0 flex-col gap-3">
          <div className="flex gap-2 border-b border-[var(--color-border)]">
            {(['problem', 'schema', 'hints', 'submissions'] as Tab[]).map((key) => (
              <button
                key={key}
                type="button"
                onClick={() => setTab(key)}
                className={`border-b-2 px-3 py-2 text-sm capitalize ${
                  tab === key
                    ? 'border-[var(--color-accent)] text-[var(--color-accent)]'
                    : 'border-transparent text-[var(--color-text-muted)]'
                }`}
              >
                {key}
              </button>
            ))}
          </div>

          <Card className="min-h-0 flex-1 overflow-y-auto" padding="md">
            {tab === 'problem' && (
              <div className="space-y-4 text-sm">
                {problem.scenario && (
                  <div>
                    <h4 className="font-medium">Scenario</h4>
                    <p className="mt-1 whitespace-pre-wrap text-[var(--color-text-muted)]">
                      {problem.scenario}
                    </p>
                  </div>
                )}
                <div>
                  <h4 className="font-medium">Description</h4>
                  <p className="mt-1 whitespace-pre-wrap text-[var(--color-text)]">
                    {problem.description}
                  </p>
                </div>
                <div>
                  <h4 className="font-medium">Task</h4>
                  <p className="mt-1 whitespace-pre-wrap text-[var(--color-text-muted)]">
                    {problem.task_description}
                  </p>
                </div>
                {problem.expected_columns.length > 0 && (
                  <div>
                    <h4 className="font-medium">Expected columns</h4>
                    <p className="mt-1 font-mono text-xs text-[var(--color-text-muted)]">
                      {problem.expected_columns.join(', ')}
                    </p>
                  </div>
                )}
                {problem.sample_expected_rows.length > 0 && (
                  <div>
                    <h4 className="mb-2 font-medium">Sample expected rows</h4>
                    <SqlResultTable
                      columns={problem.expected_columns}
                      rows={problem.sample_expected_rows}
                    />
                  </div>
                )}
              </div>
            )}

            {tab === 'schema' && (
              <SqlSchemaExplorer problemId={problem.id} tables={problem.schema_tables} />
            )}

            {tab === 'hints' && (
              <div className="space-y-3">
                {problem.hints.length === 0 ? (
                  <p className="text-sm text-[var(--color-text-muted)]">No hints for this problem.</p>
                ) : (
                  problem.hints.map((hint, index) => (
                    <div
                      key={index}
                      className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface-muted)] p-3 text-sm"
                    >
                      <p className="mb-1 text-xs font-medium text-[var(--color-text-subtle)]">
                        Hint {index + 1}
                      </p>
                      <p className="text-[var(--color-text)]">{hint}</p>
                    </div>
                  ))
                )}
              </div>
            )}

            {tab === 'submissions' && (
              <div className="space-y-2">
                <h3 className="mb-3 text-sm font-medium">Your submissions</h3>
                {submissions?.items.length ? (
                  submissions.items.map((sub) => (
                    <Link
                      key={sub.id}
                      to={`/sql/submissions/${sub.id}`}
                      className="flex items-center justify-between rounded-md border border-[var(--color-border)] px-3 py-2 text-sm hover:bg-[var(--color-surface-muted)]"
                    >
                      <div>
                        <p className="font-medium capitalize">{sub.status.replace(/_/g, ' ')}</p>
                        <p className="text-xs text-[var(--color-text-muted)]">
                          {sub.result_row_count != null ? `${sub.result_row_count} rows · ` : ''}
                          {new Date(sub.submitted_at).toLocaleString()}
                        </p>
                      </div>
                      {sub.execution_time_ms != null && (
                        <Badge>{sub.execution_time_ms.toFixed(0)} ms</Badge>
                      )}
                    </Link>
                  ))
                ) : (
                  <p className="text-sm text-[var(--color-text-muted)]">No submissions yet.</p>
                )}
              </div>
            )}
          </Card>
        </div>

        <div className="flex min-h-0 flex-col gap-3">
          <Card className="min-h-[280px] flex-1 overflow-hidden p-0">
            <SqlEditor value={query} onChange={setQuery} height="100%" />
          </Card>

          <Card padding="md" className="max-h-64 overflow-y-auto">
            <h4 className="mb-3 text-sm font-medium">Results</h4>
            {resultMode === 'run' && runResult && (
              <div className="space-y-3">
                {runResult.error ? (
                  <p className="text-sm text-red-600 dark:text-red-400">{runResult.error}</p>
                ) : (
                  <>
                    <p className="text-xs text-[var(--color-text-muted)]">
                      {runResult.row_count} row{runResult.row_count === 1 ? '' : 's'}
                      {runResult.execution_time_ms != null &&
                        ` · ${runResult.execution_time_ms.toFixed(0)} ms`}
                    </p>
                    <SqlResultTable
                      columns={runResult.columns}
                      rows={runResult.rows}
                      truncated={runResult.truncated}
                    />
                  </>
                )}
              </div>
            )}

            {resultMode === 'submit' && submitResult && (
              <div className="space-y-3">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge
                    variant={
                      submitResult.status === 'accepted'
                        ? 'success'
                        : submitResult.status === 'wrong_answer'
                          ? 'warning'
                          : 'default'
                    }
                  >
                    {submitResult.status.replace(/_/g, ' ')}
                  </Badge>
                  {submitResult.execution_time_ms != null && (
                    <span className="text-xs text-[var(--color-text-muted)]">
                      {submitResult.execution_time_ms.toFixed(0)} ms
                    </span>
                  )}
                </div>
                <p className="text-sm text-[var(--color-text)]">{submitResult.message}</p>
                {submitResult.error && (
                  <p className="text-sm text-red-600 dark:text-red-400">{submitResult.error}</p>
                )}
                {submitResult.status === 'wrong_answer' && submitResult.feedback && (
                  <p className="text-sm text-[var(--color-text-muted)]">
                    {typeof submitResult.feedback.message === 'string'
                      ? submitResult.feedback.message
                      : submitResult.message}
                  </p>
                )}
                {submitResult.status === 'accepted' && submitResult.columns.length > 0 && (
                  <SqlResultTable
                    columns={submitResult.columns}
                    rows={submitResult.rows}
                    truncated={submitResult.truncated}
                  />
                )}
                {submitResult.status === 'wrong_answer' && (
                  <p className="text-xs text-[var(--color-text-subtle)]">
                    Expected result rows are hidden. Use the feedback above to adjust your query.
                  </p>
                )}
              </div>
            )}

            {!resultMode && (
              <p className="text-sm text-[var(--color-text-muted)]">
                Run or submit your query to see results here.
              </p>
            )}
          </Card>
        </div>
      </div>
    </div>
  )
}
