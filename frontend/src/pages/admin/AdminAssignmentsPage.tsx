import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
import { ErrorState, LoadingState } from '@/components/practice-workspace/PracticeWorkspace'
import { fetchAssignmentQueue, saveAssignmentReview } from '@/services/assignmentService'

export function AdminAssignmentsPage() {
  const queryClient = useQueryClient()
  const [notes, setNotes] = useState<Record<string, string>>({})
  const { data, isLoading, error } = useQuery({
    queryKey: ['assignment-queue'],
    queryFn: fetchAssignmentQueue,
  })
  const review = useMutation({
    mutationFn: ({ id, review_note }: { id: string; review_note: string }) =>
      saveAssignmentReview(id, review_note),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['assignment-queue'] }),
  })

  if (isLoading) return <LoadingState label="Loading assignment reports" />
  if (error) return <ErrorState message="Could not load assignment reports." />

  const pending = (data ?? []).filter((item) => item.status !== 'reviewed')

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold">Assignment reports</h1>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          {pending.length} awaiting review. These are links and questions, not automatic grades.
        </p>
      </div>
      {(data ?? []).length === 0 ? (
        <Card>
          <p className="text-sm text-[var(--color-text-muted)]">No manual submissions yet.</p>
        </Card>
      ) : (
        data!.map((item) => (
          <Card key={item.id}>
            <CardHeader
              title={item.title}
              description={`${item.student_name} · ${item.student_email} · ${item.status === 'reviewed' ? 'Reviewed' : 'Awaiting review'}`}
            />
            <a className="text-sm text-[var(--color-accent)] hover:underline" href={item.link} target="_blank" rel="noreferrer">
              {item.link}
            </a>
            {item.project_title ? <p className="mt-2 text-sm">Project: {item.project_title}</p> : null}
            {item.note ? <p className="mt-2 text-sm text-[var(--color-text-muted)]">{item.note}</p> : null}
            {item.question ? <p className="mt-2 text-sm">Question: {item.question}</p> : null}
            {item.review_note ? <p className="mt-2 text-sm">Review: {item.review_note}</p> : null}
            {item.status !== 'reviewed' ? (
              <form
                className="mt-3 grid gap-2"
                onSubmit={(event) => {
                  event.preventDefault()
                  const review_note = (notes[item.id] ?? '').trim()
                  if (review_note.length < 3) return
                  review.mutate({ id: item.id, review_note })
                }}
              >
                <textarea
                  className="w-full rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm"
                  rows={3}
                  placeholder="Review note"
                  value={notes[item.id] ?? ''}
                  onChange={(event) => setNotes((current) => ({ ...current, [item.id]: event.target.value }))}
                />
                <div>
                  <Button type="submit" variant="primary" size="sm" disabled={review.isPending}>
                    {review.isPending ? 'Saving...' : 'Save review'}
                  </Button>
                </div>
                {review.isError ? (
                  <p className="text-sm text-[var(--color-danger)]">
                    {review.error instanceof Error ? review.error.message : 'Could not save the review.'}
                  </p>
                ) : null}
              </form>
            ) : null}
          </Card>
        ))
      )}
    </div>
  )
}
