import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { Button } from '@/components/common/Button'
import { Card } from '@/components/common/Card'
import { ErrorState, LoadingState } from '@/components/practice-workspace/PracticeWorkspace'
import {
  fetchMistakeSummary,
  fetchMistakes,
  markMistakeReviewed,
  resolveMistake,
  startRetrySession,
} from '@/services/mistakeService'

const FILTERS = ['all', 'mcq', 'sql', 'coding', 'prompt', 'scenario', 'interview'] as const

export function MistakesPage() {
  const [sourceFilter, setSourceFilter] = useState<string>('all')
  const [view, setView] = useState('recent')
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: summary } = useQuery({ queryKey: ['mistakes-summary'], queryFn: fetchMistakeSummary })
  const { data, isLoading, error } = useQuery({
    queryKey: ['mistakes', sourceFilter, view],
    queryFn: () =>
      fetchMistakes({
        source_type: sourceFilter === 'all' ? undefined : sourceFilter,
        view,
      }),
  })

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['mistakes'] })
    queryClient.invalidateQueries({ queryKey: ['mistakes-summary'] })
  }

  const reviewMutation = useMutation({
    mutationFn: markMistakeReviewed,
    onSuccess: invalidate,
  })
  const resolveMutation = useMutation({
    mutationFn: resolveMistake,
    onSuccess: invalidate,
  })
  const retryMutation = useMutation({
    mutationFn: (questionIds: string[]) => startRetrySession(questionIds),
    onSuccess: (session) => navigate(`/practice/sessions/${session.id}`),
  })

  const mcqIds = (data ?? [])
    .filter((item) => item.source_type === 'mcq' && item.status !== 'resolved' && item.source_id)
    .map((item) => item.source_id)
    .slice(0, 50)

  if (isLoading) return <LoadingState label="Loading mistake book" />
  if (error) return <ErrorState message="Could not load mistakes." />

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-[var(--color-text)]">Mistake Book</h1>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          Review incorrect answers and practice gaps. Interview self-reviews marked Needs Review appear
          here — they are not factual mistakes.
        </p>
      </div>

      {summary && (
        <div className="grid gap-3 sm:grid-cols-4">
          <Stat label="Open" value={summary.open_count} />
          <Stat label="Repeated" value={summary.repeated_count} />
          <Stat label="Resolved" value={summary.resolved_count} />
          <Stat
            label="Top weak topic"
            value={summary.top_weak_topics[0]?.title ?? '—'}
            sub={summary.top_weak_topics[0] ? `${summary.top_weak_topics[0].count} misses` : undefined}
          />
        </div>
      )}

      {mcqIds.length > 0 ? (
        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="primary"
            size="sm"
            onClick={() => retryMutation.mutate([...new Set(mcqIds)])}
            disabled={retryMutation.isPending}
          >
            Retry incorrect ({new Set(mcqIds).size})
          </Button>
          {retryMutation.isError ? (
            <p className="text-sm text-[var(--color-danger)]">Could not start a retry session.</p>
          ) : null}
        </div>
      ) : null}

      <div className="flex flex-wrap gap-2">
        {['recent', 'repeated', 'unresolved', 'resolved'].map((v) => (
          <Button
            key={v}
            size="sm"
            variant={view === v ? 'primary' : 'secondary'}
            onClick={() => setView(v)}
          >
            {v}
          </Button>
        ))}
      </div>

      <div className="flex flex-wrap gap-2">
        {FILTERS.map((f) => (
          <button
            key={f}
            type="button"
            className={`rounded-full px-3 py-1 text-xs capitalize ${
              sourceFilter === f
                ? 'bg-[var(--color-accent)] text-white'
                : 'border border-[var(--color-border)] text-[var(--color-text-muted)]'
            }`}
            onClick={() => setSourceFilter(f)}
          >
            {f}
          </button>
        ))}
      </div>

      <div className="space-y-3">
        {(data ?? []).length === 0 ? (
          <Card>
            <p className="text-sm text-[var(--color-text-muted)]">No mistakes in this view yet.</p>
          </Card>
        ) : (
          data!.map((item) => (
            <Card key={item.id}>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-xs uppercase text-[var(--color-text-subtle)]">{item.source_type}</p>
                  <p className="font-medium text-[var(--color-text)]">{item.title}</p>
                  {item.summary && (
                    <p className="mt-1 text-sm text-[var(--color-text-muted)]">{item.summary}</p>
                  )}
                  <p className="mt-1 text-xs text-[var(--color-text-subtle)]">
                    {item.occurrence_count} occurrence{item.occurrence_count !== 1 ? 's' : ''} ·{' '}
                    {item.status}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  {item.source_type === 'mcq' && item.status !== 'resolved' ? (
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => retryMutation.mutate([item.source_id])}
                      disabled={retryMutation.isPending}
                    >
                      Retry incorrect
                    </Button>
                  ) : item.retry_href ? (
                    <Link to={item.retry_href}>
                      <Button size="sm" variant="secondary">
                        Retry
                      </Button>
                    </Link>
                  ) : null}
                  {item.status !== 'reviewed' && item.status !== 'resolved' && (
                    <Button size="sm" variant="secondary" onClick={() => reviewMutation.mutate(item.id)}>
                      Mark Reviewed
                    </Button>
                  )}
                  {item.status !== 'resolved' && (
                    <Button size="sm" onClick={() => resolveMutation.mutate(item.id)}>
                      Resolve
                    </Button>
                  )}
                </div>
              </div>
            </Card>
          ))
        )}
      </div>
    </div>
  )
}

function Stat({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <Card>
      <p className="text-xs text-[var(--color-text-muted)]">{label}</p>
      <p className="text-xl font-semibold text-[var(--color-text)]">{value}</p>
      {sub && <p className="text-xs text-[var(--color-text-subtle)]">{sub}</p>}
    </Card>
  )
}
