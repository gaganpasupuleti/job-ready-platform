import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
import { ErrorState, LoadingState } from '@/components/practice-workspace/PracticeWorkspace'
import { fetchMyAssignments, submitManualAssignment } from '@/services/assignmentService'

const inputClass =
  'mt-1 w-full rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)]'

export function ManualAssignmentSection({ projectId }: { projectId?: string }) {
  const queryClient = useQueryClient()
  const location = useLocation()
  const [title, setTitle] = useState('')
  const [link, setLink] = useState('')
  const [note, setNote] = useState('')
  const [question, setQuestion] = useState('')
  const [error, setError] = useState('')

  const { data, isLoading, isError } = useQuery({
    queryKey: ['manual-assignments'],
    queryFn: fetchMyAssignments,
  })

  const submit = useMutation({
    mutationFn: submitManualAssignment,
    onSuccess: () => {
      setTitle('')
      setLink('')
      setNote('')
      setQuestion('')
      setError('')
      void queryClient.invalidateQueries({ queryKey: ['manual-assignments'] })
    },
    onError: (submitError: Error) => {
      setError(submitError.message || 'Could not submit the assignment.')
    },
  })

  const mine = (data ?? []).filter((item) => !projectId || item.project_id === projectId)

  useEffect(() => {
    const id = location.hash.replace(/^#/, '')
    if (!id.startsWith('submission-')) return
    document.getElementById(id)?.scrollIntoView({ block: 'nearest' })
  }, [location.hash, data])

  return (
    <Card>
      <CardHeader
        title="Submit a manual assignment"
        description="Paste a GitHub repository or another https link. This is saved for review. It is not graded automatically and it does not mark the project complete."
      />
      <form
        className="grid gap-3"
        onSubmit={(event) => {
          event.preventDefault()
          setError('')
          submit.mutate({
            title: title.trim(),
            link: link.trim(),
            note: note.trim() || undefined,
            question: question.trim() || undefined,
            project_id: projectId,
          })
        }}
      >
        <label className="text-xs text-[var(--color-text-muted)]">
          Title
          <input className={inputClass} value={title} onChange={(e) => setTitle(e.target.value)} required minLength={3} />
        </label>
        <label className="text-xs text-[var(--color-text-muted)]">
          Link
          <input
            className={inputClass}
            value={link}
            onChange={(e) => setLink(e.target.value)}
            placeholder="https://github.com/you/repo"
            required
          />
        </label>
        <label className="text-xs text-[var(--color-text-muted)]">
          What you did
          <textarea className={inputClass} rows={3} value={note} onChange={(e) => setNote(e.target.value)} />
        </label>
        <label className="text-xs text-[var(--color-text-muted)]">
          Question for review
          <textarea className={inputClass} rows={2} value={question} onChange={(e) => setQuestion(e.target.value)} />
        </label>
        {error ? <p className="text-sm text-[var(--color-danger)]">{error}</p> : null}
        <div>
          <Button type="submit" variant="primary" disabled={submit.isPending}>
            {submit.isPending ? 'Submitting...' : 'Submit for review'}
          </Button>
        </div>
      </form>

      {isLoading ? <LoadingState label="Loading your submissions" /> : null}
      {isError ? <ErrorState message="Could not load your submissions." /> : null}
      {!isLoading && !isError && mine.length === 0 ? (
        <p className="mt-4 text-sm text-[var(--color-text-muted)]">No submissions yet.</p>
      ) : null}
      {!isLoading && !isError && mine.length > 0 ? (
        <div className="mt-4 space-y-3">
          {mine.map((item) => (
            <div key={item.id} id={`submission-${item.id}`} className="rounded-md border border-[var(--color-border)] p-3 text-sm">
              <p className="font-medium">{item.title}</p>
              <a className="text-[var(--color-accent)] hover:underline" href={item.link} target="_blank" rel="noreferrer">
                {item.link}
              </a>
              <p className="mt-1 text-xs text-[var(--color-text-subtle)]">
                {item.kind} · {item.status === 'reviewed' ? 'Reviewed' : 'Awaiting review'} · not graded
              </p>
              {item.question ? <p className="mt-2 text-[var(--color-text-muted)]">Question: {item.question}</p> : null}
              {item.review_note ? <p className="mt-2">Review: {item.review_note}</p> : null}
            </div>
          ))}
        </div>
      ) : null}
    </Card>
  )
}
