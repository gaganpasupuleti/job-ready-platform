import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { Bookmark } from 'lucide-react'

import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { addedToJobReadyLabel, employerPostedLabel } from '@/lib/jobPortalDates'
import { humanLabel } from '@/lib/studentLabels'
import type { JobCard } from '@/types/job'

function formatExperience(min: number | null, max: number | null) {
  if (min === 0 && max === 0) return null
  if (min != null && max != null) return `${min}–${max} yrs`
  if (min != null) return `${min}+ yrs`
  if (max != null) return `Up to ${max} yrs`
  return null
}

function formatToken(value: string | null) {
  if (!value || value.toLowerCase() === 'unknown') return null
  return humanLabel(value)
}

export function JobCardView({
  job,
  action,
  onToggleSave,
  saving,
  compact = true,
}: {
  job: JobCard
  action?: ReactNode
  onToggleSave?: () => void
  saving?: boolean
  compact?: boolean
}) {
  const experience = formatExperience(job.experience_min_years, job.experience_max_years)
  const workMode = formatToken(job.work_mode)
  const badges = [
    job.location_text,
    job.experience_bucket,
    job.is_remote ? 'Remote' : null,
    workMode,
    experience,
    formatToken(job.employment_type),
  ].filter(Boolean) as string[]

  if (compact) {
    return (
      <article
        className="job-card-wrap job-card-wrap--compact"
        data-job-id={job.id}
        data-job-slug={job.slug}
      >
        <div className="job-card-compact-head">
          <div className="job-card-compact-main min-w-0">
            <Link to={`/jobs/${job.slug}`} className="job-card-compact-title">
              {job.title}
            </Link>
            <p className="job-card-compact-company">{job.company_name}</p>
          </div>
          {onToggleSave ? (
            <Button
              type="button"
              size="sm"
              variant={job.is_saved ? 'primary' : 'ghost'}
              onClick={onToggleSave}
              disabled={saving}
              aria-label={job.is_saved ? 'Remove from saved' : 'Save job'}
              className="job-card-save-btn"
            >
              <Bookmark className="h-3.5 w-3.5" fill={job.is_saved ? 'currentColor' : 'none'} />
            </Button>
          ) : null}
        </div>
        {badges.length > 0 ? (
          <div className="job-card-compact-badges">
            {badges.slice(0, 4).map((label, index) => (
              <Badge key={`${label}-${index}`}>{label}</Badge>
            ))}
          </div>
        ) : null}
        <p className="job-card-compact-dates">
          {addedToJobReadyLabel(job.first_seen_at)}
          <span aria-hidden="true"> · </span>
          {employerPostedLabel(job.posted_at)}
        </p>
        <div className="job-card-compact-foot">
          <Link to={`/jobs/${job.slug}`} className="job-card-details-link job-card-details-link--compact">
            View details
          </Link>
          {action}
        </div>
      </article>
    )
  }

  return (
    <article className="job-card-wrap" data-job-id={job.id} data-job-slug={job.slug}>
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <Link to={`/jobs/${job.slug}`} className="text-[15px] font-semibold leading-snug text-[var(--color-text)] hover:underline">
            {job.title}
          </Link>
          <p className="mt-0.5 text-[13px] text-[var(--color-text-muted)]">{job.company_name}</p>
        </div>
        {onToggleSave ? (
          <Button
            type="button"
            size="sm"
            variant={job.is_saved ? 'primary' : 'secondary'}
            onClick={onToggleSave}
            disabled={saving}
            aria-label={job.is_saved ? 'Remove from saved' : 'Save job'}
          >
            <Bookmark className="h-3.5 w-3.5" fill={job.is_saved ? 'currentColor' : 'none'} />
          </Button>
        ) : null}
      </div>
      <div className="flex flex-wrap gap-1">
        {badges.map((label, index) => (
          <Badge key={`${label}-${index}`}>{label}</Badge>
        ))}
      </div>
      <p className="text-xs text-[var(--color-text-muted)]">
        {addedToJobReadyLabel(job.first_seen_at)} · {employerPostedLabel(job.posted_at)}
      </p>
      <div className="mt-auto flex flex-wrap items-center gap-2 pt-1">
        <Link to={`/jobs/${job.slug}`} className="job-card-details-link">View details</Link>
        {action}
      </div>
    </article>
  )
}
