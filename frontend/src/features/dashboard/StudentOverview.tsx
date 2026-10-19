import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
import { EmptyState, ErrorState } from '@/components/practice-workspace/PracticeWorkspace'
import { statusLabel } from '@/components/practice-workspace/practiceWorkspaceUtils'
import {
  mcqAccuracyState,
  practiceCatalogHref,
  quizStatusCounts,
  recentPracticeHref,
  sectionStaleMessage,
  sectionUnavailable,
  visibleQuizzes,
  type SectionQuery,
} from '@/features/dashboard/overviewModel'
import { fetchJobs } from '@/services/jobService'
import {
  fetchNotifications,
  fetchUnreadCount,
  markNotificationRead,
  notificationDestination,
  type NotificationItem,
} from '@/services/notificationService'
import { fetchPracticeTracker, type PracticeTracker } from '@/services/practiceTrackerService'

const REFRESH_MS = 60_000

function visibleInterval() {
  return document.visibilityState === 'visible' ? REFRESH_MS : false
}

function sectionState(query: SectionQuery & { isPending: boolean; isFetching: boolean }) {
  return {
    loading: query.data == null && query.isPending && query.isFetching,
    unavailable: sectionUnavailable(query),
    stale: sectionStaleMessage(query, typeof navigator === 'undefined' ? true : navigator.onLine),
  }
}

function Retry({ onRetry }: { onRetry: () => void }) {
  return (
    <Button type="button" variant="secondary" size="sm" onClick={onRetry}>
      Retry
    </Button>
  )
}

function formatWhen(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
}

