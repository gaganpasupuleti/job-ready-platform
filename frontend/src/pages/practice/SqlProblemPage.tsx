import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Bookmark } from 'lucide-react'

import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { Card } from '@/components/common/Card'
import {
  EmptyState,
  ErrorState,
  HintPanel,
  LoadingState,
  PracticeHeader,
  PracticeStatusBadge,
  PracticeTabs,
  ProblemNavigator,
  SuccessState,
  WorkspaceSplit,
} from '@/components/practice-workspace/PracticeWorkspace'
import {
  apiErrorMessage,
  useWorkspaceShortcuts,
} from '@/components/practice-workspace/practiceWorkspaceUtils'
import { SqlEditor } from '@/features/sql/SqlEditor'
import { SqlResultTable } from '@/features/sql/SqlResultTable'
import { SqlSchemaExplorer } from '@/features/sql/SqlSchemaExplorer'
import { SqlSolutionViewer } from '@/features/sql/SqlSolutionViewer'
import { useAuth } from '@/hooks/useAuth'
import {
  fetchSqlExecutionStatus,
  fetchSqlNavigation,
  fetchSqlProblem,
  fetchSqlProblemSubmissions,
  fetchSqlSolution,
  runSqlQuery,
  submitSqlQuery,
  toggleSqlBookmark,
} from '@/services/sqlService'
import type { SqlRunResponse, SqlSubmitResponse } from '@/types/sql'

type Tab = 'problem' | 'schema' | 'hints' | 'submissions' | 'solution'
type ResultMode = 'run' | 'submit' | null

const STARTER_QUERY = '-- Write your SQL query here\n'

function draftKey(userId: string, problemId: string) {
  return `sql-draft:${userId}:${problemId}`
}

