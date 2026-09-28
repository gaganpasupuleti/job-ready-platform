import { useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'

import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
import { ErrorState, EmptyState, LoadingState } from '@/components/practice-workspace/PracticeWorkspace'
import { supportLoadFailed, supportLoadMessage } from '@/features/support/queryState'
import { SupportTimeline } from '@/features/support/SupportTimeline'
import { useAuth } from '@/hooks/useAuth'
import {
  SUPPORT_CATEGORIES,
  SUPPORT_STATUSES,
  fetchAdminTicket,
  fetchAdminTickets,
  newClientRequestId,
  replyToAdminTicket,
  supportLabel,
  updateAdminTicketStatus,
  type SupportStatus,
} from '@/services/supportService'

export function AdminFeedbackPage() {
  const { user } = useAuth()
  const { ticketId } = useParams()
  const queryClient = useQueryClient()
  const replyId = useRef(newClientRequestId())
  const statusId = useRef(newClientRequestId())
  const [category, setCategory] = useState('')
  const [status, setStatus] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [applied, setApplied] = useState({ category: '', status: '', date_from: '', date_to: '' })
  const [replyBody, setReplyBody] = useState('')
  const [nextStatus, setNextStatus] = useState<SupportStatus>('in_review')
  const [fieldError, setFieldError] = useState('')
  const filters = {
    category: applied.category || undefined,
    status: applied.status || undefined,
    date_from: applied.date_from || undefined,
    date_to: applied.date_to || undefined,
  }
  const tickets = useQuery({
    queryKey: ['admin-support-tickets', user?.id, applied],
    queryFn: () => fetchAdminTickets(filters),
    enabled: Boolean(user?.id),
  })
  const ticket = useQuery({
    queryKey: ['admin-support-ticket', user?.id, ticketId],
    queryFn: () => fetchAdminTicket(ticketId!),
    enabled: Boolean(user?.id && ticketId),
  })
  const reply = useMutation({
    mutationFn: (text: string) => replyToAdminTicket(ticketId!, text, replyId.current),
    onSuccess: async () => {
      replyId.current = newClientRequestId()
      setReplyBody('')
      setFieldError('')
      await refresh()
    },
  })
  const statusChange = useMutation({
    mutationFn: (value: SupportStatus) => updateAdminTicketStatus(ticketId!, value, statusId.current),
    onSuccess: async () => {
      statusId.current = newClientRequestId()
      await refresh()
    },
  })

  async function refresh() {
    await queryClient.invalidateQueries({ queryKey: ['admin-support-ticket', user?.id, ticketId] })
    await queryClient.invalidateQueries({ queryKey: ['admin-support-tickets', user?.id] })
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold">Student feedback</h1>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          Requests from students, with the page they were on and the conversation so far.
        </p>
      </div>
      <form
        className="grid gap-3 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-4 md:grid-cols-4"
        onSubmit={(event) => {
          event.preventDefault()
          setApplied({ category, status, date_from: dateFrom, date_to: dateTo })
        }}
      >
        <label className="grid gap-1 text-sm">
          Category
          <select
            className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2"
            value={category}
            onChange={(event) => setCategory(event.target.value)}
          >
            <option value="">All</option>
            {SUPPORT_CATEGORIES.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </label>
        <label className="grid gap-1 text-sm">
          Status
          <select
            className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2"
            value={status}
            onChange={(event) => setStatus(event.target.value)}
          >
            <option value="">All</option>
            {SUPPORT_STATUSES.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </label>
        <label className="grid gap-1 text-sm">
          From
          <input
            type="date"
            className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2"
            value={dateFrom}
            onChange={(event) => setDateFrom(event.target.value)}
          />
        </label>
        <label className="grid gap-1 text-sm">
          To
          <input
            type="date"
            className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2"
            value={dateTo}
            onChange={(event) => setDateTo(event.target.value)}
          />
        </label>
        <div className="md:col-span-4">
          <Button type="submit" variant="secondary" size="sm">
            Apply filters
          </Button>
        </div>
      </form>

      {tickets.isLoading ? <LoadingState label="Loading student feedback" /> : null}
      {supportLoadFailed(tickets) ? (
        <div className="space-y-2">
          <ErrorState message={supportLoadMessage(tickets.error, 'Could not load feedback.')} />
          <Button type="button" variant="secondary" size="sm" onClick={() => tickets.refetch()}>
            Retry
          </Button>
        </div>
      ) : null}
      {tickets.data && tickets.data.length === 0 ? <EmptyState title="No matching requests" /> : null}
      <ul className="space-y-2">
        {(tickets.data ?? []).map((item) => (
          <li key={item.id}>
            <Link
              to={`/admin/feedback/${item.id}`}
              className="block rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm hover:bg-[var(--color-surface-muted)]"
            >
              <span className="font-medium">{item.reference}</span>
              <span className="text-[var(--color-text-muted)]">
                {' '}
                · {item.student_name} · {item.student_email} · {supportLabel(SUPPORT_STATUSES, item.status)}
              </span>
              <span className="mt-1 block">{item.title}</span>
            </Link>
          </li>
        ))}
      </ul>

      {ticketId && ticket.isLoading ? <LoadingState label="Loading request" /> : null}
      {ticketId && supportLoadFailed(ticket) ? (
        <div className="space-y-2">
          <ErrorState message={supportLoadMessage(ticket.error, 'Could not load this request.')} />
          <Button type="button" variant="secondary" size="sm" onClick={() => ticket.refetch()}>
            Retry
          </Button>
        </div>
      ) : null}
      {ticket.data ? (
        <Card>
          <CardHeader
            title={ticket.data.title}
            description={`${ticket.data.reference} · ${ticket.data.student_name} · ${ticket.data.student_email} · ${supportLabel(SUPPORT_STATUSES, ticket.data.status)}`}
          />
          <p className="text-sm text-[var(--color-text-muted)]">
            {supportLabel(SUPPORT_CATEGORIES, ticket.data.category)}
            {ticket.data.page_path ? (
              <>
                {' '}
                · Reported page: <span className="support-text">{ticket.data.page_path}</span>
              </>
            ) : null}
          </p>
          <p className="support-text mt-3 text-sm">{ticket.data.description}</p>
          <div className="mt-4">
            <SupportTimeline items={ticket.data.timeline} />
          </div>
          <form
            className="mt-4 grid gap-2"
            onSubmit={(event) => {
              event.preventDefault()
              const text = replyBody.trim()
              if (!text) {
                setFieldError('Write a reply before sending.')
                return
              }
              setFieldError('')
              reply.mutate(text)
            }}
          >
            <label className="grid gap-1 text-sm">
              Reply
              <textarea
                className="w-full rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm"
                rows={3}
                value={replyBody}
                maxLength={4000}
                onChange={(event) => setReplyBody(event.target.value)}
              />
            </label>
            {fieldError ? <p className="text-sm text-[var(--color-danger)]">{fieldError}</p> : null}
            {reply.isError ? (
              <ErrorState message={reply.error instanceof Error ? reply.error.message : 'Could not send the reply.'} />
            ) : null}
            <div>
              <Button type="submit" variant="primary" size="sm" disabled={reply.isPending}>
                {reply.isPending ? 'Sending...' : reply.isError ? 'Retry' : 'Send reply'}
              </Button>
            </div>
          </form>
          <form
            className="mt-4 flex flex-wrap items-end gap-2"
            onSubmit={(event) => {
              event.preventDefault()
              statusChange.mutate(nextStatus)
            }}
          >
            <label className="grid gap-1 text-sm">
              Status
              <select
                className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2"
                value={nextStatus}
                onChange={(event) => setNextStatus(event.target.value as SupportStatus)}
              >
                {SUPPORT_STATUSES.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </select>
            </label>
            <Button type="submit" variant="secondary" size="sm" disabled={statusChange.isPending}>
              {statusChange.isPending ? 'Saving...' : statusChange.isError ? 'Retry status' : 'Update status'}
            </Button>
          </form>
          {statusChange.isError ? (
            <div className="mt-2">
              <ErrorState
                message={statusChange.error instanceof Error ? statusChange.error.message : 'Could not update the status.'}
              />
            </div>
          ) : null}
        </Card>
      ) : null}
    </div>
  )
}
