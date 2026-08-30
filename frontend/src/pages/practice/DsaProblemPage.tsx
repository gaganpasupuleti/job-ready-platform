import { useMemo, useState } from 'react'
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
import { getMonacoLanguage } from '@/constants/languages'
import { CodeEditor } from '@/features/dsa/CodeEditor'
import { ExecutionResults } from '@/features/dsa/ExecutionResults'
import { useAuth } from '@/hooks/useAuth'
import { useCodingDraft } from '@/hooks/useCodingDraft'
import {
  fetchCodingNavigation,
  fetchCodingProblem,
  fetchExecutionStatus,
  fetchLanguages,
  fetchSubmissions,
  runCode,
  submitCode,
  toggleCodingBookmark,
} from '@/services/codingService'
import type { ExecutionResponse } from '@/types/coding'

type Tab = 'problem' | 'hints' | 'submissions' | 'solution'

export function DsaProblemPage() {
  const { problemId = '' } = useParams()
  const [searchParams] = useSearchParams()
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [tab, setTab] = useState<Tab>('problem')
  const [languageId, setLanguageId] = useState(71)
  const [lastResult, setLastResult] = useState<ExecutionResponse | null>(null)
  const [revealedHints, setRevealedHints] = useState(0)
  const [mobileTab, setMobileTab] = useState<'problem' | 'code' | 'output'>('problem')
  const [fontSize, setFontSize] = useState(14)
  const [wrap, setWrap] = useState(true)
  const [fullscreen, setFullscreen] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)

  const { data: problem, isLoading, error } = useQuery({
    queryKey: ['coding-problem', problemId],
    queryFn: () => fetchCodingProblem(problemId),
    enabled: Boolean(problemId),
  })

  const { data: navigation } = useQuery({
    queryKey: ['coding-nav', problemId],
    queryFn: () => fetchCodingNavigation(problemId),
    enabled: Boolean(problemId),
  })

  const { data: languages } = useQuery({
    queryKey: ['coding-languages'],
    queryFn: fetchLanguages,
  })

  const { data: executionStatus } = useQuery({
    queryKey: ['coding-execution-status'],
    queryFn: fetchExecutionStatus,
    refetchInterval: 30000,
  })

  const { data: submissions } = useQuery({
    queryKey: ['coding-submissions', problemId],
    queryFn: () => fetchSubmissions({ problem_id: problemId, limit: 20 }),
    enabled: tab === 'submissions',
  })

  const starterForLang =
    problem?.starter_code[String(languageId)] ??
    (problem ? Object.values(problem.starter_code)[0] ?? '' : '')

  const { sourceCode, setSourceCode, resetCode, initialized } = useCodingDraft(
    user?.id,
    problemId,
    languageId,
    starterForLang,
  )

  const executionAvailable =
    problem?.execution_available !== false && executionStatus?.available !== false

  const runMutation = useMutation({
    mutationFn: () => runCode(problemId, sourceCode, languageId),
    onSuccess: (data) => {
      setActionError(null)
      setLastResult(data)
      setMobileTab('output')
    },
    onError: (err) => setActionError(apiErrorMessage(err, 'Could not run code.')),
  })

  const submitMutation = useMutation({
    mutationFn: () => submitCode(problemId, sourceCode, languageId),
    onSuccess: (data) => {
      setActionError(null)
      setLastResult(data)
      setMobileTab('output')
      void queryClient.invalidateQueries({ queryKey: ['coding-progress'] })
      void queryClient.invalidateQueries({ queryKey: ['coding-problem', problemId] })
      void queryClient.invalidateQueries({ queryKey: ['coding-nav', problemId] })
      void queryClient.invalidateQueries({ queryKey: ['coding-submissions', problemId] })
    },
    onError: (err) => setActionError(apiErrorMessage(err, 'Could not submit code.')),
  })

  const bookmarkMutation = useMutation({
    mutationFn: () => toggleCodingBookmark(problemId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['coding-problem', problemId] }),
  })

  const isRunning = runMutation.isPending || submitMutation.isPending
  const sampleCases = useMemo(() => problem?.sample_test_cases ?? [], [problem])
  useWorkspaceShortcuts({
    enabled: Boolean(problem) && executionAvailable && !isRunning,
    run: () => runMutation.mutate(),
    submit: () => submitMutation.mutate(),
  })

  if (isLoading || !initialized) return <LoadingState label="Loading coding problem" />
  if (error || !problem) return <ErrorState message={apiErrorMessage(error, 'Problem not found.')} />

  const langOptions = (languages ?? problem.supported_languages).filter((lang) => lang.available !== false)
  const projectReturn = searchParams.get('fromProject')
  const left = (
    <div className="flex h-full flex-col gap-3">
      <PracticeTabs
        tabs={[
          { id: 'problem', label: 'Problem' },
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
            <div className="whitespace-pre-wrap">{problem.description}</div>
            {problem.input_format && (
              <div>
                <h3 className="font-medium">Input format</h3>
                <p className="mt-1 text-[var(--color-text-muted)]">{problem.input_format}</p>
              </div>
            )}
            {problem.output_format && (
              <div>
                <h3 className="font-medium">Output format</h3>
                <p className="mt-1 text-[var(--color-text-muted)]">{problem.output_format}</p>
              </div>
            )}
            {problem.constraints && (
              <div>
                <h3 className="font-medium">Constraints</h3>
                <p className="mt-1 whitespace-pre-wrap text-[var(--color-text-muted)]">{problem.constraints}</p>
              </div>
            )}
            {sampleCases.length > 0 && (
              <div className="space-y-3">
                <h3 className="font-medium">Sample tests</h3>
                {sampleCases.map((tc) => (
                  <div key={tc.id} className="rounded-md border border-[var(--color-border)] p-3 text-xs">
                    {tc.name && <p className="mb-1 font-medium">{tc.name}</p>}
                    <p>Input: {tc.input}</p>
                    <p>Output: {tc.expected_output}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
        {tab === 'hints' && (
          <HintPanel hints={problem.hints ?? []} revealed={revealedHints} onReveal={() => setRevealedHints((n) => n + 1)} />
        )}
        {tab === 'submissions' && (
          submissions?.items.length ? (
            <div className="space-y-2">
              {submissions.items.map((sub) => (
                <Link
                  key={sub.id}
                  to={`/submissions/${sub.id}`}
                  className="flex items-center justify-between rounded-md border border-[var(--color-border)] px-3 py-2 text-sm"
                >
                  <span className="capitalize">{sub.status.replace(/_/g, ' ')}</span>
                  <Badge>{sub.submission_type}</Badge>
                </Link>
              ))}
            </div>
          ) : (
            <EmptyState title="No submissions yet" />
          )
        )}
        {tab === 'solution' &&
          (problem.solution_unlocked && problem.solution ? (
            <div className="space-y-2 text-sm">
              {problem.solution.explanation && <p className="whitespace-pre-wrap">{problem.solution.explanation}</p>}
              {problem.solution.approach && <p>{problem.solution.approach}</p>}
              {problem.solution.complexity && <p className="text-xs">{problem.solution.complexity}</p>}
              {problem.solution.code && (
                <pre className="overflow-x-auto rounded bg-[var(--color-surface-muted)] p-3 text-xs">
                  {problem.solution.code}
                </pre>
              )}
            </div>
          ) : (
            <EmptyState title="Solution locked" description="Solutions unlock after the problem is solved, when a solution is published." />
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

  return (
    <div className={`flex flex-col gap-3 overflow-hidden ${fullscreen ? 'fixed inset-0 z-40 bg-[var(--color-bg)] p-4' : 'h-[calc(100vh-7rem)]'}`}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <PracticeHeader backTo={projectReturn ? `/projects/${projectReturn}` : '/practice/dsa'} backLabel="Back" title={problem.title}>
          <div className="mt-1 flex flex-wrap gap-2">
            <Badge>{problem.difficulty}</Badge>
            <PracticeStatusBadge status={problem.progress_status} />
          </div>
        </PracticeHeader>
        <div className="flex flex-wrap items-center gap-2">
          {navigation?.previous && (
            <Link to={navigation.previous.href}>
              <Button variant="ghost" size="sm">Previous</Button>
            </Link>
          )}
          {navigation?.next && (
            <Link to={navigation.next.href}>
              <Button variant="ghost" size="sm">Next</Button>
            </Link>
          )}
          <Button variant="ghost" size="sm" onClick={() => bookmarkMutation.mutate()} aria-label="Bookmark problem">
            <Bookmark className="h-4 w-4" />
            {problem.bookmarked ? 'Bookmarked' : 'Bookmark'}
          </Button>
          <select
            aria-label="Language"
            value={languageId}
            onChange={(e) => setLanguageId(Number(e.target.value))}
            className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1.5 text-sm"
          >
            {langOptions.map((lang) => (
              <option key={lang.id} value={lang.id}>
                {lang.name}
              </option>
            ))}
          </select>
          <label className="text-xs text-[var(--color-text-muted)]">
            Font
            <input
              aria-label="Editor font size"
              type="number"
              min={12}
              max={22}
              value={fontSize}
              onChange={(e) => setFontSize(Number(e.target.value))}
              className="ml-1 w-14 rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-1"
            />
          </label>
          <Button variant="ghost" size="sm" onClick={() => setWrap((v) => !v)}>
            {wrap ? 'Unwrap' : 'Wrap'}
          </Button>
          <Button variant="ghost" size="sm" onClick={() => setFullscreen((v) => !v)}>
            {fullscreen ? 'Exit full screen' : 'Full screen'}
          </Button>
          <Button
            variant="secondary"
            onClick={() => {
              if (sourceCode !== starterForLang && !window.confirm('Reset editor to starter code?')) return
              resetCode()
            }}
          >
            Reset
          </Button>
          <Button variant="secondary" disabled={!executionAvailable || isRunning} onClick={() => runMutation.mutate()}>
            {runMutation.isPending ? 'Running...' : 'Run'}
          </Button>
          <Button variant="primary" disabled={!executionAvailable || isRunning} onClick={() => submitMutation.mutate()}>
            {submitMutation.isPending ? 'Submitting...' : 'Submit'}
          </Button>
        </div>
      </div>
      {!executionAvailable && (
        <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-100">
          Code execution is temporarily unavailable. You can still solve the problem in the editor, save your draft,
          review samples, hints, and submissions.
        </div>
      )}
      {actionError && <ErrorState message={actionError} />}
      <WorkspaceSplit
        storageKey="dsa-split"
        left={left}
        right={
          <Card className="h-full min-h-[240px] overflow-hidden p-0">
            <CodeEditor
              value={sourceCode}
              language={getMonacoLanguage(languageId)}
              onChange={setSourceCode}
              height="100%"
              fontSize={fontSize}
              wordWrap={wrap ? 'on' : 'off'}
            />
          </Card>
        }
        bottom={
          <Card padding="md" className="h-full overflow-auto">
            <h3 className="mb-2 text-sm font-medium">Execution output</h3>
            {lastResult ? (
              <>
                {lastResult.status === 'accepted' && (
                  <SuccessState title="Accepted">
                    {lastResult.passed_tests}/{lastResult.total_tests} tests ·{' '}
                    {lastResult.execution_time_ms != null ? `${lastResult.execution_time_ms.toFixed(0)} ms` : ''}
                  </SuccessState>
                )}
                <ExecutionResults
                  results={lastResult.results}
                  passedTests={lastResult.passed_tests}
                  totalTests={lastResult.total_tests}
                  status={lastResult.status}
                />
              </>
            ) : (
              <EmptyState
                title={executionAvailable ? 'No output yet' : 'Execution unavailable'}
                description={
                  executionAvailable
                    ? 'Run sample tests or submit when ready.'
                    : 'Results will appear here after an execution provider is enabled.'
                }
              />
            )}
          </Card>
        }
        mobileTab={mobileTab}
        onMobileTab={setMobileTab}
      />
    </div>
  )
}
