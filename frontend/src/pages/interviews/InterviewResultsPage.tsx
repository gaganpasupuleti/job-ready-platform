import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
import {
  ErrorState,
  LoadingState,
  PracticeHeader,
} from '@/components/practice-workspace/PracticeWorkspace'
import { InterviewModeBadge } from '@/features/interviews/InterviewSessionRow'
import { fetchInterviewResults } from '@/services/interviewService'

export function InterviewResultsPage() {
  const { sessionId = '' } = useParams()
  const { data, isLoading, error } = useQuery({
    queryKey: ['interview-results', sessionId],
    queryFn: () => fetchInterviewResults(sessionId),
    enabled: Boolean(sessionId),
  })

  if (isLoading) return <LoadingState label="Loading results" />
  if (error || !data) return <ErrorState message="Unable to load session results." />

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <PracticeHeader backTo="/interviews" backLabel="Interview hub" title={data.label || 'Self-Review Summary'}>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          This is a self-review summary — not an interview score or readiness grade.
        </p>
        <div className="mt-2">
          <InterviewModeBadge mode={data.session.mode} />
        </div>
      </PracticeHeader>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card padding="sm">
          <p className="text-xs text-[var(--color-text-muted)]">Reviewed</p>
          <p className="text-2xl font-semibold text-[var(--color-text)]">
            {data.reviewed_count}/{data.questions_total}
          </p>
        </Card>
        <Card padding="sm">
          <p className="text-xs text-[var(--color-text-muted)]">Needs review</p>
          <p className="text-2xl font-semibold text-[var(--color-text)]">{data.needs_review_count}</p>
        </Card>
        <Card padding="sm">
          <p className="text-xs text-[var(--color-text-muted)]">Strong / Good</p>
          <p className="text-2xl font-semibold text-[var(--color-text)]">
            {data.strong + data.good}
          </p>
        </Card>
        <Card padding="sm">
          <p className="text-xs text-[var(--color-text-muted)]">Key-point coverage</p>
          <p className="text-2xl font-semibold text-[var(--color-text)]">
            {data.key_point_coverage_avg != null
              ? `${Math.round(data.key_point_coverage_avg * 100)}%`
              : '—'}
          </p>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader title="Self-ratings" />
          <ul className="space-y-1 text-sm text-[var(--color-text)]">
            <li>Strong: {data.strong}</li>
            <li>Good: {data.good}</li>
            <li>Partial: {data.partial}</li>
            <li>Needs review: {data.needs_review_rating}</li>
          </ul>
        </Card>
        <Card>
          <CardHeader title="Confidence" />
          {Object.keys(data.confidence_breakdown).length ? (
            <ul className="space-y-1 text-sm text-[var(--color-text)]">
              {Object.entries(data.confidence_breakdown).map(([level, count]) => (
                <li key={level}>
                  {level}: {count}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-[var(--color-text-muted)]">No confidence data yet.</p>
          )}
        </Card>
      </div>

      {data.skill_breakdown.length > 0 && (
        <Card>
          <CardHeader title="By skill" />
          <div className="space-y-2 text-sm">
            {data.skill_breakdown.map((row) => (
              <div key={row.skill} className="flex justify-between gap-2">
                <span>{row.skill}</span>
                <span className="text-[var(--color-text-muted)]">
                  {row.question_count} q
                  {row.key_point_coverage_avg != null
                    ? ` · ${Math.round(row.key_point_coverage_avg * 100)}% coverage`
                    : ''}
                </span>
              </div>
            ))}
          </div>
        </Card>
      )}

      <div className="flex flex-wrap gap-2">
        <Link to="/interviews/review">
          <Button variant="primary">Needs review queue</Button>
        </Link>
        <Link to="/interviews/session/new">
          <Button>Start another session</Button>
        </Link>
        <Link to="/interviews/history">
          <Button>History</Button>
        </Link>
      </div>
    </div>
  )
}
