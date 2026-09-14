import { Link, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useEffect, useMemo, useState } from 'react'

import { Button } from '@/components/common/Button'
import {
  EmptyState,
  ErrorState,
  LoadingState,
} from '@/components/practice-workspace/PracticeWorkspace'
import { CatalogSelect } from '@/features/jobs/CatalogSelect'
import { JobCardView } from '@/features/jobs/JobCard'
import { useAuth } from '@/hooks/useAuth'
import { fetchJobFamilyCounts, fetchJobFilterOptions, fetchJobs, fetchJobsSummary } from '@/services/jobService'

const inputClass =
  'rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)]'

function param(searchParams: URLSearchParams, key: string) {
  const value = searchParams.get(key)?.trim()
  return value || undefined
}

export function JobsHubPage() {
  const { user } = useAuth()
  const uid = user?.id
  const [searchParams, setSearchParams] = useSearchParams()
  const [q, setQ] = useState(searchParams.get('q') ?? '')
  const [skill, setSkill] = useState(searchParams.get('skill') ?? '')
  const [locationQuery, setLocationQuery] = useState('')
  const [companyQuery, setCompanyQuery] = useState('')
  const [showAllFamilies, setShowAllFamilies] = useState(false)

  const page = Number(searchParams.get('page') ?? '1') || 1
  const sort = searchParams.get('sort') ?? 'newest'
  const family = param(searchParams, 'role_family')
  const location = param(searchParams, 'location')
  const company = param(searchParams, 'company')
  const experience = param(searchParams, 'experience_bucket')
  const role = param(searchParams, 'role')

  useEffect(() => {
    setQ(searchParams.get('q') ?? '')
    setSkill(searchParams.get('skill') ?? '')
  }, [searchParams])

  const applied = {
    q: param(searchParams, 'q'),
    skill: param(searchParams, 'skill'),
    company,
    location,
    role_family: family,
    experience_bucket: experience,
    role,
    sort,
    page,
    limit: 20,
  }
  const countFilters = {
    q: applied.q,
    skill: applied.skill,
    company,
    location,
    experience_bucket: experience,
    role,
  }

  const { data: summary } = useQuery({
    queryKey: ['jobs-summary', uid],
    queryFn: fetchJobsSummary,
    enabled: Boolean(uid),
  })

  const families = useQuery({
    queryKey: ['job-family-counts', uid, countFilters],
    queryFn: () => fetchJobFamilyCounts(countFilters),
    enabled: Boolean(uid),
  })

  const options = useQuery({
    queryKey: ['job-filter-options', uid, locationQuery, companyQuery, location, company],
    queryFn: () =>
      fetchJobFilterOptions({
        location_q: locationQuery || undefined,
        company_q: companyQuery || undefined,
        location,
        company,
      }),
    enabled: Boolean(uid),
  })

  const { data, isLoading, error } = useQuery({
    queryKey: ['jobs', uid, applied],
    queryFn: () => fetchJobs(applied),
    enabled: Boolean(uid),
  })

  const pills = useMemo(() => {
    const rows = families.data?.families ?? []
    if (!family) return rows
    return [...rows].sort((left, right) => Number(right.id === family) - Number(left.id === family))
  }, [families.data, family])

  const writeParams = (patch: Record<string, string | undefined>, resetPage = true) => {
    const next = new URLSearchParams(searchParams)
    for (const [key, value] of Object.entries(patch)) {
      if (value) next.set(key, value)
      else next.delete(key)
    }
    if (resetPage) next.set('page', '1')
    if ((next.get('sort') ?? 'newest') === 'newest') next.delete('sort')
    setSearchParams(next)
  }

  const applyFilters = () => {
    writeParams({
      q: q.trim() || undefined,
      skill: skill.trim() || undefined,
    })
  }

  const clearFilters = () => {
    setQ('')
    setSkill('')
    setLocationQuery('')
    setCompanyQuery('')
    const next = new URLSearchParams()
    if (sort !== 'newest') next.set('sort', sort)
    next.set('page', '1')
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
        <Link to="/jobs/preferences">Preferences</Link>
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

      <section className="jobs-family-panel" aria-label="Job families">
        {families.isLoading ? (
          <p className="jobs-family-status" role="status">
            Loading role counts
          </p>
        ) : families.isError ? (
          <p className="jobs-family-status" role="alert">
            Unable to load role counts
          </p>
        ) : (
          <div className={showAllFamilies ? 'jobs-family-pills' : 'jobs-family-pills is-collapsed'}>
            <button
              type="button"
              className="jobs-family-pill"
              aria-pressed={!family}
              onClick={() => writeParams({ role_family: undefined })}
            >
              <span>All jobs</span>
              <span className="jobs-family-count">{families.data?.all ?? ''}</span>
            </button>
            {pills.map((item) => (
              <button
                key={item.id}
                type="button"
                className="jobs-family-pill"
                aria-pressed={family === item.id}
                onClick={() => writeParams({ role_family: family === item.id ? undefined : item.id })}
              >
                <span>{item.label}</span>
                <span className="jobs-family-count">{item.count}</span>
              </button>
            ))}
          </div>
        )}
        {!families.isLoading && !families.isError && (
          <button
            type="button"
            className="jobs-family-toggle"
            aria-expanded={showAllFamilies}
            onClick={() => setShowAllFamilies((current) => !current)}
          >
            {showAllFamilies ? 'Show fewer' : 'Show all roles'}
          </button>
        )}
      </section>

      <div className="jobs-filter-bar">
        <input
          className={inputClass}
          placeholder="Keywords"
          value={q}
          onChange={(event) => setQ(event.target.value)}
          aria-label="Keywords"
          onKeyDown={(event) => {
            if (event.key === 'Enter') applyFilters()
          }}
        />
        <input
          className={inputClass}
          placeholder="Skill"
          value={skill}
          onChange={(event) => setSkill(event.target.value)}
          aria-label="Skill"
          onKeyDown={(event) => {
            if (event.key === 'Enter') applyFilters()
          }}
        />
        <CatalogSelect
          label="Location"
          value={location ?? ''}
          options={options.data?.locations ?? []}
          loading={options.isLoading}
          error={options.isError}
          onQueryChange={setLocationQuery}
          onChange={(next) => writeParams({ location: next || undefined })}
        />
        <CatalogSelect
          label="Company"
          value={company ?? ''}
          options={options.data?.companies ?? []}
          loading={options.isLoading}
          error={options.isError}
          onQueryChange={setCompanyQuery}
          onChange={(next) => writeParams({ company: next || undefined })}
        />
        <select
          className={inputClass}
          value={experience ?? ''}
          aria-label="Experience"
          onChange={(event) => writeParams({ experience_bucket: event.target.value || undefined })}
        >
          <option value="">Any experience</option>
          {(experience && !(options.data?.experience_buckets ?? []).includes(experience)
            ? [experience, ...(options.data?.experience_buckets ?? [])]
            : (options.data?.experience_buckets ?? [])
          ).map((bucket) => (
            <option key={bucket} value={bucket}>
              {bucket}
            </option>
          ))}
        </select>
        <select
          className={inputClass}
          value={sort}
          aria-label="Sort jobs"
          onChange={(event) => writeParams({ sort: event.target.value }, false)}
        >
          <option value="newest">Newest</option>
          <option value="oldest">Oldest</option>
          <option value="company">Company</option>
        </select>
        <Button type="button" variant="primary" onClick={applyFilters}>
          Search
        </Button>
        <Button type="button" variant="secondary" onClick={clearFilters}>
          Clear filters
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
              <Button type="button" size="sm" disabled={page <= 1} onClick={() => writeParams({ page: String(page - 1) }, false)}>
                Previous
              </Button>
              <span className="text-sm text-[var(--color-text-muted)]">
                Page {page} of {totalPages}
              </span>
              <Button
                type="button"
                size="sm"
                disabled={page >= totalPages}
                onClick={() => writeParams({ page: String(page + 1) }, false)}
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
