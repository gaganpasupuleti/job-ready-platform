import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { Badge } from '@/components/common/Badge'
import { Card, CardHeader } from '@/components/common/Card'
import { fetchHistory } from '@/services/practiceService'

function isActiveStatus(status: string) {
  return status.toLowerCase() === 'active'
}

export function PracticeHistory({ categoryNames = [] }: { categoryNames?: string[] }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['practice-history'],
    queryFn: fetchHistory,
  })

  if (isLoading) {
    return <p className="text-sm text-[var(--color-text-muted)]">Loading history for this subject.</p>
  }
  if (isError) {
    return (
      <p className="text-sm text-[var(--color-danger)]" role="alert">
        Could not load history for this subject.
      </p>
    )
  }

  const sessions = (data?.sessions ?? []).filter((session) => {
    if (!categoryNames.length) return true
    return Boolean(session.category_name && categoryNames.includes(session.category_name))
  })

  return (
    <Card padding="md">
      <CardHeader
        title="This subject"
        description="History and resume links stay inside the subjects on this page."
      />
      {sessions.length === 0 ? (
        <p className="text-sm text-[var(--color-text-muted)]" role="status">
          No sessions for this subject yet.
        </p>
      ) : (
      <ul className="divide-y divide-[var(--color-border)]">
        {sessions.slice(0, 8).map((session) => {
          const active = isActiveStatus(session.status)
          const href = active
            ? `/practice/sessions/${session.id}`
            : `/practice/sessions/${session.id}/results`
          return (
            <li key={session.id} className="flex items-center justify-between gap-3 py-2.5 text-sm">
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-1.5">
                  <p className="truncate font-medium text-[var(--color-text)]">
                    {session.topic_name ?? session.category_name ?? 'Practice Session'}
                  </p>
                  {active ? <Badge variant="warning">In progress</Badge> : null}
                  {session.mode === 'exam' ? <Badge>Exam</Badge> : <Badge>Practice</Badge>}
                </div>
                <p className="mt-0.5 text-[11px] text-[var(--color-text-muted)]">
                  {active
                    ? `${session.question_count} questions · resume before the deadline`
                    : `${session.correct_count}/${session.question_count} correct`}
                </p>
              </div>
              <Link
                to={href}
                className="shrink-0 text-xs font-medium text-[var(--color-accent)] hover:underline"
              >
                {active ? 'Resume' : 'View results'}
              </Link>
            </li>
          )
        })}
      </ul>
      )}
    </Card>
  )
}
