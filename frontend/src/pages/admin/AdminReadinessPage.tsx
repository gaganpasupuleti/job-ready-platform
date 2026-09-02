import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
import { ErrorState, LoadingState, SuccessState } from '@/components/practice-workspace/PracticeWorkspace'
import {
  deleteAdminRoleRequirement,
  fetchAdminReadinessRoles,
  upsertAdminRoleRequirement,
} from '@/services/adminReadinessService'

const inputClass =
  'mt-1 w-full rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)]'

const IMPORTANCE_OPTIONS = ['core', 'important', 'nice_to_have'] as const

export function AdminReadinessPage() {
  const queryClient = useQueryClient()
  const [selectedRoleId, setSelectedRoleId] = useState<string | null>(null)
  const [skillId, setSkillId] = useState('')
  const [importance, setImportance] = useState<(typeof IMPORTANCE_OPTIONS)[number]>('core')
  const [weight, setWeight] = useState('1')
  const [minimumReadiness, setMinimumReadiness] = useState('')

  const { data, isLoading, error } = useQuery({
    queryKey: ['admin-readiness-roles'],
    queryFn: fetchAdminReadinessRoles,
  })

  const selected = data?.find((r) => r.role.id === selectedRoleId) ?? data?.[0] ?? null

  const saveMutation = useMutation({
    mutationFn: async () => {
      if (!selected) throw new Error('No role selected')
      if (!skillId.trim()) throw new Error('Skill ID required')
      const w = Number(weight)
      if (Number.isNaN(w) || w < 0) throw new Error('Invalid weight')
      const min = minimumReadiness.trim() ? Number(minimumReadiness) : null
      return upsertAdminRoleRequirement(selected.role.id, skillId.trim(), {
        skill_id: skillId.trim(),
        importance,
        weight: w,
        minimum_readiness: min,
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-readiness-roles'] })
      setSkillId('')
      setMinimumReadiness('')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async ({ roleId, skillId: sid }: { roleId: string; skillId: string }) =>
      deleteAdminRoleRequirement(roleId, sid),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-readiness-roles'] }),
  })

  if (isLoading) return <LoadingState label="Loading role skill requirements" />
  if (error) return <ErrorState message="Could not load admin readiness config." />

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-[var(--color-text)]">Readiness Config</h1>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          Manage role skill requirements, importance, and weights. No student readiness data is shown
          here.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader title="Roles" />
          <ul className="space-y-1 text-sm">
            {(data ?? []).map((entry) => (
              <li key={entry.role.id}>
                <button
                  type="button"
                  className={`w-full rounded-md px-2 py-1.5 text-left hover:bg-[var(--color-surface-muted)] ${
                    (selected?.role.id ?? '') === entry.role.id ? 'bg-[var(--color-surface-muted)] font-medium' : ''
                  }`}
                  onClick={() => setSelectedRoleId(entry.role.id)}
                >
                  {entry.role.name}
                  <span className="ml-1 text-xs text-[var(--color-text-muted)]">
                    ({entry.requirements.length})
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </Card>

        <div className="space-y-4 lg:col-span-2">
          {selected && (
            <>
              <Card>
                <CardHeader
                  title={`${selected.role.name} requirements`}
                  description="Preview of weighted skills used in role readiness formulas"
                />
                {selected.requirements.length === 0 ? (
                  <p className="text-sm text-[var(--color-text-muted)]">No requirements seeded yet.</p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                      <thead>
                        <tr className="border-b border-[var(--color-border)] text-[var(--color-text-muted)]">
                          <th className="py-2 pr-3">Skill</th>
                          <th className="py-2 pr-3">Importance</th>
                          <th className="py-2 pr-3">Weight</th>
                          <th className="py-2 pr-3">Min readiness</th>
                          <th className="py-2">Source</th>
                          <th className="py-2" />
                        </tr>
                      </thead>
                      <tbody>
                        {selected.requirements.map((req) => (
                          <tr key={req.id} className="border-b border-[var(--color-border)]">
                            <td className="py-2 pr-3">{req.skill_name}</td>
                            <td className="py-2 pr-3 capitalize">{req.importance.replace('_', ' ')}</td>
                            <td className="py-2 pr-3">{req.weight}</td>
                            <td className="py-2 pr-3">{req.minimum_readiness ?? '—'}</td>
                            <td className="py-2 pr-3">{req.source}</td>
                            <td className="py-2">
                              <Button
                                size="sm"
                                variant="secondary"
                                onClick={() =>
                                  deleteMutation.mutate({
                                    roleId: selected.role.id,
                                    skillId: req.skill_id,
                                  })
                                }
                              >
                                Remove
                              </Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </Card>

              <Card>
                <CardHeader title="Add or update requirement" />
                <form
                  className="grid gap-3 sm:grid-cols-2"
                  onSubmit={(e) => {
                    e.preventDefault()
                    saveMutation.mutate()
                  }}
                >
                  <label className="text-sm sm:col-span-2">
                    Skill ID (UUID from skills table)
                    <input
                      className={inputClass}
                      value={skillId}
                      onChange={(e) => setSkillId(e.target.value)}
                      placeholder="skill uuid"
                      required
                    />
                  </label>
                  <label className="text-sm">
                    Importance
                    <select
                      className={inputClass}
                      value={importance}
                      onChange={(e) =>
                        setImportance(e.target.value as (typeof IMPORTANCE_OPTIONS)[number])
                      }
                    >
                      {IMPORTANCE_OPTIONS.map((opt) => (
                        <option key={opt} value={opt}>
                          {opt.replace('_', ' ')}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="text-sm">
                    Weight
                    <input
                      className={inputClass}
                      type="number"
                      min={0}
                      step={0.1}
                      value={weight}
                      onChange={(e) => setWeight(e.target.value)}
                      required
                    />
                  </label>
                  <label className="text-sm sm:col-span-2">
                    Minimum readiness (optional, 0–100)
                    <input
                      className={inputClass}
                      type="number"
                      min={0}
                      max={100}
                      value={minimumReadiness}
                      onChange={(e) => setMinimumReadiness(e.target.value)}
                    />
                  </label>
                  <div className="sm:col-span-2">
                    <Button type="submit" disabled={saveMutation.isPending}>
                      Save requirement
                    </Button>
                  </div>
                </form>
                {saveMutation.isError && (
                  <p className="mt-2 text-sm text-red-600">Could not save requirement.</p>
                )}
                {saveMutation.isSuccess && <SuccessState title="Requirement saved" />}
              </Card>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
