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
  fetchMyTicket,
  fetchMyTickets,
  newClientRequestId,
  replyToMyTicket,
  supportLabel,
} from '@/services/supportService'

export function MyRequestsPage() {
  const { user } = useAuth()
  const { ticketId } = useParams()
  const queryClient = useQueryClient()
  const replyId = useRef(newClientRequestId())
  const [body, setBody] = useState('')
  const [fieldError, setFieldError] = useState('')
  const tickets = useQuery({
    queryKey: ['support-tickets', user?.id],
    queryFn: fetchMyTickets,
    enabled: Boolean(user?.id),
  })
  const ticket = useQuery({
    queryKey: ['support-ticket', user?.id, ticketId],
    queryFn: () => fetchMyTicket(ticketId!),
    enabled: Boolean(user?.id && ticketId),
  })
  const reply = useMutation({
    mutationFn: (text: string) => replyToMyTicket(ticketId!, text, replyId.current),
    onSuccess: async () => {
      replyId.current = newClientRequestId()
      setBody('')
      setFieldError('')
      await queryClient.invalidateQueries({ queryKey: ['support-ticket', user?.id, ticketId] })
      await queryClient.invalidateQueries({ queryKey: ['support-tickets', user?.id] })
    },
  })

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-lg font-semibold">My requests</h1>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">Feedback you have sent, including replies and status.</p>
      </div>
      {tickets.isLoading ? <LoadingState label="Loading your requests" /> : null}
      {supportLoadFailed(tickets) ? (
        <div className="space-y-2">
          <ErrorState message={supportLoadMessage(tickets.error, 'Could not load your requests.')} />
          <Button type="button" variant="secondary" size="sm" onClick={() => tickets.refetch()}>
            Retry
          </Button>
        </div>
      ) : null}
      {tickets.data && tickets.data.length === 0 ? (
        <EmptyState title="No requests yet" description="Use Feedback in the header to send a bug, idea, or note." />
      ) : null}
      {tickets.data && tickets.data.length > 0 ? (
        <ul className="space-y-2">
          {tickets.data.map((item) => (
            <li key={item.id}>
              <Link
                to={`/support/requests/${item.id}`}
                className="block rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm hover:bg-[var(--color-surface-muted)]"
              >
                <span className="font-medium">{item.reference}</span>
                <span className="text-[var(--color-text-muted)]">
                  {' '}
                  · {supportLabel(SUPPORT_CATEGORIES, item.category)} · {supportLabel(SUPPORT_STATUSES, item.status)}
                </span>
                <span className="mt-1 block">{item.title}</span>
              </Link>
            </li>
          ))}
        </ul>
      ) : null}

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
            description={`${ticket.data.reference} · ${supportLabel(SUPPORT_CATEGORIES, ticket.data.category)} · ${supportLabel(SUPPORT_STATUSES, ticket.data.status)}`}
          />
          {ticket.data.page_path ? (
            <p className="mb-3 text-sm text-[var(--color-text-muted)]">
              Reported page: <span className="support-text">{ticket.data.page_path}</span>
            </p>
          ) : null}
          <p className="support-text text-sm">{ticket.data.description}</p>
          <div className="mt-4">
            <SupportTimeline items={ticket.data.timeline} />
          </div>
          <form
            className="mt-4 grid gap-2"
            onSubmit={(event) => {
              event.preventDefault()
              const text = body.trim()
              if (!text) {
                setFieldError('Write a follow-up before sending.')
                return
              }
              if (text.length > 4000) {
                setFieldError('Follow-up must be 4000 characters or fewer.')
                return
              }
              setFieldError('')
              reply.mutate(text)
            }}
          >
            <label className="grid gap-1 text-sm">
              Follow-up
              <textarea
                className="w-full rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm"
                rows={3}
                value={body}
                maxLength={4000}
                onChange={(event) => setBody(event.target.value)}
              />
            </label>
            {fieldError ? <p className="text-sm text-[var(--color-danger)]">{fieldError}</p> : null}
            {reply.isError ? (
              <ErrorState message={reply.error instanceof Error ? reply.error.message : 'Could not send the follow-up.'} />
            ) : null}
            <div>
              <Button type="submit" variant="primary" size="sm" disabled={reply.isPending}>
                {reply.isPending ? 'Sending...' : reply.isError ? 'Retry' : 'Send follow-up'}
              </Button>
            </div>
          </form>
        </Card>
      ) : null}
    </div>
  )
}
