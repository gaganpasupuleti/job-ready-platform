import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { Bookmark } from 'lucide-react'

import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { Card } from '@/components/common/Card'
import type { JobCard } from '@/types/job'

function formatExperience(min: number | null, max: number | null) {
  if (min != null && max != null) return `${min}–${max} yrs`
  if (min != null) return `${min}+ yrs`
  if (max != null) return `Up to ${max} yrs`
  return null
}

function formatWorkMode(mode: string | null) {
  if (!mode) return null
  return mode.replace(/_/g, ' ')
}

export function JobCardView({
  job,
  action,
  onToggleSave,
  saving,
}: {
  job: JobCard
  action?: ReactNode
  onToggleSave?: () => void
  saving?: boolean
}) {
  const experience = formatExperience(job.experience_min_years, job.experience_max_years)
  const workMode = formatWorkMode(job.work_mode)

  return (
    <Card padding="md" className="flex flex-col gap-3">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <Link
            to={`/jobs/${job.slug}`}
            className="font-medium text-[var(--color-text)] hover:underline"
          >
            {job.title}
          </Link>
          <p className="mt-0.5 text-sm text-[var(--color-text-muted)]">{job.company_name}</p>
        </div>
        {onToggleSave && (
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
        )}
      </div>

      <div className="flex flex-wrap gap-1">
        {job.is_sample && <Badge variant="accent">Sample</Badge>}
        {job.posted_at &&
          Date.now() - new Date(job.posted_at).getTime() < 7 * 24 * 60 * 60 * 1000 && (
            <Badge variant="accent">New</Badge>
          )}
        {job.location_text && <Badge>{job.location_text}</Badge>}
        {job.is_remote && <Badge variant="accent">Remote</Badge>}
        {workMode && workMode.toLowerCase() === 'hybrid' && <Badge>Hybrid</Badge>}
        {workMode && workMode.toLowerCase() !== 'hybrid' && <Badge>{workMode}</Badge>}
        {experience && <Badge>{experience}</Badge>}
        {job.employment_type && (
          <Badge>{job.employment_type.replace(/_/g, ' ')}</Badge>
        )}
      </div>

      {job.requirement_coverage != null && (
        <p className="text-sm font-medium text-[var(--color-accent)]">
          {Math.round(job.requirement_coverage)}% requirement coverage
          {job.missing_skill_count != null && job.missing_skill_count > 0
            ? ` · ${job.missing_skill_count} skills to develop`
            : ''}
        </p>
      )}
      {job.has_sufficient_mapping === false && (
        <p className="text-xs text-[var(--color-text-muted)]">Not enough mapped requirements</p>
      )}

      {job.top_skills.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {job.top_skills.slice(0, 5).map((skill) => (
            <Badge key={skill} variant="default">{skill}</Badge>
          ))}
        </div>
      )}

      {action}
    </Card>
  )
}
