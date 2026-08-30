import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { useMemo, useState } from 'react'

import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
import {
  approveContentCandidate,
  bulkApproveContent,
  fetchContentBatches,
  fetchContentCandidates,
  rejectContentCandidate,
} from '@/services/contentService'

export function AdminContentPage() {
  const queryClient = useQueryClient()
  const [role, setRole] = useState('')
  const [skill, setSkill] = useState('')
  const [company, setCompany] = useState('')
  const [difficulty, setDifficulty] = useState('')
  const [contentType, setContentType] = useState('interview_qa')
  const [batchId, setBatchId] = useState('')
  const [selected, setSelected] = useState<string[]>([])

  const params = useMemo(() => {
    const next: Record<string, string> = { review_status: 'pending' }
    if (role) next.role = role
    if (skill) next.skill = skill
    if (company) next.company = company
    if (difficulty) next.difficulty = difficulty
    if (contentType) next.content_type = contentType
    if (batchId) next.batch_id = batchId
    return next
  }, [role, skill, company, difficulty, contentType, batchId])

  const { data: batches } = useQuery({
    queryKey: ['admin-content-batches'],
    queryFn: fetchContentBatches,
  })

  const { data, isLoading } = useQuery({
    queryKey: ['admin-content-candidates', params],
    queryFn: () => fetchContentCandidates(params),
  })

  const approveOne = useMutation({
    mutationFn: approveContentCandidate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-content-candidates'] })
      queryClient.invalidateQueries({ queryKey: ['admin-content-batches'] })
    },
  })
  const rejectOne = useMutation({
    mutationFn: rejectContentCandidate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-content-candidates'] })
      queryClient.invalidateQueries({ queryKey: ['admin-content-batches'] })
    },
  })
  const bulk = useMutation({
    mutationFn: () => bulkApproveContent(selected),
    onSuccess: () => {
      setSelected([])
      queryClient.invalidateQueries({ queryKey: ['admin-content-candidates'] })
      queryClient.invalidateQueries({ queryKey: ['admin-content-batches'] })
    },
  })

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-[var(--color-text)]">Content Factory</h2>
        <p className="text-sm text-[var(--color-text-muted)]">
          Review Cursor-generated interview Q&A before it becomes student-facing.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        <input
          className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1.5 text-sm"
          placeholder="Filter role"
          value={role}
          onChange={(e) => setRole(e.target.value)}
        />
        <input
          className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1.5 text-sm"
          placeholder="Filter skill"
          value={skill}
          onChange={(e) => setSkill(e.target.value)}
        />
        <input
          className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1.5 text-sm"
          placeholder="Filter company"
          value={company}
          onChange={(e) => setCompany(e.target.value)}
        />
        <input
          className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1.5 text-sm"
          placeholder="Batch id"
          value={batchId}
          onChange={(e) => setBatchId(e.target.value)}
        />
        <select
          className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1.5 text-sm"
          value={contentType}
          onChange={(e) => setContentType(e.target.value)}
        >
          <option value="interview_qa">interview_qa</option>
        </select>
        <select
          className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1.5 text-sm"
          value={difficulty}
          onChange={(e) => setDifficulty(e.target.value)}
        >
          <option value="">All difficulties</option>
          <option value="easy">easy</option>
          <option value="medium">medium</option>
          <option value="hard">hard</option>
        </select>
        <Button disabled={!selected.length || bulk.isPending} onClick={() => bulk.mutate()}>
          Bulk approve ({selected.length})
        </Button>
      </div>

      <Card>
        <CardHeader title={`Generation batches (${batches?.total ?? 0})`} />
        <div className="space-y-2 text-sm">
          {(batches?.items ?? []).slice(0, 8).map((batch) => (
            <div key={batch.id} className="flex flex-wrap items-center justify-between gap-2">
              <Link
                to={`/admin/content/batches/${batch.id}`}
                className="text-[var(--color-accent)] hover:underline"
              >
                {batch.source_filename ?? batch.id.slice(0, 8)}
              </Link>
              <span className="text-xs text-[var(--color-text-muted)]">
                {batch.generated_count} generated · {batch.accepted_count} accepted
              </span>
            </div>
          ))}
          {!batches?.items.length && (
            <p className="text-sm text-[var(--color-text-muted)]">No import batches yet.</p>
          )}
        </div>
      </Card>

      <Card>
        <CardHeader title={`Pending candidates (${data?.total ?? 0})`} />
        {isLoading ? (
          <p className="text-sm text-[var(--color-text-muted)]">Loading...</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs text-[var(--color-text-subtle)]">
                <tr>
                  <th className="pb-2"></th>
                  <th className="pb-2">Question</th>
                  <th className="pb-2">Validation</th>
                  <th className="pb-2">Batch</th>
                  <th className="pb-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {(data?.items ?? []).map((item) => {
                  const text = String(item.payload_json.question_text ?? '')
                  const valid = item.validation_status === 'valid'
                  return (
                    <tr key={item.id} className="border-t border-[var(--color-border)]">
                      <td className="py-3 pr-2">
                        <input
                          type="checkbox"
                          checked={selected.includes(item.id)}
                          onChange={(e) =>
                            setSelected((prev) =>
                              e.target.checked ? [...prev, item.id] : prev.filter((id) => id !== item.id),
                            )
                          }
                        />
                      </td>
                      <td className="py-3 pr-4">
                        <Link
                          to={`/admin/content/batches/${item.batch_id}`}
                          className="text-[var(--color-accent)] hover:underline"
                        >
                          {text.slice(0, 90) || item.id}
                        </Link>
                      </td>
                      <td className="py-3 pr-4">
                        <Badge variant={valid ? 'success' : 'warning'}>{item.validation_status}</Badge>
                      </td>
                      <td className="py-3 pr-4 text-xs text-[var(--color-text-muted)]">
                        {item.batch_id.slice(0, 8)}
                      </td>
                      <td className="py-3">
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant="primary"
                            disabled={!valid || approveOne.isPending}
                            onClick={() => approveOne.mutate(item.id)}
                          >
                            Approve
                          </Button>
                          <Button
                            size="sm"
                            disabled={rejectOne.isPending}
                            onClick={() => rejectOne.mutate(item.id)}
                          >
                            Reject
                          </Button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}
