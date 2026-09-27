import { Link, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'

import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
import {
  EmptyState,
  ErrorState,
  LoadingState,
} from '@/components/practice-workspace/PracticeWorkspace'
import { JobCardView } from '@/features/jobs/JobCard'
import { fetchJobFamilyCounts, fetchJobs, fetchJobsSummary } from '@/services/jobService'

const inputClass =
  'rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)]'

export function JobsHubPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [q, setQ] = useState(searchParams.get('q') ?? '')
  const [role, setRole] = useState(searchParams.get('role') ?? '')
  const [skill, setSkill] = useState(searchParams.get('skill') ?? '')
  const [company, setCompany] = useState(searchParams.get('company') ?? '')
  const page = Number(searchParams.get('page') ?? '1')
  const sort = searchParams.get('sort') ?? 'newest'
  const roleFamily = searchParams.get('role_family') ?? ''

  const filters = {
    q: searchParams.get('q') || undefined,
    role: searchParams.get('role') || undefined,
    skill: searchParams.get('skill') || undefined,
    company: searchParams.get('company') || undefined,
    role_family: roleFamily || undefined,
    sort,
    page,
    limit: 20,
  }

  const { data: summary } = useQuery({
    queryKey: ['jobs-summary'],
    queryFn: fetchJobsSummary,
  })

  const { data: families } = useQuery({
    queryKey: ['job-families', filters.q, filters.role, filters.skill, filters.company],
    queryFn: () =>
      fetchJobFamilyCounts({
        q: filters.q,
        role: filters.role,
        skill: filters.skill,
        company: filters.company,
      }),
  })

  const { data, isLoading, error } = useQuery({
    queryKey: ['jobs', filters],
    queryFn: () => fetchJobs(filters),
  })

  const applyFilters = () => {
    const next = new URLSearchParams()
    if (q.trim()) next.set('q', q.trim())
    if (role.trim()) next.set('role', role.trim())
    if (skill.trim()) next.set('skill', skill.trim())
    if (company.trim()) next.set('company', company.trim())
    if (roleFamily) next.set('role_family', roleFamily)
    if (sort !== 'newest') next.set('sort', sort)
    next.set('page', '1')
    setSearchParams(next)
  }

  const selectFamily = (familyId: string) => {
    const next = new URLSearchParams(searchParams)
    if (familyId) next.set('role_family', familyId)
    else next.delete('role_family')
    next.set('page', '1')
    setSearchParams(next)
  }

  const goToPage = (nextPage: number) => {
    const next = new URLSearchParams(searchParams)
    next.set('page', String(nextPage))
    setSearchParams(next)
  }

  if (isLoading) return <LoadingState label="Loading jobs" />
  if (error) return <ErrorState message="Unable to load jobs." />

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.limit)) : 1

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold text-[var(--color-text)]">Jobs</h1>
          <p className="mt-1 text-sm text-[var(--color-text-muted)]">
            Published listings only. A source row stays hidden until it has an explicit publish decision and a reviewed sync.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link to="/jobs/recommended">
            <Button>Relevant jobs</Button>
          </Link>
          <Link to="/jobs/saved">
            <Button>Saved</Button>
          </Link>
          <Link to="/jobs/applications">
            <Button variant="primary">Applications</Button>
          </Link>
        </div>
      </div>

      {summary && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Card padding="sm">
            <p className="text-xs text-[var(--color-text-muted)]">Saved</p>
            <p className="mt-1 text-2xl font-semibold text-[var(--color-text)]">
              {summary.saved_count}
            </p>
          </Card>
          <Card padding="sm">
            <p className="text-xs text-[var(--color-text-muted)]">Applications</p>
            <p className="mt-1 text-2xl font-semibold text-[var(--color-text)]">
              {summary.applications_total}
            </p>
            <p className="text-xs text-[var(--color-text-subtle)]">
              {summary.applied_count} applied · {summary.interview_count} interview
            </p>
          </Card>
          <Card padding="sm">
            <p className="text-xs text-[var(--color-text-muted)]">Offers</p>
            <p className="mt-1 text-2xl font-semibold text-[var(--color-text)]">
              {summary.offer_count}
            </p>
          </Card>
          <Card padding="sm">
            <p className="text-xs text-[var(--color-text-muted)]">Follow-ups</p>
            <p className="mt-1 text-2xl font-semibold text-[var(--color-text)]">
              {summary.follow_ups_due}
            </p>
            <p className="text-xs text-[var(--color-text-subtle)]">
              {summary.follow_ups_overdue} overdue · {summary.follow_ups_today} today
            </p>
          </Card>
        </div>
      )}

      {families && families.families.some((family) => family.count > 0) ? (
        <div className="flex gap-2 overflow-x-auto pb-1">
          <FamilyPill
            label={`All ${families.all}`}
            active={!roleFamily}
            onClick={() => selectFamily('')}
          />
          {families.families
            .filter((family) => family.count > 0)
            .map((family) => (
              <FamilyPill
                key={family.id}
                label={`${family.label} ${family.count}`}
                active={roleFamily === family.id}
                onClick={() => selectFamily(family.id)}
              />
            ))}
        </div>
      ) : null}

      <Card>
        <CardHeader title="Search & filter" />
        <div className="flex flex-wrap gap-2">
          <input
            className={inputClass}
            placeholder="Keywords"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          <input
            className={inputClass}
            placeholder="Role"
            value={role}
            onChange={(e) => setRole(e.target.value)}
          />
          <input
            className={inputClass}
            placeholder="Skill"
            value={skill}
            onChange={(e) => setSkill(e.target.value)}
          />
          <input
            className={inputClass}
            placeholder="Company"
            value={company}
            onChange={(e) => setCompany(e.target.value)}
          />
          <select
            className={inputClass}
            value={sort}
            onChange={(e) => {
              const next = new URLSearchParams(searchParams)
              next.set('sort', e.target.value)
              setSearchParams(next)
            }}
          >
            <option value="newest">Newest</option>
            <option value="oldest">Oldest</option>
            <option value="company">Company</option>
          </select>
          <Button type="button" variant="primary" onClick={applyFilters}>Search</Button>
        </div>
      </Card>

      {data && data.items.length > 0 ? (
        <>
          <p className="text-sm text-[var(--color-text-muted)]">
            {data.total} job{data.total !== 1 ? 's' : ''} found
          </p>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {data.items.map((job) => (
              <JobCardView key={job.id} job={job} />
            ))}
          </div>
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2">
              <Button
                type="button"
                size="sm"
                disabled={page <= 1}
                onClick={() => goToPage(page - 1)}
              >
                Previous
              </Button>
              <span className="text-sm text-[var(--color-text-muted)]">
                Page {page} of {totalPages}
              </span>
              <Button
                type="button"
                size="sm"
                disabled={page >= totalPages}
                onClick={() => goToPage(page + 1)}
              >
                Next
              </Button>
            </div>
          )}
        </>
      ) : (
        <EmptyState
          title={roleFamily || q || role || skill || company ? 'No published jobs match these filters' : 'No published jobs yet'}
          description="The catalog lists active jobs only. Source listings stay out until an admin records publish and the reviewed sync is applied."
        />
      )}
    </div>
  )
}

function FamilyPill({
  label,
  active,
  onClick,
}: {
  label: string
  active: boolean
  onClick: () => void
}) {
  return (
    <button
      type="button"
      className={`whitespace-nowrap rounded-full border px-3 py-1.5 text-xs ${
        active
          ? 'border-[var(--color-accent)] bg-[var(--color-accent-muted)] text-[var(--color-accent)]'
          : 'border-[var(--color-border)] text-[var(--color-text-muted)]'
      }`}
      onClick={onClick}
    >
      {label}
    </button>
  )
}