export function StudentOverview({ userId }: { userId: string }) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [notice, setNotice] = useState('')
  const tracker = useQuery({
    queryKey: ['practice-tracker', userId],
    queryFn: fetchPracticeTracker,
    enabled: Boolean(userId),
  })
  const jobs = useQuery({
    queryKey: ['overview-active-jobs', userId],
    queryFn: () => fetchJobs({ page: 1, limit: 5, sort: 'newest' }),
    enabled: Boolean(userId),
  })
  const unread = useQuery({
    queryKey: ['notification-unread', userId],
    queryFn: fetchUnreadCount,
    enabled: Boolean(userId),
    refetchInterval: visibleInterval,
    refetchIntervalInBackground: false,
  })
  const notifications = useQuery({
    queryKey: ['notifications', userId],
    queryFn: () => fetchNotifications(),
    enabled: Boolean(userId),
    refetchInterval: visibleInterval,
    refetchIntervalInBackground: false,
  })

  const trackerState = sectionState(tracker)
  const jobsState = sectionState(jobs)
  const notificationState = sectionState(notifications)
  const unreadState = sectionState(unread)

  async function openNotification(item: NotificationItem) {
    setNotice('')
    const destination = notificationDestination(item.destination_path)
    if (!item.read_at) {
      try {
        await markNotificationRead(item.id)
        await Promise.all([
          queryClient.invalidateQueries({ queryKey: ['notification-unread', userId] }),
          queryClient.invalidateQueries({ queryKey: ['notifications', userId] }),
        ])
      } catch (error) {
        setNotice(error instanceof Error ? error.message : 'Could not mark this notification read.')
        return
      }
    }
    if (!destination) {
      setNotice('This notification does not have a page to open.')
      return
    }
    navigate(destination)
  }

  return (
    <div className="grid min-w-0 gap-4 lg:grid-cols-2">
      <Card className="min-w-0 lg:col-span-2">
        <CardHeader
          title="This UTC week"
          description="Monday 00:00:00 UTC through the next Monday, excluding the end. Opening a page is not counted."
        />
        {trackerState.loading ? <p className="text-sm text-[var(--color-text-muted)]">Loading weekly practice</p> : null}
        {trackerState.unavailable ? (
          <div className="space-y-3">
            <ErrorState message="Weekly practice could not be loaded." />
            <Retry onRetry={() => void tracker.refetch()} />
          </div>
        ) : null}
        {trackerState.stale ? (
          <div className="mb-3 space-y-3">
            <ErrorState message={trackerState.stale} />
            <Retry onRetry={() => void tracker.refetch()} />
          </div>
        ) : null}
        {tracker.data ? <WeekDetails tracker={tracker.data} /> : null}
      </Card>

      <Card className="min-w-0">
        <CardHeader title="Recent practice" description="Saved answers and submits. Select one to resume or open its result." />
        {trackerState.loading ? <p className="text-sm text-[var(--color-text-muted)]">Loading recent practice</p> : null}
        {trackerState.unavailable ? (
          <p className="text-sm text-[var(--color-text-muted)]">Recent practice uses the weekly practice request, which did not load.</p>
        ) : null}
        {tracker.data && tracker.data.recent_practice.length === 0 ? (
          <EmptyState title="No saved practice yet" description="A page view is not an attempt." />
        ) : null}
        {tracker.data && tracker.data.recent_practice.length > 0 ? (
          <ul className="space-y-2">
            {tracker.data.recent_practice.map((item) => {
              const href = recentPracticeHref(item)
              const body = (
                <>
                  <p className="break-words text-sm font-medium text-[var(--color-text)]">{item.title}</p>
                  <p className="text-xs text-[var(--color-text-muted)]">
                    {statusLabel(item.status)} · {formatWhen(item.occurred_at)}
                  </p>
                </>
              )
              return (
                <li key={`${item.kind}-${item.source_id}`} className="min-w-0">
                  {href ? (
                    <Link to={href} className="block rounded-md border border-[var(--color-border)] p-3 hover:border-[var(--color-accent)]">
                      {body}
                    </Link>
                  ) : (
                    <div className="rounded-md border border-[var(--color-border)] p-3">{body}</div>
                  )}
                </li>
              )
            })}
          </ul>
        ) : null}
      </Card>

      <Card className="min-w-0">
        <CardHeader title="Weak topics" description="Completed MCQ sessions with at least one incorrect graded answer." />
        {trackerState.loading ? <p className="text-sm text-[var(--color-text-muted)]">Loading weak topics</p> : null}
        {trackerState.unavailable ? (
          <p className="text-sm text-[var(--color-text-muted)]">Weak topics use the weekly practice request, which did not load.</p>
        ) : null}
        {tracker.data && tracker.data.weak_topics.length === 0 ? (
          <EmptyState title="No weak topics yet" description="This appears after a completed MCQ session has an incorrect answer." />
        ) : null}
        {tracker.data && tracker.data.weak_topics.length > 0 ? (
          <ul className="space-y-2">
            {tracker.data.weak_topics.map((topic) => (
              <li key={topic.topic_id} className="min-w-0">
                <Link
                  to={practiceCatalogHref(topic.category_name)}
                  className="block rounded-md border border-[var(--color-border)] p-3 hover:border-[var(--color-accent)]"
                >
                  <p className="break-words text-sm font-medium text-[var(--color-text)]">{topic.topic_name}</p>
                  <p className="text-xs text-[var(--color-text-muted)]">
                    {topic.accuracy_percent}% of {topic.graded_answers} graded MCQ answers · {topic.incorrect_answers} incorrect
                  </p>
                </Link>
              </li>
            ))}
          </ul>
        ) : null}
      </Card>

      <Card className="min-w-0 lg:col-span-2">
        <CardHeader
          title="Quizzes"
          description={
            tracker.data && !tracker.data.recently_published.available
              ? 'Statuses are not started, in progress, or completed. These are not labeled new.'
              : 'Statuses are not started, in progress, or completed.'
          }
        />
        {trackerState.loading ? <p className="text-sm text-[var(--color-text-muted)]">Loading quizzes</p> : null}
        {trackerState.unavailable ? (
          <p className="text-sm text-[var(--color-text-muted)]">Quizzes use the weekly practice request, which did not load.</p>
        ) : null}
        {tracker.data ? <QuizDetails tracker={tracker.data} /> : null}
      </Card>

      <Card className="min-w-0">
        <CardHeader
          title="Active jobs"
          description="Active published listings from the student catalog."
          action={
            <Link to="/jobs" className="text-sm text-[var(--color-accent)] hover:underline">
              Browse jobs
            </Link>
          }
        />
        {jobsState.loading ? <p className="text-sm text-[var(--color-text-muted)]">Loading active jobs</p> : null}
        {jobsState.unavailable ? (
          <div className="space-y-3">
            <ErrorState message="Active jobs could not be loaded." />
            <Retry onRetry={() => void jobs.refetch()} />
          </div>
        ) : null}
        {jobsState.stale ? (
          <div className="mb-3 space-y-3">
            <ErrorState message={jobsState.stale} />
            <Retry onRetry={() => void jobs.refetch()} />
          </div>
        ) : null}
        {jobs.data && jobs.data.items.length === 0 ? (
          <EmptyState title="No active jobs" description="The student catalog has no active published listings." />
        ) : null}
        {jobs.data && jobs.data.items.length > 0 ? (
          <ul className="space-y-2">
            {jobs.data.items.map((job) => (
              <li key={job.id} className="min-w-0">
                <Link
                  to={`/jobs/${job.slug}`}
                  className="block rounded-md border border-[var(--color-border)] p-3 hover:border-[var(--color-accent)]"
                >
                  <p className="break-words text-sm font-medium text-[var(--color-text)]">{job.title}</p>
                  <p className="break-words text-xs text-[var(--color-text-muted)]">{job.company_name}</p>
                </Link>
              </li>
            ))}
          </ul>
        ) : null}
      </Card>

      <Card className="min-w-0">
        <CardHeader title="Unread updates" description="The count matches the notification bell." />
        {notificationState.loading || (unreadState.loading && unread.data == null) ? (
          <p className="text-sm text-[var(--color-text-muted)]">Loading updates</p>
        ) : null}
        {notificationState.unavailable ? (
          <div className="space-y-3">
            <ErrorState message="Updates could not be loaded." />
            <Retry onRetry={() => void notifications.refetch()} />
          </div>
        ) : null}
        {unreadState.unavailable && unread.data == null ? (
          <div className="mt-3 space-y-3">
            <ErrorState message="The unread count could not be loaded." />
            <Retry onRetry={() => void unread.refetch()} />
          </div>
        ) : null}
        {notificationState.stale ? (
          <div className="mb-3 space-y-3">
            <ErrorState message={notificationState.stale} />
            <Retry onRetry={() => void notifications.refetch()} />
          </div>
        ) : null}
        {notice ? <p className="mb-3 text-sm text-[var(--color-text)]">{notice}</p> : null}
        {notifications.data ? (
          <UnreadList
            count={unread.data?.count}
            items={notifications.data.items.filter((item) => !item.read_at)}
            onOpen={(item) => void openNotification(item)}
          />
        ) : null}
      </Card>
    </div>
  )
}

