import { Link } from 'react-router-dom'

import { Badge } from '@/components/common/Badge'
import type { InterviewSessionSummary } from '@/types/interview'

export function InterviewSessionStatusBadge({ status }: { status: string }) {
  const variant =
    status === 'completed' ? 'success' : status === 'abandoned' ? 'warning' : 'accent'
  return <Badge variant={variant}>{status.replace('_', ' ')}</Badge>
}

export function InterviewModeBadge({ mode }: { mode: string }) {
  return <Badge>{mode.replace('_', ' ')}</Badge>
}

export function InterviewSessionRow({ session }: { session: InterviewSessionSummary }) {
  const href =
    session.status === 'completed'
      ? `/interviews/sessions/${session.id}/results`
      : `/interviews/sessions/${session.id}`

  return (
    <Link
      to={href}
      className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-[var(--color-border)] p-3 hover:border-[var(--color-accent)]"
    >
      <div>
        <p className="text-sm font-medium text-[var(--color-text)]">{session.title}</p>
        <p className="mt-1 text-xs text-[var(--color-text-muted)]">
          {session.reviewed_count}/{session.question_count} reviewed
          {session.needs_review_count > 0 ? ` · ${session.needs_review_count} need review` : ''}
        </p>
      </div>
      <div className="flex flex-wrap gap-1">
        <InterviewModeBadge mode={session.mode} />
        <InterviewSessionStatusBadge status={session.status} />
      </div>
    </Link>
  )
}
