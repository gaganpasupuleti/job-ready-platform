import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
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
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-[var(--color-text)]">Practice Complete</h2>
        <p className="text-sm text-[var(--color-text-muted)]">Review your performance below.</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card padding="sm">
          <p className="text-xs text-[var(--color-text-muted)]">Score</p>
          <p className="text-2xl font-semibold">
            {data.session.correct_count} / {data.session.question_count}
          </p>
        </Card>
        <Card padding="sm">
          <p className="text-xs text-[var(--color-text-muted)]">Accuracy</p>
          <p className="text-2xl font-semibold">{formatPercent(data.accuracy)}</p>
        </Card>
        <Card padding="sm">
          <p className="text-xs text-[var(--color-text-muted)]">Incorrect</p>
          <p className="text-2xl font-semibold">{data.session.incorrect_count}</p>
        </Card>
        <Card padding="sm">
          <p className="text-xs text-[var(--color-text-muted)]">Time Taken</p>
          <p className="text-2xl font-semibold">{formatDuration(data.time_taken_seconds)}</p>
        </Card>
      </div>

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
              <p className="text-sm text-[var(--color-text)]">{item.question_text}</p>
              <p className="mt-2 text-xs text-[var(--color-text-muted)]">
                Your answer: {item.selected_option_texts.join(', ') || 'Not answered'}
              </p>
              <p className="text-xs text-[var(--color-text-muted)]">
                Correct answer: {item.correct_option_texts.join(', ')}
              </p>
              {item.explanation && (
                <p className="mt-2 text-xs text-[var(--color-text-subtle)]">{item.explanation}</p>
              )}
            </div>
          ))}
        </div>
      </Card>

      <Link to="/">
        <Button variant="secondary">Back to Dashboard</Button>
      </Link>
    </div>
  )
}
