import { useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useLocation } from 'react-router-dom'

import { Button } from '@/components/common/Button'
import { ErrorState, LoadingState } from '@/components/practice-workspace/PracticeWorkspace'
import { useAuth } from '@/hooks/useAuth'
import {
  SUPPORT_CATEGORIES,
  SUPPORT_STATUSES,
  createSupportTicket,
  currentSupportPagePath,
  fetchMyTickets,
  newClientRequestId,
  supportLabel,
  type SupportCategory,
} from '@/services/supportService'

export function FeedbackPanel({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { user } = useAuth()
  const location = useLocation()
  const queryClient = useQueryClient()
  const pagePath = currentSupportPagePath(location.pathname)
  const requestId = useRef(newClientRequestId())
  const [category, setCategory] = useState<SupportCategory>('bug')
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [fieldError, setFieldError] = useState('')
  const [confirmation, setConfirmation] = useState<{ reference: string; id: string } | null>(null)
  const tickets = useQuery({
    queryKey: ['support-tickets', user?.id],
    queryFn: fetchMyTickets,
    enabled: open && Boolean(user?.id),
  })
  const create = useMutation({
    mutationFn: createSupportTicket,
    onSuccess: (ticket) => {
      setConfirmation({ reference: ticket.reference, id: ticket.id })
      setFieldError('')
      queryClient.invalidateQueries({ queryKey: ['support-tickets', user?.id] })
    },
  })

  if (!open || !user) return null

  function resetDraft() {
    requestId.current = newClientRequestId()
    setTitle('')
    setDescription('')
    setCategory('bug')
    setFieldError('')
    setConfirmation(null)
    create.reset()
  }

  function submit() {
    const trimmedTitle = title.trim()
    const trimmedDescription = description.trim()
    if (trimmedTitle.length < 3) {
      setFieldError('Title must be at least 3 characters.')
      return
    }
    if (trimmedTitle.length > 160) {
      setFieldError('Title must be 160 characters or fewer.')
      return
    }
    if (trimmedDescription.length < 10) {
      setFieldError('Description must be at least 10 characters.')
      return
    }
    if (trimmedDescription.length > 4000) {
      setFieldError('Description must be 4000 characters or fewer.')
      return
    }
    setFieldError('')
    create.mutate({
      category,
      title: trimmedTitle,
      description: trimmedDescription,
      page_path: pagePath,
      client_request_id: requestId.current,
    })
  }

  return (
    <>
      <button type="button" className="feedback-backdrop" aria-label="Close feedback" onClick={onClose} />
      <aside id="student-feedback-panel" className="feedback-panel" role="dialog" aria-modal="true" aria-labelledby="feedback-title">
        <div className="mb-4 flex items-start justify-between gap-3">
          <div>
            <h2 id="feedback-title" className="text-lg font-semibold">
              Feedback
            </h2>
            <p className="mt-1 text-sm text-[var(--color-text-muted)]">
              This page: <span className="support-text">{pagePath}</span>
            </p>
          </div>
          <Button type="button" variant="ghost" size="sm" onClick={onClose}>
            Close
          </Button>
        </div>

        {confirmation ? (
          <div className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface-muted)] p-3 text-sm">
            <p className="font-medium">Request received</p>
            <p className="mt-1">
              Ticket reference <strong>{confirmation.reference}</strong>
            </p>
            <Link
              className="mt-3 inline-block text-[var(--color-accent)] hover:underline"
              to={`/support/requests/${confirmation.id}`}
              onClick={onClose}
            >
              View this request
            </Link>
            <div className="mt-3">
              <Button type="button" variant="secondary" size="sm" onClick={resetDraft}>
                Send another
              </Button>
            </div>
          </div>
        ) : (
          <form
            className="grid gap-3"
            onSubmit={(event) => {
              event.preventDefault()
              submit()
            }}
          >
            <label className="grid gap-1 text-sm">
              Category
              <select
                className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2"
                value={category}
                onChange={(event) => setCategory(event.target.value as SupportCategory)}
              >
                {SUPPORT_CATEGORIES.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="grid gap-1 text-sm">
              Title
              <input
                className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2"
                value={title}
                maxLength={160}
                required
                onChange={(event) => setTitle(event.target.value)}
              />
            </label>
            <label className="grid gap-1 text-sm">
              Description
              <textarea
                className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2"
                rows={5}
                value={description}
                maxLength={4000}
                required
                onChange={(event) => setDescription(event.target.value)}
              />
            </label>
            {fieldError ? <p className="text-sm text-[var(--color-danger)]">{fieldError}</p> : null}
            {create.isError ? (
              <ErrorState message={create.error instanceof Error ? create.error.message : 'Could not send feedback.'} />
            ) : null}
            <div>
              <Button type="submit" variant="primary" size="sm" disabled={create.isPending}>
                {create.isPending ? 'Sending...' : create.isError ? 'Retry' : 'Send feedback'}
              </Button>
            </div>
          </form>
        )}

        <div className="mt-6">
          <div className="mb-2 flex items-center justify-between gap-2">
            <h3 className="text-sm font-semibold">My requests</h3>
            <Link className="text-sm text-[var(--color-accent)] hover:underline" to="/support/requests" onClick={onClose}>
              Open list
            </Link>
          </div>
          {tickets.isLoading ? <LoadingState label="Loading your requests" /> : null}
          {tickets.isError ? (
            <div className="space-y-2">
              <ErrorState message="Could not load your requests." />
              <Button type="button" variant="secondary" size="sm" onClick={() => tickets.refetch()}>
                Retry
              </Button>
            </div>
          ) : null}
          {tickets.data && tickets.data.length === 0 ? (
            <p className="text-sm text-[var(--color-text-muted)]">No requests yet.</p>
          ) : null}
          <ul className="space-y-2">
            {(tickets.data ?? []).map((ticket) => (
              <li key={ticket.id}>
                <Link
                  className="block rounded-md border border-[var(--color-border)] px-3 py-2 text-sm hover:bg-[var(--color-surface-muted)]"
                  to={`/support/requests/${ticket.id}`}
                  onClick={onClose}
                >
                  <span className="font-medium">{ticket.reference}</span>
                  <span className="text-[var(--color-text-muted)]"> · {supportLabel(SUPPORT_STATUSES, ticket.status)}</span>
                  <span className="mt-1 block">{ticket.title}</span>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </aside>
    </>
  )
}
