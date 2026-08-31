import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
import {
  EmptyState,
  ErrorState,
  LoadingState,
  PracticeProgress,
} from '@/components/practice-workspace/PracticeWorkspace'
import { InterviewPackCard } from '@/features/interviews/InterviewPackCard'
import { InterviewSessionRow } from '@/features/interviews/InterviewSessionRow'
import { fetchInterviewHub } from '@/services/interviewService'

export function InterviewHubPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['interview-hub'],
    queryFn: fetchInterviewHub,
  })

  if (isLoading) return <LoadingState label="Loading interview hub" />
  if (error || !data) {
    return <ErrorState message="Unable to load interview hub." />
  }

  const reviewed = data.progress.questions_reviewed
  const needsReview = data.needs_review_count || data.progress.needs_review
  const progressPercent =
    reviewed + needsReview > 0
      ? Math.round((reviewed / Math.max(reviewed + needsReview, 1)) * 100)
      : 0

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold text-[var(--color-text)]">Interview Prep</h1>
          <p className="mt-1 text-sm text-[var(--color-text-muted)]">
            Study packs, mock sessions, and self-review — no fake interview scores.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link to="/interviews/session/new">
            <Button variant="primary">Start session</Button>
          </Link>
          <Link to="/interviews/questions">
            <Button>Browse questions</Button>
          </Link>
        </div>
      </div>

      {data.continue_session && data.continue_session.status === 'active' && (
        <Card>
          <CardHeader
            title="Continue"
            description={data.continue_session.title}
            action={
              <Link to={`/interviews/sessions/${data.continue_session.id}`}>
                <Button variant="primary" size="sm">
                  Resume
                </Button>
              </Link>
            }
          />
          <p className="text-sm text-[var(--color-text-muted)]">
            Question {data.continue_session.current_question_index} of{' '}
            {data.continue_session.question_count} · {data.continue_session.mode.replace('_', ' ')}
          </p>
        </Card>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Card padding="sm">
          <p className="text-xs text-[var(--color-text-muted)]">Questions reviewed</p>
          <p className="mt-1 text-2xl font-semibold text-[var(--color-text)]">
            {data.progress.questions_reviewed}
          </p>
        </Card>
        <Card padding="sm">
          <p className="text-xs text-[var(--color-text-muted)]">Needs review</p>
          <p className="mt-1 text-2xl font-semibold text-[var(--color-text)]">{needsReview}</p>
          <Link
            to="/interviews/review"
            className="mt-2 inline-block text-xs text-[var(--color-accent)] hover:underline"
          >
            Open review queue
          </Link>
        </Card>
        <Card padding="sm">
          <p className="text-xs text-[var(--color-text-muted)]">Sessions completed</p>
          <p className="mt-1 text-2xl font-semibold text-[var(--color-text)]">
            {data.progress.sessions_completed}
          </p>
          <div className="mt-3">
            <PracticeProgress percent={progressPercent} label="Review coverage" />
          </div>
        </Card>
      </div>

      <Card>
        <CardHeader
          title="Interview packs"
          action={
            <Link to="/interviews/packs" className="text-xs text-[var(--color-accent)] hover:underline">
              View all
            </Link>
          }
        />
        {data.packs.length ? (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {data.packs.slice(0, 6).map((pack) => (
              <InterviewPackCard key={pack.id} pack={pack} />
            ))}
          </div>
        ) : (
          <EmptyState title="No packs yet" description="Approved interview packs will appear here." />
        )}
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader
            title="Recent sessions"
            action={
              <Link
                to="/interviews/history"
                className="text-xs text-[var(--color-accent)] hover:underline"
              >
                History
              </Link>
            }
          />
          {data.recent_sessions.length ? (
            <div className="space-y-2">
              {data.recent_sessions.slice(0, 5).map((session) => (
                <InterviewSessionRow key={session.id} session={session} />
              ))}
            </div>
          ) : (
            <EmptyState title="No sessions yet" description="Start a study or mock session." />
          )}
        </Card>
        <Card>
          <CardHeader title="Quick links" />
          <div className="flex flex-col gap-2 text-sm">
            <Link to="/interviews/progress" className="text-[var(--color-accent)] hover:underline">
              Progress breakdown
            </Link>
            <Link to="/interviews/review" className="text-[var(--color-accent)] hover:underline">
              Needs review ({needsReview})
            </Link>
            <Link to="/company-prep" className="text-[var(--color-accent)] hover:underline">
              Company prep
            </Link>
            <Link to="/practice" className="text-[var(--color-accent)] hover:underline">
              Practice hub search
            </Link>
          </div>
        </Card>
      </div>
    </div>
  )
}
