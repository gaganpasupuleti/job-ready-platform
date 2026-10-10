import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
import { CatalogMetrics } from '@/components/practice/CatalogMetrics'
import { StructuredExplanation } from '@/features/practice/StructuredExplanation'
import { fetchResults } from '@/services/practiceService'
import { formatPercent } from '@/utils/cn'

function formatDuration(seconds: number) {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
}

export function PracticeResultsPage() {
  const { sessionId = '' } = useParams()
  const { data, isLoading, error } = useQuery({
    queryKey: ['practice-results', sessionId],
    queryFn: () => fetchResults(sessionId),
    enabled: Boolean(sessionId),
  })

  if (isLoading) return <p className="text-sm text-[var(--color-text-muted)]">Loading results...</p>
  if (error || !data) {
    return <p className="text-sm text-[var(--color-danger)]">Unable to load results.</p>
  }

  return (
    <div className="mx-auto max-w-4xl space-y-4">
      <div>
        <h1 className="text-base font-semibold text-[var(--color-text)] sm:text-lg">Practice Complete</h1>
        <p className="mt-0.5 text-sm text-[var(--color-text-muted)]">Review your performance below.</p>
      </div>

      <CatalogMetrics
        metrics={[
          { label: 'Score', value: `${data.session.correct_count}/${data.session.question_count}` },
          { label: 'Accuracy', value: formatPercent(data.accuracy) },
          { label: 'Incorrect', value: String(data.session.incorrect_count) },
          { label: 'Unanswered', value: String(data.session.unanswered_count) },
          { label: 'Time', value: formatDuration(data.time_taken_seconds) },
        ]}
      />

      {data.topic_performance.length > 0 && (
        <Card>
          <CardHeader title="Topic Performance" />
          <div className="space-y-3">
            {data.topic_performance.map((topic) => (
              <div key={topic.topic_name}>
                <div className="mb-1 flex justify-between text-sm">
                  <span>{topic.topic_name}</span>
                  <span>{formatPercent(topic.accuracy)}</span>
                </div>
                <div className="h-1.5 rounded-full bg-[var(--color-surface-muted)]">
                  <div
                    className="h-full rounded-full bg-[var(--color-accent)]"
                    style={{ width: `${topic.accuracy}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      <Card>
        <CardHeader title="Review Questions" />
        <div className="space-y-4">
          {data.questions.map((item) => (
            <div
              key={item.question_number}
              className="rounded-md border border-[var(--color-border)] p-4"
            >
              <div className="mb-2 flex items-center gap-2">
                <Badge>Q{item.question_number}</Badge>
                <Badge variant={item.is_correct ? 'success' : 'warning'}>
                  {item.is_correct ? 'Correct' : 'Incorrect'}
                </Badge>
              </div>
              <div className="reading-shell">
                <p className="text-[var(--color-text)]">{item.question_text}</p>
                <p className="mt-2 text-sm text-[var(--color-text-muted)]">
                  Your answer: {item.selected_option_texts.join(', ') || 'Not answered'}
                </p>
                <p className="text-sm text-[var(--color-text-muted)]">
                  Correct answer: {item.correct_option_texts.join(', ')}
                </p>
                {item.explanation && (
                  <div className="mt-3">
                    <StructuredExplanation
                      text={item.explanation}
                      className="whitespace-pre-wrap text-sm text-[var(--color-text)]"
                    />
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </Card>

      <p className="text-sm text-[var(--color-text-muted)]" role="status">
        A new retry session is not available. This page is the saved result.
      </p>
      <div className="flex flex-wrap gap-3 text-sm">
        <Link to="/practice/mcq" className="text-[var(--color-accent)] hover:underline">
          Back to Technical MCQs
        </Link>
        <Link to="/practice/aptitude" className="text-[var(--color-accent)] hover:underline">
          Back to Aptitude
        </Link>
        <Link to="/mistakes">
          <Button variant="secondary">Mistake book</Button>
        </Link>
      </div>
    </div>
  )
}
