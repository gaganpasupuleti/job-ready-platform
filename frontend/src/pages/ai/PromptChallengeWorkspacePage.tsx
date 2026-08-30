import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
import {
  apiErrorMessage,
  ErrorState,
  HintPanel,
  LoadingState,
  PracticeProgress,
  PracticeStatusBadge,
  useWorkspaceShortcuts,
} from '@/components/practice-workspace/PracticeWorkspace'
import { useAuth } from '@/hooks/useAuth'
import {
  fetchPromptChallenge,
  fetchPromptChallenges,
  submitPrompt,
  testPrompt,
  togglePromptBookmark,
  type PromptEvaluateResponse,
} from '@/services/aiService'

function draftKey(userId: string, challengeId: string) {
  return `prompt-draft:${userId}:${challengeId}`
}

export function PromptChallengeWorkspacePage() {
  const { slug = '' } = useParams()
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const { data, isLoading } = useQuery({
    queryKey: ['prompt-challenge', slug],
    queryFn: () => fetchPromptChallenge(slug),
    enabled: Boolean(slug),
  })
  const [revealedHints, setRevealedHints] = useState(0)
  const [prompt, setPrompt] = useState('')
  const [result, setResult] = useState<PromptEvaluateResponse | null>(null)
  const { data: siblings } = useQuery({
    queryKey: ['prompt-challenges'],
    queryFn: () => fetchPromptChallenges(),
  })

  useEffect(() => {
    if (!data || !user) return
    const saved = localStorage.getItem(draftKey(user.id, data.id))
    setPrompt(saved ?? data.starter_prompt ?? '')
  }, [data, user])

  useEffect(() => {
    if (!data || !user) return
    localStorage.setItem(draftKey(user.id, data.id), prompt)
  }, [prompt, data, user])

  const preview = useMemo(() => {
    const vars = data?.public_cases[0]?.variables ?? {}
    let rendered = prompt
    Object.entries(vars).forEach(([key, value]) => {
      rendered = rendered.replaceAll(`{{${key}}}`, String(value))
    })
    return rendered
  }, [prompt, data])

  const testMutation = useMutation({
    mutationFn: () => testPrompt(slug, prompt),
    onSuccess: setResult,
  })
  const submitMutation = useMutation({
    mutationFn: () => submitPrompt(slug, prompt),
    onSuccess: (body) => {
      setResult(body)
      queryClient.invalidateQueries({ queryKey: ['prompt-challenge', slug] })
    },
  })
  useWorkspaceShortcuts({
    enabled: Boolean(data) && !testMutation.isPending && !submitMutation.isPending,
    run: () => testMutation.mutate(),
    submit: () => submitMutation.mutate(),
  })
  const bookmarkMutation = useMutation({
    mutationFn: () => togglePromptBookmark(data!.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['prompt-challenge', slug] }),
  })

  if (isLoading || !data) {
    return <LoadingState label="Loading prompt challenge" />
  }
  const nextChallenge = (Array.isArray(siblings) ? siblings : []).find(
    (_item, index, arr) => arr[index - 1]?.slug === data.slug,
  )

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-lg font-semibold text-[var(--color-text)]">{data.title}</h2>
          <div className="mt-2 max-w-sm">
            <PracticeProgress
              percent={Math.min(100, Math.round((data.best_score / Math.max(data.mastery_threshold, 1)) * 100))}
              label={`Best ${data.best_score} / mastery ${data.mastery_threshold}`}
            />
          </div>
          <div className="mt-1 flex gap-2">
            <Badge>{data.difficulty}</Badge>
            <Badge>{data.task_type}</Badge>
            <PracticeStatusBadge status={data.status} />
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => bookmarkMutation.mutate()}>
            {data.bookmarked ? 'Bookmarked' : 'Bookmark'}
          </Button>
          <Link to="/ai/prompt-engineering/challenges" className="text-sm text-[var(--color-accent)] hover:underline">
            All challenges
          </Link>
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <div className="space-y-3">
          <Card>
            <CardHeader title="Challenge" />
            <p className="text-sm text-[var(--color-text)]">{data.scenario}</p>
          </Card>
          <Card>
            <CardHeader title="Requirements" />
            <p className="whitespace-pre-wrap text-sm text-[var(--color-text)]">{data.instructions}</p>
            <p className="mt-2 text-xs text-[var(--color-text-muted)]">{data.input_description}</p>
            <p className="mt-2 text-xs text-[var(--color-text-muted)]">{data.expected_behavior}</p>
          </Card>
          <Card>
            <CardHeader title="Public examples" />
            {data.public_cases.map((item, index) => (
              <pre key={item.id} className="mb-2 overflow-x-auto rounded bg-[var(--color-surface-muted)] p-2 text-xs">
                Case {index + 1}: {JSON.stringify(item.variables)}
                {item.input_text ? `\n${item.input_text}` : ''}
              </pre>
            ))}
            <p className="text-xs text-[var(--color-text-subtle)]">{data.hidden_case_count} hidden case(s) on submit.</p>
          </Card>
          <Card>
            <CardHeader title="Evaluation" />
            <p className="text-sm">{data.evaluation_criteria_summary}</p>
            {data.hints.length > 0 && (
              <HintPanel hints={data.hints} revealed={revealedHints} onReveal={() => setRevealedHints((n) => n + 1)} />
            )}
            {data.common_mistakes.length > 0 && (
              <p className="mt-2 text-xs text-[var(--color-text-muted)]">
                Common mistakes: {data.common_mistakes.join('; ')}
              </p>
            )}
          </Card>
        </div>

        <div className="space-y-3">
          <Card>
            <CardHeader title="Prompt editor" />
            <textarea
              className="min-h-[220px] w-full rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] p-3 text-sm"
              value={prompt}
              maxLength={data.max_prompt_length}
              onChange={(e) => setPrompt(e.target.value)}
            />
            <p className="mt-1 text-xs text-[var(--color-text-subtle)]">
              {prompt.length} / {data.max_prompt_length} · drafts saved locally
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              <Button onClick={() => testMutation.mutate()} disabled={testMutation.isPending}>
                {testMutation.isPending ? 'Testing...' : 'Test Prompt'}
              </Button>
              <Button variant="primary" onClick={() => submitMutation.mutate()} disabled={submitMutation.isPending}>
                {submitMutation.isPending ? 'Submitting...' : 'Submit Prompt'}
              </Button>
              <Button variant="secondary" onClick={() => setPrompt(data.starter_prompt ?? '')}>
                Reset
              </Button>
              <Button variant="secondary" onClick={() => user && data && localStorage.setItem(draftKey(user.id, data.id), prompt)}>
                Save Draft
              </Button>
            </div>
          </Card>
          <Card>
            <CardHeader title="Variables / context preview" />
            <pre className="overflow-x-auto whitespace-pre-wrap text-xs text-[var(--color-text-muted)]">{preview}</pre>
          </Card>
        </div>
      </div>

      {result && (
        <Card>
          <CardHeader title={result.is_test ? 'Public test results' : 'Submission results'} />
          <p className="text-sm">
            Score {result.overall_score} · passed {result.passed_cases}/{result.total_cases}
            {result.mastered ? ' · Mastered' : ''}
          </p>
          <p className="mt-1 text-xs text-[var(--color-text-muted)]">{result.feedback}</p>
          <div className="mt-3 grid gap-2 sm:grid-cols-3">
            {Object.entries(result.rubric_breakdown).map(([key, value]) => (
              <div key={key} className="rounded border border-[var(--color-border)] px-2 py-1 text-xs">
                {key}: {value}
              </div>
            ))}
          </div>
          <div className="mt-3 space-y-2">
            {result.case_results.map((row, index) => (
              <div key={row.case_id} className="rounded border border-[var(--color-border)] p-2 text-sm">
                <span className={row.passed ? 'text-green-600' : 'text-red-600'}>
                  {row.revealed ? `Case ${index + 1}` : 'Hidden case'} {row.passed ? 'passed' : 'failed'}
                </span>
                <p className="text-xs text-[var(--color-text-muted)]">{row.feedback}</p>
              </div>
            ))}
          </div>
          {(testMutation.isError || submitMutation.isError) && (
            <ErrorState
              message={apiErrorMessage(testMutation.error || submitMutation.error, 'Prompt evaluation failed.')}
            />
          )}
          {nextChallenge && (
            <Link to={`/ai/prompt-engineering/challenges/${nextChallenge.slug}`} className="mt-2 inline-block text-sm">
              Next Challenge
            </Link>
          )}
          {result.submission_id && !result.is_test && (
            <Link
              to={`/ai/prompt-engineering/submissions/${result.submission_id}`}
              className="mt-2 inline-block text-sm text-[var(--color-accent)] hover:underline"
            >
              Open submission
            </Link>
          )}
        </Card>
      )}
    </div>
  )
}