function WeekDetails({ tracker }: { tracker: PracticeTracker }) {
  const accuracy = mcqAccuracyState(tracker.mcq_accuracy.accuracy_percent)
  return (
    <div className="space-y-4">
      <p className="break-words text-xs text-[var(--color-text-muted)]">{tracker.week.boundary}</p>
      <div className="grid gap-3 sm:grid-cols-4">
        <Metric label="MCQ answers" value={String(tracker.weekly_activity.mcq_finalized_answers)} />
        <Metric label="Coding submits" value={String(tracker.weekly_activity.coding_submits)} />
        <Metric label="SQL submits" value={String(tracker.weekly_activity.sql_submits)} />
        <Metric label="Week total" value={String(tracker.weekly_activity.total)} />
      </div>
      <div className="grid gap-3 sm:grid-cols-3">
        <Metric label="Completed sessions" value={String(tracker.completed_sessions)} note="All time, not this UTC week." />
        <Metric label="Active sessions" value={String(tracker.in_progress_sessions)} note="Still open. Not counted as completed." />
        {accuracy.kind === 'empty' ? (
          <div className="min-w-0">
            <p className="text-xs text-[var(--color-text-muted)]">MCQ accuracy</p>
            <p className="text-sm text-[var(--color-text)]">No graded MCQ answers yet</p>
          </div>
        ) : (
          <Metric
            label="MCQ accuracy"
            value={accuracy.label}
            note={`${tracker.mcq_accuracy.correct_answers} correct of ${tracker.mcq_accuracy.graded_answers} graded MCQ answers. Coding and SQL are separate.`}
          />
        )}
      </div>
    </div>
  )
}

