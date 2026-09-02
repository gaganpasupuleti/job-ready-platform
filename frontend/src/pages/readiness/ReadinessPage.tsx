import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
import { ErrorState, LoadingState } from '@/components/practice-workspace/PracticeWorkspace'
import { fetchReadiness, refreshReadiness } from '@/services/readinessService'

export function ReadinessPage() {
  const [showWhy, setShowWhy] = useState(false)
  const queryClient = useQueryClient()
  const { data, isLoading, error } = useQuery({ queryKey: ['readiness'], queryFn: fetchReadiness })
  const refresh = useMutation({
    mutationFn: refreshReadiness,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['readiness'] }),
  })

  if (isLoading) return <LoadingState label="Loading readiness" />
  if (error || !data) return <ErrorState message="Could not load readiness profile." />

  const scoreLabel =
    data.has_minimum_evidence && data.score != null
      ? `${Math.round(data.score)}%`
      : 'Building your profile'

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-lg font-semibold text-[var(--color-text)]">Job Readiness</h1>
          <p className="mt-1 max-w-2xl text-sm text-[var(--color-text-muted)]">
            Readiness is based only on activity completed in this platform and is not a prediction of
            hiring outcomes.
          </p>
        </div>
        <Button variant="secondary" onClick={() => refresh.mutate()} disabled={refresh.isPending}>
          Refresh
        </Button>
      </div>

      <Card>
        <CardHeader
          title={data.target_role ? `Target Role: ${data.target_role.name}` : 'No target role selected'}
          description={data.message ?? undefined}
        />
        <div className="grid gap-4 sm:grid-cols-3">
          <div>
            <p className="text-3xl font-semibold text-[var(--color-text)]">{scoreLabel}</p>
            <p className="text-xs text-[var(--color-text-muted)]">Role readiness</p>
          </div>
          <div>
            <p className="text-lg font-medium capitalize text-[var(--color-text)]">
              {data.evidence_strength}
            </p>
            <p className="text-xs text-[var(--color-text-muted)]">Evidence strength</p>
          </div>
          <div>
            <p className="text-lg font-medium text-[var(--color-text)]">
              {data.core_coverage.covered} / {data.core_coverage.total}
            </p>
            <p className="text-xs text-[var(--color-text-muted)]">Core skill coverage</p>
          </div>
        </div>
        {!data.target_role && (
          <p className="mt-4 text-sm">
            <Link to="/jobs" className="text-[var(--color-accent)] hover:underline">
              Set your target role in Jobs preferences
            </Link>
          </p>
        )}
        <button
          type="button"
          className="mt-4 text-sm text-[var(--color-accent)] hover:underline"
          onClick={() => setShowWhy((v) => !v)}
        >
          {showWhy ? 'Hide' : 'Why this score?'}
        </button>
        {showWhy && data.why_breakdown.length > 0 && (
          <div className="mt-3 space-y-2 rounded-md border border-[var(--color-border)] p-3 text-sm">
            {data.why_breakdown.map((row) => (
              <div key={row.skill} className="flex flex-wrap justify-between gap-2">
                <span className="font-medium">{row.skill}</span>
                <span className="text-[var(--color-text-muted)]">
                  importance {row.importance} · effective {row.effective_score} · evidence{' '}
                  {row.evidence_strength}
                </span>
              </div>
            ))}
          </div>
        )}
      </Card>

      <div className="grid gap-4 lg:grid-cols-3">
        <SkillGroup title="Strong Skills" items={data.strong_skills} skills={data.skills} filter="strong" />
        <SkillGroup
          title="Developing"
          items={data.developing_skills}
          skills={data.skills}
          filter="developing"
        />
        <SkillGroup title="Missing Evidence" items={data.missing_skills} skills={data.skills} filter="missing" />
      </div>

      {data.recommended_actions.length > 0 && (
        <Card>
          <CardHeader title="Recommended Next" description="Deterministic actions based on your gaps" />
          <div className="space-y-3">
            {data.recommended_actions.map((action) => (
              <div
                key={action.href + action.title}
                className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-[var(--color-border)] p-3"
              >
                <div>
                  <p className="text-sm font-medium text-[var(--color-text)]">{action.title}</p>
                  <p className="text-xs text-[var(--color-text-muted)]">{action.reason}</p>
                </div>
                <Link to={action.href}>
                  <Button size="sm">Start</Button>
                </Link>
              </div>
            ))}
          </div>
        </Card>
      )}

      <p className="text-xs text-[var(--color-text-subtle)]">
        <Link to="/readiness/skills" className="hover:underline">
          View full skill profile
        </Link>
      </p>
    </div>
  )
}

function SkillGroup({
  title,
  items,
  skills,
  filter,
}: {
  title: string
  items: string[]
  skills: { skill_name?: string; readiness: number; status: string }[]
  filter: string
}) {
  const rows = skills.filter((s) => s.status === filter || items.includes(s.skill_name ?? ''))
  return (
    <Card>
      <CardHeader title={title} />
      {rows.length === 0 && items.length === 0 ? (
        <p className="text-sm text-[var(--color-text-muted)]">None yet</p>
      ) : (
        <ul className="space-y-2 text-sm">
          {(rows.length ? rows : items.map((name) => ({ skill_name: name, readiness: 0, status: filter }))).map(
            (s) => (
              <li key={s.skill_name} className="flex justify-between">
                <span>{s.skill_name}</span>
                <span className="text-[var(--color-text-muted)]">
                  {s.readiness > 0 ? `${Math.round(s.readiness)}%` : '—'}
                </span>
              </li>
            ),
          )}
        </ul>
      )}
    </Card>
  )
}
