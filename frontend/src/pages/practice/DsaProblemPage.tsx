import { useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Bookmark } from 'lucide-react'

import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { Card } from '@/components/common/Card'
import { getMonacoLanguage } from '@/constants/languages'
import { CodeEditor } from '@/features/dsa/CodeEditor'
import { ExecutionResults } from '@/features/dsa/ExecutionResults'
import { useAuth } from '@/hooks/useAuth'
import { useCodingDraft } from '@/hooks/useCodingDraft'
import {
  fetchCodingProblem,
  fetchExecutionStatus,
  fetchLanguages,
  fetchSubmissions,
  runCode,
  submitCode,
  toggleCodingBookmark,
} from '@/services/codingService'
import type { ExecutionResponse } from '@/types/coding'

type Tab = 'problem' | 'submissions'

export function DsaProblemPage() {
  const { problemId = '' } = useParams()
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [tab, setTab] = useState<Tab>('problem')
  const [languageId, setLanguageId] = useState(71)
  const [lastResult, setLastResult] = useState<ExecutionResponse | null>(null)

  const { data: problem, isLoading } = useQuery({
    queryKey: ['coding-problem', problemId],
    queryFn: () => fetchCodingProblem(problemId),
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
    onSuccess: (data) => setLastResult(data),
  })

  const submitMutation = useMutation({
    mutationFn: () => submitCode(problemId, sourceCode, languageId),
    onSuccess: (data) => {
      setLastResult(data)
      queryClient.invalidateQueries({ queryKey: ['coding-progress'] })
      queryClient.invalidateQueries({ queryKey: ['coding-problem', problemId] })
      queryClient.invalidateQueries({ queryKey: ['coding-submissions', problemId] })
    },
  })

  const bookmarkMutation = useMutation({
    mutationFn: () => toggleCodingBookmark(problemId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['coding-problem', problemId] }),
  })

  const isRunning = runMutation.isPending || submitMutation.isPending
  const sampleCases = useMemo(() => problem?.sample_test_cases ?? [], [problem])

  if (isLoading || !problem || !initialized) {
    return <p className="text-sm text-[var(--color-text-muted)]">Loading problem...</p>
  }

  const langOptions = languages ?? problem.supported_languages

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Link to="/practice/dsa" className="text-xs text-[var(--color-accent)] hover:underline">
            ← Back to problems
          </Link>
          <h2 className="text-lg font-semibold text-[var(--color-text)]">{problem.title}</h2>
          <div className="mt-1 flex flex-wrap gap-2">
            <Badge>{problem.difficulty}</Badge>
            {problem.progress_status && <Badge variant="success">{problem.progress_status}</Badge>}
            {(problem.tags ?? []).map((t) => (
              <Badge key={t}>{t}</Badge>
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
          <select
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
          <Button variant="secondary" onClick={resetCode}>
            Reset Code
          </Button>
          <Button
            variant="secondary"
            disabled={!executionAvailable || isRunning}
            onClick={() => runMutation.mutate()}
          >
            {runMutation.isPending ? 'Running...' : 'Run'}
          </Button>
          <Button
            variant="primary"
            disabled={!executionAvailable || isRunning}
            onClick={() => submitMutation.mutate()}
          >
            {submitMutation.isPending ? 'Submitting...' : 'Submit'}
          </Button>
        </div>
      </div>

      {!executionAvailable && (
        <div className="rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-100">
          Code execution is currently unavailable. You can still read the problem, edit code, and
          review samples.
        </div>
      )}

      <div className="flex gap-2 border-b border-[var(--color-border)]">
        {(['problem', 'submissions'] as Tab[]).map((key) => (
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

      {tab === 'submissions' ? (
        <Card padding="md" className="overflow-y-auto">
          <h3 className="mb-3 text-sm font-medium">Your submissions</h3>
          {submissions?.items.length ? (
            <div className="space-y-2">
              {submissions.items.map((sub) => (
                <Link
                  key={sub.id}
                  to={`/submissions/${sub.id}`}
                  className="flex items-center justify-between rounded-md border border-[var(--color-border)] px-3 py-2 text-sm hover:bg-[var(--color-surface-muted)]"
                >
                  <div>
                    <p className="font-medium capitalize">{sub.status.replace(/_/g, ' ')}</p>
                    <p className="text-xs text-[var(--color-text-muted)]">
                      {sub.language_name} · {sub.passed_tests}/{sub.total_tests} ·{' '}
                      {new Date(sub.created_at).toLocaleString()}
                    </p>
                  </div>
                  <Badge>{sub.submission_type}</Badge>
                </Link>
              ))}
            </div>
          ) : (
            <p className="text-sm text-[var(--color-text-muted)]">No submissions yet.</p>
          )}
        </Card>
      ) : (
        <div className="grid min-h-0 flex-1 gap-4 lg:grid-cols-2">
          <Card className="overflow-y-auto" padding="md">
            <div className="whitespace-pre-wrap text-sm text-[var(--color-text)]">
              {problem.description}
            </div>
            {problem.input_format && (
              <div className="mt-4">
                <h4 className="text-sm font-medium">Input format</h4>
                <p className="mt-1 text-sm text-[var(--color-text-muted)]">{problem.input_format}</p>
              </div>
            )}
            {problem.output_format && (
              <div className="mt-4">
                <h4 className="text-sm font-medium">Output format</h4>
                <p className="mt-1 text-sm text-[var(--color-text-muted)]">
                  {problem.output_format}
                </p>
              </div>
            )}
            {problem.constraints && (
              <div className="mt-4">
                <h4 className="text-sm font-medium">Constraints</h4>
                <p className="mt-1 whitespace-pre-wrap text-sm text-[var(--color-text-muted)]">
                  {problem.constraints}
                </p>
              </div>
            )}
            {sampleCases.length > 0 && (
              <div className="mt-4 space-y-3">
                <h4 className="text-sm font-medium">Sample test cases</h4>
                {sampleCases.map((tc) => (
                  <div
                    key={tc.id}
                    className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface-muted)] p-3 text-xs"
                  >
                    {tc.name && <p className="mb-1 font-medium">{tc.name}</p>}
                    <p>
                      <span className="text-[var(--color-text-subtle)]">Input: </span>
                      {tc.input}
                    </p>
                    <p>
                      <span className="text-[var(--color-text-subtle)]">Output: </span>
                      {tc.expected_output}
                    </p>
                  </div>
                ))}
              </div>
            )}
            {lastResult && (
              <div className="mt-6 border-t border-[var(--color-border)] pt-4">
                <h4 className="mb-3 text-sm font-medium">Results</h4>
                <ExecutionResults
                  results={lastResult.results}
                  passedTests={lastResult.passed_tests}
                  totalTests={lastResult.total_tests}
                  status={lastResult.status}
                />
              </div>
            )}
          </Card>
          <Card className="min-h-[320px] overflow-hidden p-0">
            <CodeEditor
              value={sourceCode}
              language={getMonacoLanguage(languageId)}
              onChange={setSourceCode}
              height="100%"
            />
          </Card>
        </div>
      )}
    </div>
  )
}
