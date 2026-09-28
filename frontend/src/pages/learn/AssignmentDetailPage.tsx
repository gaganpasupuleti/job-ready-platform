import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { Button } from '@/components/common/Button'
import { Textarea } from '@/components/common/Field'
import { SafeMarkdown } from '@/components/learn/SafeMarkdown'
import { LearnSubnav } from '@/components/learn/LearnSubnav'
import { fetchAssignment, saveAssignmentDraft, submitAssignment } from '@/services/studioService'

export function AssignmentDetailPage() {
  const { key = '' } = useParams()
  const queryClient = useQueryClient()
  const { data, isLoading, isError } = useQuery({
    queryKey: ['studio-assignment', key],
    queryFn: () => fetchAssignment(key),
    enabled: Boolean(key),
  })
  const latest = data?.submissions.at(-1)
  const draftKey = latest?.status === 'draft' ? latest.id : 'new'
  const [answer, setAnswer] = useState('')
  const [url, setUrl] = useState('')
  const [loadedDraft, setLoadedDraft] = useState('')
  if (draftKey !== loadedDraft) {
    setLoadedDraft(draftKey)
    setAnswer(latest?.status === 'draft' ? latest.answer_text : '')
    setUrl(latest?.status === 'draft' ? latest.evidence_url ?? '' : '')
  }
  const draftMutation = useMutation({
    mutationFn: () => saveAssignmentDraft(key, { answer_text: answer, evidence_url: url }),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['studio-assignment', key] }),
  })
  const submitMutation = useMutation({
    mutationFn: () => submitAssignment(key, { answer_text: answer, evidence_url: url }),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['studio-assignment', key] }),
  })

  return (
    <div className="module-page learn-page">
      <LearnSubnav />
      {isLoading ? (
        <p>Loading assignment...</p>
      ) : isError || !data ? (
        <p role="alert">Unable to load this assignment.</p>
      ) : (
        <>
          <header className="module-heading">
            <div>
              <p className="eyebrow">
                {data.unavailable
                  ? 'Unavailable · Python locked'
                  : data.local_python
                    ? 'Local Python · manual review'
                    : data.mode === 'manual_review'
                      ? 'Local work · manual review'
                      : 'SQL evidence'}
              </p>
              <h1>{data.title}</h1>
              <p>{data.goal}</p>
            </div>
          </header>
          {data.unavailable && (
            <p role="status" className="mb-3 rounded-[5px] border border-[var(--color-border)] bg-[var(--color-surface-muted)] p-3 text-sm">
              {data.unavailable_reason ??
                'Python is locked for this release. Previous submissions and reviews stay visible. New submissions are not accepted.'}
            </p>
          )}
          {!data.unavailable && (data.local_python || data.mode === 'manual_review') && (
            <p role="status" className="mb-3 text-sm">Solve this on your own computer. The online runner is locked and will not grade this assignment.</p>
          )}
          {data.sql_problem_slug && (
            <p className="mb-3 text-sm">
              Linked SQL problem:{' '}
              <Link to={`/practice/sql/${data.sql_problem_slug}`} className="text-[var(--color-accent)]">{data.sql_problem_slug}</Link>
              . A browser note is not a substitute for an accepted studio submission.
            </p>
          )}
          <SafeMarkdown source={data.brief_md} />
          <p className="mt-2 text-xs text-[var(--color-text-muted)]">Estimated effort {data.minutes} min. Due date: {data.due_at ?? 'none'}. Version {data.version}.</p>
          <h2 className="mt-4 text-sm font-semibold">Requirements</h2>
          <ul className="list-disc pl-5 text-sm">{data.requirements.map((item) => <li key={item}>{item}</li>)}</ul>
          <h2 className="mt-4 text-sm font-semibold">Rubric</h2>
          <ul className="list-disc pl-5 text-sm">{data.rubric.map((item) => <li key={item.criterion}>{item.criterion} ({item.points})</li>)}</ul>
          {!data.unavailable && (
          <form className="mt-4 space-y-3" onSubmit={(event) => event.preventDefault()}>
            <label className="block text-sm" htmlFor="answer-text">Answer text</label>
            <Textarea id="answer-text" value={answer} onChange={(event) => setAnswer(event.target.value)} rows={8} />
            <label className="block text-sm" htmlFor="evidence-url">HTTPS repository or document URL</label>
            <input id="evidence-url" className="w-full rounded-[5px] border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1 text-sm" value={url} onChange={(event) => setUrl(event.target.value)} placeholder="https://" />
            <div className="flex flex-wrap gap-2">
              <Button type="button" variant="secondary" onClick={() => draftMutation.mutate()}>Save draft</Button>
              <Button type="button" variant="primary" onClick={() => submitMutation.mutate()}>Submit for review</Button>
            </div>
            {submitMutation.isError && <p role="alert" className="text-sm text-[var(--color-danger)]">{messageOf(submitMutation.error)}</p>}
          </form>
          )}
          <h2 className="mt-6 text-sm font-semibold">Your submissions</h2>
          {data.submissions.length === 0 ? (
            <p className="text-sm text-[var(--color-text-muted)]">No draft or submission yet.</p>
          ) : (
            <ul className="mt-2 space-y-3 text-sm">
              {data.submissions.map((item) => (
                <li key={item.id} className="rounded-[5px] border border-[var(--color-border)] p-3">
                  <p>Attempt {item.attempt} · {item.status} · version {item.version}</p>
                  {item.brief && (
                    <div className="mt-2">
                      <p className="text-xs text-[var(--color-text-muted)]">Filed brief</p>
                      <SafeMarkdown source={item.brief} />
                    </div>
                  )}
                  {item.rubric && item.rubric.length > 0 && (
                    <p className="mt-1">Filed rubric: {item.rubric.map((row) => `${row.criterion} (${row.points})`).join('; ')}</p>
                  )}
                  <pre className="mt-2 whitespace-pre-wrap text-xs">{item.answer_text}</pre>
                  {item.reviews.map((review) => (
                    <p key={`${review.version}-${review.reviewed_at ?? review.feedback}`} className="mt-2">
                      Feedback (version {review.version}{review.reviewed_at ? ` · ${review.reviewed_at.slice(0, 10)}` : ''}): {review.feedback}{review.grade ? ` · ${review.grade}` : ''}
                    </p>
                  ))}
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </div>
  )
}

function messageOf(error: unknown) {
  if (typeof error === 'object' && error && 'response' in error) {
    const detail = (error as { response?: { data?: { detail?: string } } }).response?.data?.detail
    if (detail) return detail
  }
  return 'Unable to submit.'
}
