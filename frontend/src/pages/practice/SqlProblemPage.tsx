import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Bookmark, Loader2 } from 'lucide-react'

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
} from '@/components/practice-workspace/PracticeWorkspace'
import { apiErrorMessage } from '@/components/practice-workspace/practiceWorkspaceUtils'
import { SqlBottomPanel, type SqlBottomTab } from '@/features/sql/SqlBottomPanel'
import { SqlEditor, type SqlEditorHandle } from '@/features/sql/SqlEditor'
import { SqlQuestionLearningGuide } from '@/features/sql/SqlQuestionLearningGuide'
import { SqlQueryTemplates } from '@/features/sql/SqlQueryTemplates'
import { SqlReviewCtas } from '@/features/sql/SqlReviewCtas'
import { SqlSchemaExplorer } from '@/features/sql/SqlSchemaExplorer'
import { SqlSolutionViewer } from '@/features/sql/SqlSolutionViewer'
import { SqlPaneCollapseButton } from '@/features/sql/workbench/SqlPaneChrome'
import { SqlWorkbenchLayout } from '@/features/sql/workbench/SqlWorkbenchLayout'
import { useResizableSqlLayout } from '@/features/sql/workbench/useResizableSqlLayout'
import { formatSqlQuery } from '@/features/sql/utils/sqlFormatter'
import { useAuth } from '@/hooks/useAuth'
import { fetchMistakes, fetchMistakeSummary } from '@/services/mistakeService'
import {
  fetchSqlExecutionStatus,
  fetchSqlNavigation,
  fetchSqlProblem,
  fetchSqlProblemSubmissions,
  fetchSqlProgress,
  fetchSqlProblems,
  fetchSqlSolution,
  runSqlQuery,
  submitSqlQuery,
  toggleSqlBookmark,
} from '@/services/sqlService'
import type { SqlRunResponse, SqlSubmitResponse } from '@/types/sql'

type QuestionTab = 'problem' | 'hints' | 'solution'
type ResultMode = 'run' | 'submit' | null
type RunState = 'ready' | 'running' | 'success' | 'error' | 'submitting' | 'passed' | 'failed'

const STARTER_QUERY = '-- Write your SQL query here\n'

function draftKey(userId: string, problemId: string) {
  return `sql-draft:${userId}:${problemId}`
}

