import type { FormEvent } from 'react'
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
import {
  ErrorState,
  LoadingState,
  PracticeHeader,
  SuccessState,
} from '@/components/practice-workspace/PracticeWorkspace'
import {
  ApplicationStatusBadge,
  applicationStatusLabel,
} from '@/features/jobs/ApplicationStatusBadge'
import {
  changeApplicationStatus,
  fetchApplication,
  fetchApplicationHistory,
  updateApplication,
} from '@/services/jobService'
import type { ApplicationStatus } from '@/types/job'

const STATUS_OPTIONS: ApplicationStatus[] = [
  'preparing',
  'applied',
  'screening',
  'assessment',
  'interview',
  'offer',
  'rejected',
  'withdrawn',
  'accepted',
  'ghosted',
]

const inputClass =
  'mt-1 w-full rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)]'

function formatDateTime(value: string | null) {
  if (!value) return '—'
  return new Date(value).toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

export function JobApplicationDetailPage() {
  const { applicationId } = useParams<{ applicationId: string }>()
  const queryClient = useQueryClient()

  const { data, isLoading, error } = useQuery({
    queryKey: ['application', applicationId],
    queryFn: () => fetchApplication(applicationId!),
    enabled: Boolean(applicationId),
  })

  const { data: history } = useQuery({
    queryKey: ['application-history', applicationId],
    queryFn: () => fetchApplicationHistory(applicationId!),
    enabled: Boolean(applicationId),
  })

  const [notes, setNotes] = useState('')
  const [followUp, setFollowUp] = useState('')
  const [statusNote, setStatusNote] = useState('')
  const [newStatus, setNewStatus] = useState<ApplicationStatus>('applied')

  useEffect(() => {
    if (data) {
      setNotes(data.notes ?? '')
      setFollowUp(data.next_follow_up_at ? data.next_follow_up_at.slice(0, 16) : '')
      setNewStatus(data.status)
    }
  }, [data])

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['application', applicationId] })
    queryClient.invalidateQueries({ queryKey: ['application-history', applicationId] })
    queryClient.invalidateQueries({ queryKey: ['applications'] })
    queryClient.invalidateQueries({ queryKey: ['jobs-summary'] })
  }

  const updateMutation = useMutation({
    mutationFn: (payload: Parameters<typeof updateApplication>[1]) =>
      updateApplication(applicationId!, payload),
    onSuccess: invalidate,
  })

  const statusMutation = useMutation({
    mutationFn: () =>
      changeApplicationStatus(applicationId!, {
        to_status: newStatus,
        note: statusNote || null,
      }),
    onSuccess: () => {
      setStatusNote('')
      invalidate()
    },
  })

  if (isLoading) return <LoadingState label="Loading application" />
  if (error || !data) return <ErrorState message="Unable to load this application." />

  const applyUrl = data.application_url || data.job.apply_url || data.job.source_url

  const onSaveNotes = (e: FormEvent) => {
    e.preventDefault()
    updateMutation.mutate({
      notes: notes || null,
      next_follow_up_at: followUp ? new Date(followUp).toISOString() : null,
    })
  }

  return (
    <div className="space-y-6">
      <PracticeHeader
        backTo="/jobs/applications"
        backLabel="Applications"
        title={data.job.title}
      >
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">{data.job.company_name}</p>
        <div className="mt-2 flex flex-wrap gap-2">
          <ApplicationStatusBadge status={data.status} />
          <Badge>{data.priority} priority</Badge>
          {data.applied_at && <Badge>Applied {formatDateTime(data.applied_at)}</Badge>}
        </div>
      </PracticeHeader>

      <div className="flex flex-wrap gap-2">
        <Link to={`/jobs/${data.job.slug}`}>
          <Button>View job</Button>
        </Link>
        {applyUrl && (
          <a href={applyUrl} target="_blank" rel="noopener noreferrer">
            <Button>Open application URL</Button>
          </a>
        )}
      </div>

      {(updateMutation.isSuccess || statusMutation.isSuccess) && (
        <SuccessState title="Application updated" />
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader title="Status change" />
          <div className="space-y-3">
            <select
              className={inputClass}
              value={newStatus}
              onChange={(e) => setNewStatus(e.target.value as ApplicationStatus)}
            >
              {STATUS_OPTIONS.map((s) => (
                <option key={s} value={s}>{applicationStatusLabel(s)}</option>
              ))}
            </select>
            <textarea
              className={inputClass}
              rows={2}
              placeholder="Note for this status change"
              value={statusNote}
              onChange={(e) => setStatusNote(e.target.value)}
            />
            <Button
              type="button"
              variant="primary"
              onClick={() => statusMutation.mutate()}
              disabled={statusMutation.isPending}
            >
              Update status
            </Button>
          </div>
        </Card>

        <Card>
          <CardHeader title="Notes & follow-up" />
          <form onSubmit={onSaveNotes} className="space-y-3">
            <div>
              <label className="text-xs text-[var(--color-text-muted)]">Next follow-up</label>
              <input
                type="datetime-local"
                className={inputClass}
                value={followUp}
                onChange={(e) => setFollowUp(e.target.value)}
              />
            </div>
            <div>
              <label className="text-xs text-[var(--color-text-muted)]">Notes</label>
              <textarea
                className={inputClass}
                rows={4}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
              />
            </div>
            <Button type="submit" disabled={updateMutation.isPending}>Save</Button>
          </form>
        </Card>
      </div>

      <Card>
        <CardHeader title="Status timeline" />
        {history && history.length > 0 ? (
          <ol className="space-y-3">
            {history.map((item) => (
              <li
                key={item.id}
                className="rounded-md border border-[var(--color-border)] p-3 text-sm"
              >
                <div className="flex flex-wrap items-center gap-2">
                  {item.from_status && (
                    <ApplicationStatusBadge status={item.from_status} />
                  )}
                  <span className="text-[var(--color-text-muted)]">→</span>
                  <ApplicationStatusBadge status={item.to_status} />
                  <span className="text-xs text-[var(--color-text-subtle)]">
                    {formatDateTime(item.changed_at)}
                  </span>
                </div>
                {item.note && (
                  <p className="mt-2 text-[var(--color-text-muted)]">{item.note}</p>
                )}
              </li>
            ))}
          </ol>
        ) : (
          <p className="text-sm text-[var(--color-text-muted)]">No status history yet.</p>
        )}
      </Card>
    </div>
  )
}
