import type { FormEvent } from 'react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
import {
  ErrorState,
  LoadingState,
} from '@/components/practice-workspace/PracticeWorkspace'
import {
  createAdminInterviewPack,
  fetchAdminInterviewPacks,
  updateAdminInterviewPack,
} from '@/services/interviewService'
import type { InterviewPack } from '@/types/interview'

const inputClass =
  'mt-1 w-full rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)]'

export function AdminInterviewPacksPage() {
  const queryClient = useQueryClient()
  const { data, isLoading, error } = useQuery({
    queryKey: ['admin-interview-packs'],
    queryFn: fetchAdminInterviewPacks,
  })

  const [editing, setEditing] = useState<InterviewPack | null>(null)
  const [title, setTitle] = useState('')
  const [slug, setSlug] = useState('')
  const [description, setDescription] = useState('')
  const [experienceLevel, setExperienceLevel] = useState('')
  const [targetRole, setTargetRole] = useState('')
  const [targetCompany, setTargetCompany] = useState('')
  const [isActive, setIsActive] = useState(false)

  const resetForm = () => {
    setEditing(null)
    setTitle('')
    setSlug('')
    setDescription('')
    setExperienceLevel('')
    setTargetRole('')
    setTargetCompany('')
    setIsActive(false)
  }

  const startEdit = (pack: InterviewPack) => {
    setEditing(pack)
    setTitle(pack.title)
    setSlug(pack.slug)
    setDescription(pack.description ?? '')
    setExperienceLevel(pack.experience_level ?? '')
    setTargetRole('')
    setTargetCompany('')
    setIsActive(true)
  }

  const createMutation = useMutation({
    mutationFn: createAdminInterviewPack,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-interview-packs'] })
      resetForm()
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Parameters<typeof updateAdminInterviewPack>[1] }) =>
      updateAdminInterviewPack(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-interview-packs'] })
      resetForm()
    },
  })

  const onSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (!title.trim()) return

    if (editing) {
      updateMutation.mutate({
        id: editing.id,
        payload: {
          title: title.trim(),
          description: description || null,
          experience_level: experienceLevel || null,
          target_role: targetRole || null,
          target_company: targetCompany || null,
          is_active: isActive,
        },
      })
    } else {
      createMutation.mutate({
        title: title.trim(),
        slug: slug || undefined,
        description: description || null,
        experience_level: experienceLevel || null,
        target_role: targetRole || null,
        target_company: targetCompany || null,
        is_active: isActive,
      })
    }
  }

  const pending = createMutation.isPending || updateMutation.isPending

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-[var(--color-text)]">Interview packs</h2>
          <p className="text-sm text-[var(--color-text-muted)]">Create and edit interview practice packs</p>
        </div>
        <Link to="/admin/interviews/packs" className="text-sm text-[var(--color-accent)] hover:underline">
          /admin/interviews/packs
        </Link>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader title={editing ? `Edit: ${editing.title}` : 'Create pack'} />
          <form className="space-y-3" onSubmit={onSubmit}>
            <label className="block text-xs text-[var(--color-text-muted)]" htmlFor="admin-pack-title">
              Title
              <input
                id="admin-pack-title"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className={inputClass}
              />
            </label>
            {!editing && (
              <label className="block text-xs text-[var(--color-text-muted)]" htmlFor="admin-pack-slug">
                Slug (optional)
                <input
                  id="admin-pack-slug"
                  value={slug}
                  onChange={(e) => setSlug(e.target.value)}
                  className={inputClass}
                />
              </label>
            )}
            <label className="block text-xs text-[var(--color-text-muted)]" htmlFor="admin-pack-desc">
              Description
              <textarea
                id="admin-pack-desc"
                rows={3}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className={inputClass}
              />
            </label>
            <label className="block text-xs text-[var(--color-text-muted)]" htmlFor="admin-pack-exp">
              Experience level
              <select
                id="admin-pack-exp"
                value={experienceLevel}
                onChange={(e) => setExperienceLevel(e.target.value)}
                className={inputClass}
              >
                <option value="">None</option>
                <option value="fresher">Fresher</option>
                <option value="junior">Junior</option>
                <option value="intermediate">Intermediate</option>
                <option value="senior">Senior</option>
              </select>
            </label>
            <label className="block text-xs text-[var(--color-text-muted)]" htmlFor="admin-pack-role">
              Target role
              <input
                id="admin-pack-role"
                value={targetRole}
                onChange={(e) => setTargetRole(e.target.value)}
                className={inputClass}
              />
            </label>
            <label className="block text-xs text-[var(--color-text-muted)]" htmlFor="admin-pack-company">
              Target company
              <input
                id="admin-pack-company"
                value={targetCompany}
                onChange={(e) => setTargetCompany(e.target.value)}
                className={inputClass}
              />
            </label>
            <label
              htmlFor="admin-pack-active"
              className="flex items-center gap-2 text-sm text-[var(--color-text)]"
            >
              <input
                id="admin-pack-active"
                type="checkbox"
                checked={isActive}
                onChange={(e) => setIsActive(e.target.checked)}
              />
              Active
            </label>
            <div className="flex flex-wrap gap-2">
              <Button type="submit" variant="primary" disabled={pending}>
                {editing ? 'Save changes' : 'Create pack'}
              </Button>
              {editing && (
                <Button type="button" onClick={resetForm}>
                  Cancel
                </Button>
              )}
            </div>
            {(createMutation.isError || updateMutation.isError) && (
              <p className="text-sm text-red-700 dark:text-red-300">Save failed. Check fields and try again.</p>
            )}
          </form>
        </Card>

        <Card>
          <CardHeader title={`Packs (${data?.length ?? 0})`} />
          {isLoading && <LoadingState label="Loading packs" />}
          {error && <ErrorState message="Unable to load packs." />}
          {!isLoading && !error && (
            <div className="space-y-2">
              {(data ?? []).map((pack) => (
                <div
                  key={pack.id}
                  className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-[var(--color-border)] p-3"
                >
                  <div>
                    <p className="text-sm font-medium text-[var(--color-text)]">{pack.title}</p>
                    <p className="text-xs text-[var(--color-text-muted)]">{pack.slug}</p>
                    <div className="mt-1 flex flex-wrap gap-1">
                      <Badge>{pack.question_count} questions</Badge>
                      {pack.experience_level && <Badge>{pack.experience_level}</Badge>}
                    </div>
                  </div>
                  <Button size="sm" onClick={() => startEdit(pack)}>
                    Edit
                  </Button>
                </div>
              ))}
              {!data?.length && (
                <p className="text-sm text-[var(--color-text-muted)]">No packs yet.</p>
              )}
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}
