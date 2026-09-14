import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { Button } from '@/components/common/Button'
import { fetchReviewQueue, reviewSubmission } from '@/services/studioService'

export function AdminStudioReviewsPage() {
  const queryClient = useQueryClient()
  const { data, isLoading, isError } = useQuery({ queryKey: ['studio-reviews'], queryFn: fetchReviewQueue })
  const [feedback, setFeedback] = useState<Record<string, string>>({})
  const review = useMutation({
    mutationFn: ({ id, note }: { id: string; note: string }) => reviewSubmission(id, { feedback: note, grade: 'met' }),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['studio-reviews'] }),
  })

  return (
    <div className="module-page">
      <header className="module-heading">
        <div>
          <p className="eyebrow">Admin</p>
          <h1>Assignment reviews</h1>
        </div>
      </header>
      {isLoading ? <p>Loading submissions...</p> : isError ? <p role="alert">Unable to load the review queue.</p> : (data ?? []).length === 0 ? <p>No submissions waiting.</p> : (
        <ul className="space-y-4">
          {(data ?? []).map((item) => (
            <li key={item.id} className="rounded-[5px] border border-[var(--color-border)] p-3 text-sm">
              <p>{item.title} · version {item.version}</p>
              <pre className="mt-2 whitespace-pre-wrap text-xs">{item.answer_text}</pre>
              {item.evidence_url && <p className="mt-1">{item.evidence_url}</p>}
              <label className="mt-2 block" htmlFor={`feedback-${item.id}`}>Feedback</label>
              <textarea id={`feedback-${item.id}`} className="mt-1 w-full rounded-[5px] border border-[var(--color-border)] p-2" value={feedback[item.id] ?? ''} onChange={(event) => setFeedback((current) => ({ ...current, [item.id]: event.target.value }))} />
              <Button className="mt-2" disabled={!feedback[item.id]} onClick={() => review.mutate({ id: item.id, note: feedback[item.id] })}>Record feedback</Button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