function QuizDetails({ tracker }: { tracker: PracticeTracker }) {
  const counts = quizStatusCounts(tracker.quizzes)
  const shown = visibleQuizzes(tracker.quizzes)
  return (
    <div className="space-y-3">
      <p className="text-sm text-[var(--color-text)]">
        {counts.not_started} not started · {counts.in_progress} in progress · {counts.completed} completed
      </p>
      {shown.length === 0 ? (
        <EmptyState title="No quizzes with active questions" />
      ) : (
        <ul className="grid gap-2 sm:grid-cols-2">
          {shown.map((quiz) => (
            <li key={quiz.topic_slug} className="min-w-0">
              <Link
                to={practiceCatalogHref(quiz.category_name)}
                className="block rounded-md border border-[var(--color-border)] p-3 hover:border-[var(--color-accent)]"
              >
                <p className="break-words text-sm font-medium text-[var(--color-text)]">{quiz.topic_name}</p>
                <p className="text-xs text-[var(--color-text-muted)]">
                  {statusLabel(quiz.attempt_status)} · {quiz.category_name}
                </p>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function UnreadList({
  count,
  items,
  onOpen,
}: {
  count: number | undefined
  items: NotificationItem[]
  onOpen: (item: NotificationItem) => void
}) {
  const shown = items.slice(0, 5)
  return (
    <div className="space-y-3">
      <p className="text-sm text-[var(--color-text)]">
        {typeof count === 'number' ? `${count} unread` : 'Unread count unavailable'}
      </p>
      {typeof count === 'number' && count === 0 ? <EmptyState title="No unread updates" /> : null}
      {typeof count === 'number' && count > 0 && shown.length === 0 ? (
        <p className="text-sm text-[var(--color-text-muted)]">Older unread updates are in the notification bell.</p>
      ) : null}
      {shown.length > 0 ? (
        <ul className="space-y-2">
          {shown.map((item) => (
            <li key={item.id} className="min-w-0">
              <button
                type="button"
                onClick={() => onOpen(item)}
                className="w-full min-w-0 rounded-md border border-[var(--color-border)] p-3 text-left hover:border-[var(--color-accent)]"
              >
                <p className="break-words text-sm text-[var(--color-text)]">{item.message}</p>
              </button>
            </li>
          ))}
        </ul>
      ) : null}
      {typeof count === 'number' && count > shown.length ? (
        <p className="text-xs text-[var(--color-text-muted)]">The notification bell lists the rest.</p>
      ) : null}
    </div>
  )
}

function Metric({ label, value, note }: { label: string; value: string; note?: string }) {
  return (
    <div className="min-w-0">
      <p className="text-xs text-[var(--color-text-muted)]">{label}</p>
      <p className="text-lg font-semibold text-[var(--color-text)]">{value}</p>
      {note ? <p className="break-words text-xs text-[var(--color-text-muted)]">{note}</p> : null}
    </div>
  )
}
