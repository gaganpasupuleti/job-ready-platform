import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { Button } from '@/components/common/Button'
import { Card } from '@/components/common/Card'
import { CatalogMetrics } from '@/components/practice/CatalogMetrics'
import { ErrorState, LoadingState } from '@/components/practice-workspace/PracticeWorkspace'
import { useAuth } from '@/hooks/useAuth'
import {
  knownCount,
  mistakeAction,
  reviewTopicLabel,
  showGlobalWeakTopics,
  sourceTypeLabel,
  statusLabelText,
} from '@/lib/studentLabels'
import {
  fetchMistakeSummary,
  fetchMistakes,
  markMistakeReviewed,
  resolveMistake,
} from '@/services/mistakeService'

const FILTERS = ['all', 'mcq', 'sql', 'coding', 'prompt', 'scenario', 'interview'] as const

export function MistakesPage() {
  const { user } = useAuth()
  const uid = user?.id
  const [sourceFilter, setSourceFilter] = useState<string>('all')
  const [view, setView] = useState('recent')
  const queryClient = useQueryClient()

  const { data: summary, isError: summaryError, isPending: summaryPending } = useQuery({
    queryKey: ['mistakes-summary', uid],
    queryFn: fetchMistakeSummary,
    enabled: Boolean(uid),
  })
  const { data, isLoading, error } = useQuery({
    queryKey: ['mistakes', uid, sourceFilter, view],
    queryFn: () =>
      fetchMistakes({
        source_type: sourceFilter === 'all' ? undefined : sourceFilter,
        view,
      }),
    enabled: Boolean(uid),
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

      {summaryPending ? (
        <p className="text-sm text-[var(--color-text-muted)]">Loading review totals.</p>
      ) : summaryError ? (
        <p className="text-sm text-[var(--color-danger)]" role="alert">
          Review totals could not be loaded.
        </p>
      ) : summary ? (
        <div className="space-y-2">
          <CatalogMetrics
            metrics={[
              { label: 'Open', value: knownCount(summary.open_count) },
              { label: 'Repeated', value: knownCount(summary.repeated_count) },
              { label: 'Resolved', value: knownCount(summary.resolved_count) },
            ]}
          />
          {showGlobalWeakTopics(sourceFilter) ? (
            <p className="text-sm text-[var(--color-text-muted)]" role="status">
              Across all subjects:{' '}
              {summary.top_weak_topics[0]?.title
                ? `${summary.top_weak_topics[0].title} · ${knownCount(summary.top_weak_topics[0].count)} misses`
                : 'no weak topic listed'}
            </p>
          ) : (
            <p className="text-sm text-[var(--color-text-muted)]" role="status">
              This list is only {sourceTypeLabel(sourceFilter)}. Weak topics from other subjects stay hidden.
            </p>
          )}
        </div>
      ) : null}

      <div className="flex flex-wrap gap-2">
        {(['recent', 'repeated', 'unresolved', 'resolved'] as const).map((v) => (
          <Button
            key={v}
            size="sm"
            variant={view === v ? 'primary' : 'secondary'}
            onClick={() => setView(v)}
          >
            {statusLabelText(v)}
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
                ? 'bg-[var(--color-accent)] text-[var(--color-surface)]'
                : 'border border-[var(--color-border)] text-[var(--color-text-muted)]'
            }`}
            onClick={() => setSourceFilter(f)}
          >
            {sourceTypeLabel(f)}
          </button>
        ))}
      </div>

      <div className="space-y-3">
        {(data ?? []).length === 0 ? (
          <Card>
            <p className="text-sm text-[var(--color-text-muted)]">No mistakes in this view yet.</p>
          </Card>
        ) : (
          data!.map((item) => {
            const action = mistakeAction(item.retry_href)
            return (
            <Card key={item.id}>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-xs text-[var(--color-text-subtle)]">{sourceTypeLabel(item.source_type)}</p>
                  <p className="font-medium text-[var(--color-text)]">{reviewTopicLabel(item)}</p>
                  {item.title && item.title !== reviewTopicLabel(item) ? (
                    <p className="mt-1 text-sm text-[var(--color-text-muted)]">{item.title}</p>
                  ) : null}
                  {item.summary && (
                    <p className="mt-1 text-sm text-[var(--color-text-muted)]">{item.summary}</p>
                  )}
                  <p className="mt-1 text-xs text-[var(--color-text-subtle)]">
                    {item.occurrence_count} occurrence{item.occurrence_count !== 1 ? 's' : ''} ·{' '}
                    {statusLabelText(item.status)}
                  </p>
                  {action?.note && (
                    <p className="mt-1 text-xs text-[var(--color-text-muted)]">{action.note}</p>
                  )}
                </div>
                <div className="flex flex-wrap gap-2">
                  {action && (
                    <Link to={action.href}>
                      <Button size="sm" variant="secondary">
                        {action.label}
                      </Button>
                    </Link>
                  )}
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
            )
          })
        )}
      </div>
    </div>
  )
}

