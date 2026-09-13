import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'

import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
import { JOBS_HOME, JOBS_ONBOARDING_KEY } from '@/components/navigation/navConfig'
import { ErrorState, LoadingState } from '@/components/practice-workspace/PracticeWorkspace'
import { fetchJobPreferences, updateJobPreferences } from '@/services/jobService'
import type { WorkMode } from '@/types/job'

const inputClass =
  'mt-1 w-full rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)]'

function clearOnboardingFlag() {
  sessionStorage.removeItem(JOBS_ONBOARDING_KEY)
}

export function JobsPreferencesPage() {
  const navigate = useNavigate()
  const { data, isLoading, error } = useQuery({
    queryKey: ['job-preferences'],
    queryFn: fetchJobPreferences,
  })
  const [role, setRole] = useState('')
  const [locations, setLocations] = useState('')
  const [remote, setRemote] = useState('')

  useEffect(() => {
    if (!data) return
    setRole(data.target_role_slug ?? '')
    setLocations((data.preferred_locations ?? []).join(', '))
    setRemote(data.remote_preference ?? '')
  }, [data])

  const save = useMutation({
    mutationFn: updateJobPreferences,
    onSuccess: () => {
      clearOnboardingFlag()
      navigate(JOBS_HOME, { replace: true })
    },
  })

  const submit = (event: React.FormEvent) => {
    event.preventDefault()
    const preferred = locations
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean)
    save.mutate({
      target_role_slug: role || null,
      preferred_locations: preferred,
      remote_preference: (remote || null) as WorkMode | null,
    })
  }

  if (isLoading) return <LoadingState label="Loading job preferences" />
  if (error || !data) return <ErrorState message="Unable to load job preferences." />

  return (
    <div className="module-page jobs-portal mx-auto max-w-xl space-y-5">
      <header className="module-heading">
        <div>
          <p className="eyebrow">Careers</p>
          <h1>Job preferences</h1>
          <p>Tell us the role you want. You can change this later from Jobs.</p>
        </div>
      </header>
      <Card>
        <CardHeader
          title="Target role"
          description="Used for relevant jobs. This is not a hiring score."
        />
        <form onSubmit={submit} className="space-y-4">
          <div>
            <label htmlFor="pref-role" className="text-xs text-[var(--color-text-muted)]">
              Role
            </label>
            <select
              id="pref-role"
              className={inputClass}
              value={role}
              onChange={(event) => setRole(event.target.value)}
            >
              <option value="">No target role yet</option>
              {data.roles.map((item) => (
                <option key={item.slug} value={item.slug}>
                  {item.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="pref-locations" className="text-xs text-[var(--color-text-muted)]">
              Preferred locations
            </label>
            <input
              id="pref-locations"
              className={inputClass}
              value={locations}
              onChange={(event) => setLocations(event.target.value)}
              placeholder="City or region, comma-separated"
            />
          </div>
          <div>
            <label htmlFor="pref-remote" className="text-xs text-[var(--color-text-muted)]">
              Work mode
            </label>
            <select
              id="pref-remote"
              className={inputClass}
              value={remote}
              onChange={(event) => setRemote(event.target.value)}
            >
              <option value="">No preference</option>
              <option value="remote">Remote</option>
              <option value="hybrid">Hybrid</option>
              <option value="onsite">Onsite</option>
            </select>
          </div>
          {save.isError && (
            <p className="text-xs text-[var(--color-danger)]" role="alert">
              Could not save preferences. Try again.
            </p>
          )}
          <div className="flex flex-wrap gap-2">
            <Button type="submit" variant="primary" disabled={save.isPending}>
              {save.isPending ? 'Saving...' : 'Save and browse jobs'}
            </Button>
            <Button
              type="button"
              variant="secondary"
              disabled={save.isPending}
              onClick={() =>
                save.mutate({
                  preferred_locations: locations
                    .split(',')
                    .map((item) => item.trim())
                    .filter(Boolean),
                })
              }
            >
              Browse jobs
            </Button>
          </div>
        </form>
      </Card>
    </div>
  )
}
