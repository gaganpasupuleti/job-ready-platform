import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { useState } from 'react'

import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { Card } from '@/components/common/Card'
import {
  approveContentCandidate,
  fetchContentBatch,
  rejectContentCandidate,
  updateContentCandidate,
} from '@/services/contentService'

export function AdminContentBatchPage() {
  const { batchId = '' } = useParams()
  const queryClient = useQueryClient()
  const [editingId, setEditingId] = useState<string | null>(null)
  const [draftAnswer, setDraftAnswer] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['admin-content-batch', batchId],
    queryFn: () => fetchContentBatch(batchId),
    enabled: Boolean(batchId),
  })

  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: ['admin-content-batch', batchId] })

  const approveOne = useMutation({
    mutationFn: approveContentCandidate,
    onSuccess: invalidate,
  })
  const rejectOne = useMutation({
    mutationFn: rejectContentCandidate,
    onSuccess: invalidate,
  })
  const saveEdit = useMutation({
    mutationFn: () => updateContentCandidate(editingId!, { expected_answer: draftAnswer }),
    onSuccess: () => {
      setEditingId(null)
      invalidate()
    },
  })

  if (isLoading || !data) {
    return <p className="text-sm text-[var(--color-text-muted)]">Loading batch...</p>
  }

  return (
    <div className="space-y-6">
      <div>
        <Link to="/admin/content" className="text-xs text-[var(--color-accent)] hover:underline">
          ← Content factory
        </Link>
        <h2 className="text-lg font-semibold text-[var(--color-text)]">
          Batch {data.source_filename ?? data.id.slice(0, 8)}
        </h2>
        <p className="text-sm text-[var(--color-text-muted)]">
          Generated {data.generated_count} · accepted {data.accepted_count} · rejected {data.rejected_count}
        </p>
      </div>

      {(data.candidates ?? []).map((item) => {
        const payload = item.payload_json
        const errors = item.validation_errors?.errors ?? []
        const warnings = item.validation_errors?.warnings ?? []
        return (
          <Card key={item.id} padding="md">
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <Badge>{String(payload.difficulty ?? '')}</Badge>
              <Badge>{String(payload.question_type ?? '')}</Badge>
              <Badge variant={item.review_status === 'approved' ? 'success' : 'warning'}>
                {item.review_status}
              </Badge>
              <Badge variant={item.validation_status === 'valid' ? 'success' : 'warning'}>
                {item.validation_status}
              </Badge>
            </div>
            <p className="font-medium text-[var(--color-text)]">{String(payload.question_text ?? '')}</p>
            <p className="mt-2 whitespace-pre-wrap text-sm text-[var(--color-text-muted)]">
              {String(payload.expected_answer ?? '')}
            </p>
            {Array.isArray(payload.key_points) && (
              <ul className="mt-2 list-disc pl-5 text-sm text-[var(--color-text-muted)]">
                {(payload.key_points as string[]).map((point) => (
                  <li key={point}>{point}</li>
                ))}
              </ul>
            )}
            {errors.length > 0 && (
              <p className="mt-2 text-sm text-red-600">{errors.join(' ')}</p>
            )}
            {warnings.length > 0 && (
              <p className="mt-2 text-sm text-amber-700">{warnings.join(' ')}</p>
            )}
            {item.review_status === 'pending' && (
              <div className="mt-3 flex flex-wrap gap-2">
                {editingId === item.id ? (
                  <>
                    <textarea
                      className="w-full rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] p-2 text-sm"
                      rows={4}
                      value={draftAnswer}
                      onChange={(e) => setDraftAnswer(e.target.value)}
                    />
                    <Button size="sm" variant="primary" onClick={() => saveEdit.mutate()}>
                      Save
                    </Button>
                    <Button size="sm" onClick={() => setEditingId(null)}>
                      Cancel
                    </Button>
                  </>
                ) : (
                  <>
                    <Button
                      size="sm"
                      variant="primary"
                      disabled={item.validation_status !== 'valid'}
                      onClick={() => approveOne.mutate(item.id)}
                    >
                      Approve
                    </Button>
                    <Button size="sm" onClick={() => rejectOne.mutate(item.id)}>
                      Reject
                    </Button>
                    <Button
                      size="sm"
                      onClick={() => {
                        setEditingId(item.id)
                        setDraftAnswer(String(payload.expected_answer ?? ''))
                      }}
                    >
                      Edit answer
                    </Button>
                  </>
                )}
              </div>
            )}
          </Card>
        )
      })}
    </div>
  )
}
