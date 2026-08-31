import { useQuery } from '@tanstack/react-query'

import { Card, CardHeader } from '@/components/common/Card'
import {
  ErrorState,
  LoadingState,
  PracticeHeader,
  PracticeProgress,
} from '@/components/practice-workspace/PracticeWorkspace'
import { fetchInterviewProgress } from '@/services/interviewService'

function BreakdownList({ title, data }: { title: string; data: Record<string, number> }) {
  const entries = Object.entries(data)
  if (!entries.length) return null
  return (
    <Card>
      <CardHeader title={title} />
      <ul className="space-y-2 text-sm text-[var(--color-text)]">
        {entries.map(([key, count]) => (
          <li key={key} className="flex justify-between gap-2">
            <span>{key}</span>
            <span className="text-[var(--color-text-muted)]">{count}</span>
          </li>
        ))}
      </ul>
    </Card>
  )
}

export function InterviewProgressPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['interview-progress'],
    queryFn: fetchInterviewProgress,
  })

  if (isLoading) return <LoadingState label="Loading progress" />
  if (error || !data) return <ErrorState message="Unable to load interview progress." />

  const coverage =
    data.average_key_point_coverage != null
      ? Math.round(data.average_key_point_coverage * 100)
      : null

  return (
    <div className="space-y-6">
      <PracticeHeader backTo="/interviews" backLabel="Interview hub" title="Interview progress">
        <p className="text-sm text-[var(--color-text-muted)]">
          Live self-review stats — not a readiness or interview score.
        </p>
      </PracticeHeader>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card padding="sm">
          <p className="text-xs text-[var(--color-text-muted)]">Questions reviewed</p>
          <p className="text-2xl font-semibold text-[var(--color-text)]">
            {data.questions_reviewed}
          </p>
        </Card>
        <Card padding="sm">
          <p className="text-xs text-[var(--color-text-muted)]">Needs review</p>
          <p className="text-2xl font-semibold text-[var(--color-text)]">{data.needs_review}</p>
        </Card>
        <Card padding="sm">
          <p className="text-xs text-[var(--color-text-muted)]">Sessions completed</p>
          <p className="text-2xl font-semibold text-[var(--color-text)]">
            {data.sessions_completed}
          </p>
        </Card>
        <Card padding="sm">
          <p className="text-xs text-[var(--color-text-muted)]">High confidence</p>
          <p className="text-2xl font-semibold text-[var(--color-text)]">
            {data.high_confidence_percent != null
              ? `${Math.round(data.high_confidence_percent)}%`
              : '—'}
          </p>
        </Card>
      </div>

      {coverage != null && (
        <Card>
          <CardHeader title="Average key-point coverage" />
          <PracticeProgress percent={coverage} label={`${coverage}%`} />
        </Card>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        <BreakdownList title="By role" data={data.by_role} />
        <BreakdownList title="By skill" data={data.by_skill} />
        <BreakdownList title="By type" data={data.by_type} />
        <BreakdownList title="By experience" data={data.by_experience} />
      </div>
    </div>
  )
}