export function SqlProblemPage() {
  const { slug = '' } = useParams()
  const [searchParams] = useSearchParams()
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [tab, setTab] = useState<Tab>('problem')
  const [query, setQuery] = useState(STARTER_QUERY)
  const [draftReady, setDraftReady] = useState(false)
  const [runResult, setRunResult] = useState<SqlRunResponse | null>(null)
  const [submitResult, setSubmitResult] = useState<SqlSubmitResponse | null>(null)
  const [resultMode, setResultMode] = useState<ResultMode>(null)
  const [revealedHints, setRevealedHints] = useState(0)
  const [mobileTab, setMobileTab] = useState<'problem' | 'code' | 'output'>('problem')
  const [actionError, setActionError] = useState<string | null>(null)
  const skipSaveRef = useRef(false)

  const { data: problem, isLoading, error } = useQuery({
    queryKey: ['sql-problem', slug],
    queryFn: () => fetchSqlProblem(slug),
    enabled: Boolean(slug),
  })

  const { data: navigation } = useQuery({
    queryKey: ['sql-nav', slug],
    queryFn: () => fetchSqlNavigation(slug),
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
    enabled: Boolean(problem?.id) && Boolean(solutionUnlocked) && tab === 'solution',
  })

  useEffect(() => {
    if (!user?.id || !problem?.id) return
    skipSaveRef.current = true
    const stored = localStorage.getItem(draftKey(user.id, problem.id))
    setQuery(stored ?? STARTER_QUERY)
    setDraftReady(true)
    setRevealedHints(0)
    skipSaveRef.current = false
  }, [user?.id, problem?.id])

  useEffect(() => {
    if (!user?.id || !problem?.id || !draftReady || skipSaveRef.current) return
    localStorage.setItem(draftKey(user.id, problem.id), query)
  }, [user?.id, problem?.id, query, draftReady])

  const resetQuery = useCallback(() => {
    if (query !== STARTER_QUERY && !window.confirm('Reset your query to the starter draft?')) return
    if (user?.id && problem?.id) localStorage.removeItem(draftKey(user.id, problem.id))
    skipSaveRef.current = true
    setQuery(STARTER_QUERY)
    skipSaveRef.current = false
  }, [problem?.id, query, user?.id])

  const executionAvailable =
    problem?.execution_available !== false && executionStatus?.available !== false

  const runMutation = useMutation({
    mutationFn: () => runSqlQuery(problem!.id, query),
    onSuccess: (data) => {
      setActionError(null)
      setRunResult(data)
      setResultMode('run')
      setMobileTab('output')
    },
    onError: (err) => {
      setActionError(apiErrorMessage(err, 'Could not run query.'))
      setResultMode('run')
      setRunResult(null)
    },
  })

  const submitMutation = useMutation({
    mutationFn: () => submitSqlQuery(problem!.id, query),
    onSuccess: (data) => {
      setActionError(null)
      setSubmitResult(data)
      setResultMode('submit')
      setMobileTab('output')
      void queryClient.invalidateQueries({ queryKey: ['sql-progress'] })
      void queryClient.invalidateQueries({ queryKey: ['sql-problem', slug] })
      void queryClient.invalidateQueries({ queryKey: ['sql-nav', slug] })
      void queryClient.invalidateQueries({ queryKey: ['sql-problem-submissions', problem?.id] })
    },
    onError: (err) => {
      setActionError(apiErrorMessage(err, 'Could not submit query.'))
      setResultMode('submit')
    },
  })

  const bookmarkMutation = useMutation({
    mutationFn: () => toggleSqlBookmark(problem!.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['sql-problem', slug] }),
  })

  const isBusy = runMutation.isPending || submitMutation.isPending
  useWorkspaceShortcuts({
    enabled: Boolean(problem) && executionAvailable && !isBusy,
    run: () => runMutation.mutate(),
    submit: () => submitMutation.mutate(),
  })

  if (isLoading || !draftReady) return <LoadingState label="Loading SQL problem" />
  if (error || !problem) return <ErrorState message={apiErrorMessage(error, 'SQL problem not found.')} />

  const projectReturn = searchParams.get('fromProject')
  const leftPanel = (
    <div className="flex h-full min-h-0 flex-col gap-3">
      <PracticeTabs
        tabs={[
          { id: 'problem', label: 'Problem' },
          { id: 'schema', label: 'Schema' },
          { id: 'hints', label: 'Hints' },
          { id: 'submissions', label: 'Submissions' },
          { id: 'solution', label: 'Solution' },
        ]}
        value={tab}
        onChange={(id) => setTab(id as Tab)}
      />
      <Card className="min-h-0 flex-1 overflow-y-auto" padding="md">
        {tab === 'problem' && (
          <div className="space-y-4 text-sm">
            {problem.scenario && (
              <div>
                <h2 className="font-medium">Scenario</h2>
                <p className="mt-1 whitespace-pre-wrap text-[var(--color-text-muted)]">{problem.scenario}</p>
              </div>
            )}
            <div>
              <h2 className="font-medium">Description</h2>
              <p className="mt-1 whitespace-pre-wrap">{problem.description}</p>
            </div>
            <div>
              <h3 className="font-medium">Task</h3>
              <p className="mt-1 whitespace-pre-wrap text-[var(--color-text-muted)]">{problem.task_description}</p>
            </div>
            {problem.sample_expected_rows.length > 0 && (
              <div>
                <h3 className="mb-2 font-medium">Sample expected rows</h3>
                <SqlResultTable columns={problem.expected_columns} rows={problem.sample_expected_rows} />
              </div>
            )}
          </div>
        )}
        {tab === 'schema' && <SqlSchemaExplorer problemId={problem.id} tables={problem.schema_tables} />}
        {tab === 'hints' && (
          <HintPanel
            hints={problem.hints}
            revealed={revealedHints}
            onReveal={() => setRevealedHints((n) => n + 1)}
          />
        )}
        {tab === 'submissions' && (
          <div className="space-y-2">
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
                      {new Date(sub.submitted_at).toLocaleString()}
                    </p>
                  </div>
                </Link>
              ))
            ) : (
              <EmptyState title="No submissions yet" description="Run and submit a query to build history." />
            )}
          </div>
        )}
        {tab === 'solution' &&
          (solutionUnlocked ? (
            solution ? (
              <SqlSolutionViewer solution={solution} />
            ) : (
              <EmptyState title="Loading solution" />
            )
          ) : (
            <EmptyState
              title="Solution locked"
              description="Submit an accepted query to unlock the official solution."
            />
          ))}
      </Card>
      {navigation && (
        <ProblemNavigator
          items={navigation.items.map((item) => ({
            id: item.id,
            title: item.title,
            status: item.status,
            href: item.href,
          }))}
          currentId={problem.id}
        />
      )}
    </div>
  )

  const results = (
    <Card padding="md" className="h-full overflow-auto">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-medium">Results</h3>
        {resultMode === 'run' && <Badge>Run output</Badge>}
        {resultMode === 'submit' && <Badge variant="accent">Submit verdict</Badge>}
      </div>
      {actionError && <ErrorState message={actionError} />}
      {resultMode === 'run' && runResult && (
        <div className="space-y-3">
          {runResult.error ? (
            <ErrorState message={runResult.error} />
          ) : (
            <>
              <p className="text-xs text-[var(--color-text-muted)]">
                {runResult.row_count} row{runResult.row_count === 1 ? '' : 's'}
                {runResult.execution_time_ms != null && ` · ${runResult.execution_time_ms.toFixed(0)} ms`}
                {runResult.truncated ? ' · truncated' : ''}
              </p>
              <SqlResultTable columns={runResult.columns} rows={runResult.rows} truncated={runResult.truncated} />
            </>
          )}
        </div>
      )}
      {resultMode === 'submit' && submitResult && (
        <div className="space-y-3">
          {submitResult.status === 'accepted' ? (
            <SuccessState title="✓ Accepted">
              <p>
                {submitResult.result_row_count ?? submitResult.rows.length} rows
                {submitResult.execution_time_ms != null && ` · ${submitResult.execution_time_ms.toFixed(0)} ms`}
              </p>
              <div className="mt-2 flex gap-2">
                <Button size="sm" onClick={() => setTab('solution')}>
                  View Solution
                </Button>
                {navigation?.next && (
                  <Link to={navigation.next.href} className="text-sm text-[var(--color-accent)] hover:underline">
                    Next Problem
                  </Link>
                )}
              </div>
            </SuccessState>
          ) : (
            <div>
              <Badge variant={submitResult.status === 'wrong_answer' ? 'warning' : 'default'}>
                {submitResult.status.replace(/_/g, ' ')}
              </Badge>
              <p className="mt-2 text-sm">{submitResult.message}</p>
              {submitResult.error && <ErrorState message={submitResult.error} />}
              {submitResult.status === 'wrong_answer' && (
                <p className="mt-2 text-xs text-[var(--color-text-subtle)]">
                  Expected result rows stay hidden. Use the feedback to adjust your query.
                </p>
              )}
            </div>
          )}
        </div>
      )}
      {!resultMode && !actionError && (
        <EmptyState title="No results yet" description="Run shows query output. Submit compares against the expected result." />
      )}
    </Card>
  )

  return (
    <div className="flex h-[calc(100vh-7rem)] min-h-[28rem] flex-col gap-3 overflow-hidden">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <PracticeHeader backTo={projectReturn ? `/projects/${projectReturn}` : '/practice/sql'} backLabel="Back" title={problem.title}>
          <div className="mt-1 flex flex-wrap gap-2">
            <Badge>{problem.difficulty}</Badge>
            <PracticeStatusBadge status={problem.progress_status} />
            {problem.topic_name && <Badge>{problem.topic_name}</Badge>}
          </div>
        </PracticeHeader>
        <div className="flex flex-wrap items-center gap-2">
          {navigation?.previous && (
            <Link to={navigation.previous.href}>
              <Button variant="ghost" size="sm">
                Previous
              </Button>
            </Link>
          )}
          {navigation?.next && (
            <Link to={navigation.next.href}>
              <Button variant="ghost" size="sm">
                Next
              </Button>
            </Link>
          )}
          <Button variant="ghost" size="sm" onClick={() => bookmarkMutation.mutate()} aria-label="Bookmark problem">
            <Bookmark className="h-4 w-4" />
            {problem.bookmarked ? 'Bookmarked' : 'Bookmark'}
          </Button>
          <Button variant="secondary" onClick={resetQuery}>
            Reset
          </Button>
          <Button
            variant="secondary"
            disabled={!executionAvailable || isBusy}
            onClick={() => runMutation.mutate()}
          >
            {runMutation.isPending ? 'Running...' : 'Run'}
          </Button>
          <Button
            variant="primary"
            disabled={!executionAvailable || isBusy}
            onClick={() => submitMutation.mutate()}
          >
            {submitMutation.isPending ? 'Submitting...' : 'Submit'}
          </Button>
        </div>
      </div>
      {navigation && (
        <p className="text-xs text-[var(--color-text-muted)]">
          Problem {navigation.position} of {navigation.total}
        </p>
      )}
      <WorkspaceSplit
        storageKey="sql-split"
        left={leftPanel}
        right={
          <Card className="h-full min-h-[240px] overflow-hidden p-0">
            <SqlEditor value={query} onChange={setQuery} height="100%" />
          </Card>
        }
        bottom={results}
        mobileTab={mobileTab}
        onMobileTab={setMobileTab}
      />
    </div>
  )
}
