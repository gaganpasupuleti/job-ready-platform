import { Link, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'

import { Button } from '@/components/common/Button'
import {
  EmptyState,
  ErrorState,
  LoadingState,
} from '@/components/practice-workspace/PracticeWorkspace'
import { JobCardView } from '@/features/jobs/JobCard'
import { useAuth } from '@/hooks/useAuth'
import { fetchJobs, fetchJobsSummary } from '@/services/jobService'

const inputClass =
  'rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)]'

export function JobsHubPage() {
  const { user } = useAuth()
  const uid = user?.id
  const [searchParams, setSearchParams] = useSearchParams()
  const [q, setQ] = useState(searchParams.get('q') ?? '')
  const [role, setRole] = useState(searchParams.get('role') ?? '')
  const [skill, setSkill] = useState(searchParams.get('skill') ?? '')
  const [company, setCompany] = useState(searchParams.get('company') ?? '')
  const page = Number(searchParams.get('page') ?? '1')
  const sort = searchParams.get('sort') ?? 'newest'

  const filters = {
    q: searchParams.get('q') || undefined,
    role: searchParams.get('role') || undefined,
    skill: searchParams.get('skill') || undefined,
    company: searchParams.get('company') || undefined,
    sort,
    page,
    limit: 20,
  }

  const { data: summary } = useQuery({
    queryKey: ['jobs-summary', uid],
    queryFn: fetchJobsSummary,
    enabled: Boolean(uid),
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
    if (sort !== 'newest') next.set('sort', sort)
    next.set('page', '1')
    setSearchParams(next)
  }

  const goToPage = (nextPage: number) => {
    const next = new URLSearchParams(searchParams)
    next.set('page', String(nextPage))
    setSearchParams(next)
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.limit)) : 1

  return (
    <div className="module-page jobs-portal">
      <header className="module-heading">
        <div>
          <p className="eyebrow">Careers</p>
          <h1>Jobs</h1>
          <p>Browse openings, save roles, and track applications — live listings only.</p>
        </div>
      </header>

      <nav className="jobs-tabs" aria-label="Jobs sections">
        <Link to="/jobs" className="active" aria-current="page">
          Browse
        </Link>
        <Link to="/jobs/recommended">Relevant</Link>
        <Link to="/jobs/saved">Saved{summary ? ` (${summary.saved_count})` : ''}</Link>
        <Link to="/jobs/applications">
          Applications{summary ? ` (${summary.applications_total})` : ''}
        </Link>
      </nav>

      {summary && (
        <div className="jobs-summary-strip">
          <article>
            <p>Saved</p>
            <strong>{summary.saved_count}</strong>
          </article>
          <article>
            <p>Applications</p>
            <strong>{summary.applications_total}</strong>
            <p>
              {summary.applied_count} applied · {summary.interview_count} interview
            </p>
          </article>
          <article>
            <p>Offers</p>
            <strong>{summary.offer_count}</strong>
          </article>
          <article>
            <p>Follow-ups due</p>
            <strong>{summary.follow_ups_due}</strong>
            <p>
              {summary.follow_ups_overdue} overdue · {summary.follow_ups_today} today
            </p>
          </article>
        </div>
      )}

      <div className="jobs-filter-bar">
        <input
          className={inputClass}
          placeholder="Keywords"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          aria-label="Keywords"
        />
        <input
          className={inputClass}
          placeholder="Role"
          value={role}
          onChange={(e) => setRole(e.target.value)}
          aria-label="Role"
        />
        <input
          className={inputClass}
          placeholder="Skill"
          value={skill}
          onChange={(e) => setSkill(e.target.value)}
          aria-label="Skill"
        />
        <input
          className={inputClass}
          placeholder="Company"
          value={company}
          onChange={(e) => setCompany(e.target.value)}
          aria-label="Company"
        />
        <select
          className={inputClass}
          value={sort}
          aria-label="Sort jobs"
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
        <Button type="button" variant="primary" onClick={applyFilters}>
          Search
        </Button>
      </div>

      {isLoading ? (
        <LoadingState label="Loading jobs" />
      ) : error ? (
        <ErrorState message="Unable to load jobs." />
      ) : data && data.items.length > 0 ? (
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
          title="No jobs match your filters"
          description="Try broader keywords or clear filters to see more openings."
        />
      )}
    </div>
  )
}