export function SqlProblemPage() {
  const { slug = '' } = useParams()
  const [searchParams] = useSearchParams()
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const layout = useResizableSqlLayout()
  const editorRef = useRef<SqlEditorHandle>(null)

  const [questionTab, setQuestionTab] = useState<QuestionTab>('problem')
  const [query, setQuery] = useState(STARTER_QUERY)
  const [draftReady, setDraftReady] = useState(false)
  const [runResult, setRunResult] = useState<SqlRunResponse | null>(null)
  const [submitResult, setSubmitResult] = useState<SqlSubmitResponse | null>(null)
  const [resultMode, setResultMode] = useState<ResultMode>(null)
  const [revealedHints, setRevealedHints] = useState(0)
  const [mobileTab, setMobileTab] = useState<'problem' | 'code' | 'output'>('problem')
  const [actionError, setActionError] = useState<string | null>(null)
  const [messages, setMessages] = useState<string[]>([])
  const [preferredBottomTab, setPreferredBottomTab] = useState<SqlBottomTab | null>(null)
  const [editorStatus, setEditorStatus] = useState<string | null>(null)
  const [runState, setRunState] = useState<RunState>('ready')
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
    enabled: Boolean(problem?.id),
  })

  const { data: progress } = useQuery({
    queryKey: ['sql-progress'],
    queryFn: fetchSqlProgress,
  })

  const { data: sqlMistakes } = useQuery({
    queryKey: ['mistakes', 'sql', 'unresolved'],
    queryFn: () => fetchMistakes({ source_type: 'sql', view: 'unresolved' }),
  })

  const { data: mistakeSummary } = useQuery({
    queryKey: ['mistakes-summary'],
    queryFn: fetchMistakeSummary,
  })

  const { data: unsolvedProblems } = useQuery({
    queryKey: ['sql-problems', 'unsolved-for-cta'],
    queryFn: () => fetchSqlProblems({ status: 'unsolved', limit: 5 }),
  })

  const solutionUnlocked =
    problem?.solution_unlocked ||
    submitResult?.solution_unlocked ||
    submitResult?.status === 'accepted'

  const { data: solution } = useQuery({
    queryKey: ['sql-solution', problem?.id],
    queryFn: () => fetchSqlSolution(problem!.id),
    enabled: Boolean(problem?.id) && Boolean(solutionUnlocked) && questionTab === 'solution',
  })

  useEffect(() => {
    if (!user?.id || !problem?.id) return
    skipSaveRef.current = true
    const stored = localStorage.getItem(draftKey(user.id, problem.id))
    setQuery(stored ?? STARTER_QUERY)
    setDraftReady(true)
    setRevealedHints(0)
    setRunResult(null)
    setSubmitResult(null)
    setResultMode(null)
    setActionError(null)
    setMessages([])
    setRunState('ready')
    setQuestionTab('problem')
    skipSaveRef.current = false
  }, [user?.id, problem?.id])

  useEffect(() => {
    if (!user?.id || !problem?.id || !draftReady || skipSaveRef.current) return
    localStorage.setItem(draftKey(user.id, problem.id), query)
  }, [user?.id, problem?.id, query, draftReady])

  const clearOutput = useCallback(() => {
    setRunResult(null)
    setSubmitResult(null)
    setResultMode(null)
    setActionError(null)
    setMessages(['Ready'])
    setRunState('ready')
    setPreferredBottomTab('messages')
    setEditorStatus('Output cleared')
  }, [])

  const resetQuery = useCallback(() => {
    if (query !== STARTER_QUERY && !window.confirm('Reset your query to the starter draft?')) return
    if (user?.id && problem?.id) localStorage.removeItem(draftKey(user.id, problem.id))
    skipSaveRef.current = true
    setQuery(STARTER_QUERY)
    editorRef.current?.replaceSql(STARTER_QUERY)
    skipSaveRef.current = false
    clearOutput()
    setEditorStatus('Query reset to starter')
  }, [clearOutput, problem?.id, query, user?.id])

  const formatSql = useCallback(() => {
    const next = formatSqlQuery(query)
    setQuery(next)
    editorRef.current?.replaceSql(next)
    setEditorStatus('SQL formatted locally')
    setMessages((prev) => [...prev.slice(-19), 'SQL formatted locally.'])
  }, [query])

  const executionAvailable =
    problem?.execution_available !== false && executionStatus?.available !== false

  const runMutation = useMutation({
    mutationFn: () => runSqlQuery(problem!.id, query),
    onMutate: () => {
      setRunState('running')
      setActionError(null)
    },
    onSuccess: (data) => {
      setActionError(null)
      setRunResult(data)
      setResultMode('run')
      setMobileTab('output')
      setPreferredBottomTab('results')
      if (data.error) {
        setRunState('error')
        setMessages((prev) => [...prev.slice(-19), data.error!])
      } else {
        setRunState('success')
        setMessages((prev) => [
          ...prev.slice(-19),
          `Run returned ${data.row_count} row${data.row_count === 1 ? '' : 's'}.`,
        ])
      }
    },
    onError: (err) => {
      const msg = apiErrorMessage(err, 'Could not run query.')
      setActionError(msg)
      setResultMode('run')
      setRunResult(null)
      setRunState('error')
      setPreferredBottomTab('messages')
      setMobileTab('output')
      setMessages((prev) => [...prev.slice(-19), msg])
    },
  })

  const submitMutation = useMutation({
    mutationFn: () => submitSqlQuery(problem!.id, query),
    onMutate: () => {
      setRunState('submitting')
      setActionError(null)
    },
    onSuccess: (data) => {
      setActionError(null)
      setSubmitResult(data)
      setResultMode('submit')
      setMobileTab('output')
      setPreferredBottomTab('results')
      setRunState(data.status === 'accepted' ? 'passed' : 'failed')
      setMessages((prev) => [...prev.slice(-19), data.message || data.status.replace(/_/g, ' ')])
      void queryClient.invalidateQueries({ queryKey: ['sql-progress'] })
      void queryClient.invalidateQueries({ queryKey: ['sql-problem', slug] })
      void queryClient.invalidateQueries({ queryKey: ['sql-nav', slug] })
      void queryClient.invalidateQueries({ queryKey: ['sql-problem-submissions', problem?.id] })
      void queryClient.invalidateQueries({ queryKey: ['mistakes'] })
    },
    onError: (err) => {
      const msg = apiErrorMessage(err, 'Could not submit query.')
      setActionError(msg)
      setResultMode('submit')
      setRunState('error')
      setPreferredBottomTab('messages')
      setMobileTab('output')
      setMessages((prev) => [...prev.slice(-19), msg])
    },
  })

  const bookmarkMutation = useMutation({
    mutationFn: () => toggleSqlBookmark(problem!.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['sql-problem', slug] }),
  })

  const isBusy = runMutation.isPending || submitMutation.isPending

  const firstMistakeHref = useMemo(() => {
    const open = sqlMistakes?.find((m) => m.retry_href)
    return open?.retry_href ?? null
  }, [sqlMistakes])

  const unsolvedHref = useMemo(() => {
    const item = unsolvedProblems?.items?.[0]
    if (!item) return '/practice/sql?status=unsolved'
    return `/practice/sql/${item.slug}`
  }, [unsolvedProblems])

  if (isLoading || !draftReady) return <LoadingState label="Loading SQL problem" />
  if (error || !problem) return <ErrorState message={apiErrorMessage(error, 'SQL problem not found.')} />

  const projectReturn = searchParams.get('fromProject')
  const runStateLabel: Record<RunState, string> = {
    ready: 'Ready',
    running: 'Running',
    success: 'Success',
    error: 'Error',
    submitting: 'Submitting',
    passed: 'Passed',
    failed: 'Failed',
  }

  const topBar = (
    <div className="space-y-2 border-b border-[var(--color-border)] pb-2">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <PracticeHeader
          backTo={projectReturn ? `/projects/${projectReturn}` : '/practice/sql'}
          backLabel="Back"
          title={problem.title}
        >
          <div className="mt-1 flex flex-wrap gap-2">
            <Badge>{problem.difficulty}</Badge>
            <PracticeStatusBadge status={problem.progress_status} />
            {problem.topic_name && <Badge>{problem.topic_name}</Badge>}
            <Badge variant="accent">{runStateLabel[runState]}</Badge>
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
          <Button
            variant="ghost"
            size="sm"
            onClick={() => bookmarkMutation.mutate()}
            aria-label="Bookmark problem"
          >
            <Bookmark className="h-4 w-4" />
            {problem.bookmarked ? 'Bookmarked' : 'Bookmark'}
          </Button>
          <Button variant="secondary" size="sm" onClick={resetQuery}>
            Reset
          </Button>
          <Button variant="secondary" size="sm" onClick={formatSql}>
            Format
          </Button>
          <Button variant="secondary" size="sm" onClick={clearOutput}>
            Clear Output
          </Button>
          <Button variant="ghost" size="sm" onClick={layout.resetLayout}>
            Reset Layout
          </Button>
          <Button
            variant="secondary"
            disabled={!executionAvailable || isBusy}
            onClick={() => runMutation.mutate()}
          >
            {runMutation.isPending ? (
              <>
                <Loader2 className="mr-1 h-4 w-4 animate-spin" />
                Running...
              </>
            ) : (
              'Run'
            )}
          </Button>
          <Button
            variant="primary"
            disabled={!executionAvailable || isBusy}
            onClick={() => submitMutation.mutate()}
          >
            {submitMutation.isPending ? (
              <>
                <Loader2 className="mr-1 h-4 w-4 animate-spin" />
                Submitting...
              </>
            ) : (
              'Submit'
            )}
          </Button>
        </div>
      </div>
      {navigation && (
        <p className="text-xs text-[var(--color-text-muted)]">
          Problem {navigation.position} of {navigation.total}
        </p>
      )}
      {!executionAvailable && (
        <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-100">
          SQL execution is temporarily unavailable. You can still edit drafts, review schema, hints,
          and submissions.
        </div>
      )}
    </div>
  )

  const objectExplorer = (
    <SqlSchemaExplorer
      problemId={problem.id}
      tables={problem.schema_tables}
      onInsertSnippet={(snippet) => {
        editorRef.current?.insertSnippet(snippet)
        setEditorStatus('Template inserted. Review and run when ready.')
        setMobileTab('code')
      }}
      onCollapse={layout.toggleLeftCollapsed}
    />
  )

  const questionPanel = (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex items-center justify-between border-b border-[var(--color-border)] px-3 py-2">
        <span className="text-sm font-medium text-[var(--color-text)]">Practice Question</span>
        <SqlPaneCollapseButton
          side="right"
          onClick={layout.toggleRightCollapsed}
          label="Problem"
        />
      </div>
      <div className="min-h-0 flex-1 space-y-3 overflow-auto p-3">
        <PracticeTabs
          tabs={[
            { id: 'problem', label: 'Problem' },
            { id: 'hints', label: 'Hints' },
            { id: 'solution', label: 'Solution' },
          ]}
          value={questionTab}
          onChange={(id) => setQuestionTab(id as QuestionTab)}
        />
        <Card className="min-h-0" padding="md">
          {questionTab === 'problem' && (
            <div className="space-y-4 text-sm">
              {problem.scenario && (
                <div>
                  <h2 className="font-medium">Scenario</h2>
                  <p className="mt-1 whitespace-pre-wrap text-[var(--color-text-muted)]">
                    {problem.scenario}
                  </p>
                </div>
              )}
              <div>
                <h2 className="font-medium">Description</h2>
                <p className="mt-1 whitespace-pre-wrap">{problem.description}</p>
              </div>
              <div>
                <h3 className="font-medium">Task</h3>
                <p className="mt-1 whitespace-pre-wrap text-[var(--color-text-muted)]">
                  {problem.task_description}
                </p>
              </div>
              {problem.expected_columns.length > 0 && (
                <div>
                  <h3 className="mb-1 font-medium">Expected columns</h3>
                  <div className="flex flex-wrap gap-1">
                    {problem.expected_columns.map((col) => (
                      <Badge key={col}>{col}</Badge>
                    ))}
                  </div>
                </div>
              )}
              <SqlQuestionLearningGuide problem={problem} />
              <SqlQueryTemplates
                tables={problem.schema_tables}
                onInsert={(sql) => {
                  editorRef.current?.insertSnippet(sql)
                  setEditorStatus('Quick query inserted')
                  setMobileTab('code')
                }}
              />
              {submitResult?.status === 'accepted' && (
                <div className="flex flex-wrap gap-2 rounded-md border border-emerald-300 bg-emerald-50 p-3 dark:border-emerald-800 dark:bg-emerald-950">
                  <p className="w-full text-sm font-medium text-emerald-800 dark:text-emerald-200">
                    Great work! What next?
                  </p>
                  <Button size="sm" onClick={() => setQuestionTab('solution')}>
                    View Solution
                  </Button>
                  {navigation?.next && (
                    <Link to={navigation.next.href}>
                      <Button size="sm" variant="secondary">
                        Next Problem
                      </Button>
                    </Link>
                  )}
                </div>
              )}
              {submitResult && submitResult.status !== 'accepted' && resultMode === 'submit' && (
                <div className="flex flex-wrap gap-2 rounded-md border border-[var(--color-border)] p-3">
                  <p className="w-full text-sm font-medium">Not quite — keep trying!</p>
                  <Button size="sm" variant="secondary" onClick={() => setMobileTab('code')}>
                    Try again
                  </Button>
                  {revealedHints < problem.hints.length && (
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => {
                        setQuestionTab('hints')
                        setRevealedHints((n) => n + 1)
                      }}
                    >
                      Reveal next hint
                    </Button>
                  )}
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      setPreferredBottomTab('expected')
                      setMobileTab('output')
                    }}
                  >
                    View sample expected
                  </Button>
                </div>
              )}
            </div>
          )}
          {questionTab === 'hints' && (
            <HintPanel
              hints={problem.hints}
              revealed={revealedHints}
              onReveal={() => setRevealedHints((n) => n + 1)}
            />
          )}
          {questionTab === 'solution' &&
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
        <SqlReviewCtas
          progress={progress}
          mistakes={sqlMistakes}
          mistakeSummary={mistakeSummary}
          unsolvedHref={unsolvedHref}
          firstMistakeHref={firstMistakeHref}
        />
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
    </div>
  )

  const editorPanel = (
    <Card className="h-full min-h-[240px] overflow-hidden p-0">
      <SqlEditor
        ref={editorRef}
        value={query}
        onChange={setQuery}
        height="100%"
        schemaTables={problem.schema_tables}
        onRun={() => {
          if (!executionAvailable || isBusy) return
          runMutation.mutate()
        }}
        onSubmit={() => {
          if (!executionAvailable || isBusy) return
          submitMutation.mutate()
        }}
        onFormatSql={formatSql}
        onClearOutput={clearOutput}
        editorStatus={editorStatus}
      />
    </Card>
  )

  const bottomPanel = (
    <SqlBottomPanel
      runResult={runResult}
      submitResult={submitResult}
      resultMode={resultMode}
      actionError={actionError}
      messages={messages}
      expectedColumns={problem.expected_columns}
      sampleExpectedRows={problem.sample_expected_rows}
      submissions={submissions?.items}
      preferredTab={preferredBottomTab}
      nextHref={navigation?.next?.href}
      onViewSolution={() => setQuestionTab('solution')}
      onCollapse={layout.toggleBottomCollapsed}
    />
  )

  return (
    <div className="flex h-[calc(100vh-7rem)] min-h-[28rem] flex-col overflow-hidden">
      <SqlWorkbenchLayout
        topBar={topBar}
        objectExplorer={objectExplorer}
        editorPanel={editorPanel}
        questionPanel={questionPanel}
        bottomPanel={bottomPanel}
        layout={layout}
        mobileTab={mobileTab}
        onMobileTab={setMobileTab}
      />
    </div>
  )
}
