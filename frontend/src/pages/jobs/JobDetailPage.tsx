import { Link, useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
import {
  ErrorState,
  LoadingState,
  PracticeHeader,
  SuccessState,
} from '@/components/practice-workspace/PracticeWorkspace'
import { ApplicationStatusBadge } from '@/features/jobs/ApplicationStatusBadge'
import {
  fetchJob,
  markJobApplied,
  saveJob,
  startJobPreparing,
  unsaveJob,
} from '@/services/jobService'

function formatSalary(min: string | null, max: string | null, currency: string | null) {
  if (!min && !max) return null
  const cur = currency ?? 'USD'
  if (min && max) return `${cur} ${min} – ${max}`
  if (min) return `${cur} ${min}+`
  return `Up to ${cur} ${max}`
}

export function JobDetailPage() {
  const { jobId } = useParams<{ jobId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data, isLoading, error } = useQuery({
    queryKey: ['job', jobId],
    queryFn: () => fetchJob(jobId!),
    enabled: Boolean(jobId),
  })

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['job', jobId] })
    queryClient.invalidateQueries({ queryKey: ['jobs'] })
    queryClient.invalidateQueries({ queryKey: ['jobs-summary'] })
    queryClient.invalidateQueries({ queryKey: ['jobs-saved'] })
    queryClient.invalidateQueries({ queryKey: ['applications'] })
  }

  const saveMutation = useMutation({
    mutationFn: async (isSaved: boolean) => {
      if (isSaved) await unsaveJob(data!.id)
      else await saveJob(data!.id)
    },
    onSuccess: invalidate,
  })

  const prepareMutation = useMutation({
    mutationFn: () => startJobPreparing(data!.id),
    onSuccess: (app) => {
      invalidate()
      navigate(`/jobs/applications/${app.id}`)
    },
  })

  const applyMutation = useMutation({
    mutationFn: () => markJobApplied(data!.id),
    onSuccess: (app) => {
      invalidate()
      navigate(`/jobs/applications/${app.id}`)
    },
  })

  if (isLoading) return <LoadingState label="Loading job" />
  if (error || !data) return <ErrorState message="Unable to load this job." />

  const salary = formatSalary(data.salary_min, data.salary_max, data.salary_currency)
  const applyUrl = data.apply_url || data.source_url

  return (
    <div className="space-y-6">
      <PracticeHeader backTo="/jobs" backLabel="Jobs hub" title={data.title}>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">{data.company_name}</p>
        <div className="mt-2 flex flex-wrap gap-2">
          {data.application_status && (
            <ApplicationStatusBadge status={data.application_status} />
          )}
          {data.location_text && <Badge>{data.location_text}</Badge>}
          {data.is_remote && <Badge variant="accent">Remote</Badge>}
          {data.work_mode && <Badge>{data.work_mode.replace(/_/g, ' ')}</Badge>}
          {salary && <Badge>{salary}</Badge>}
        </div>
      </PracticeHeader>

      <div className="flex flex-wrap gap-2">
        <Button
          type="button"
          variant={data.is_saved ? 'primary' : 'secondary'}
          onClick={() => saveMutation.mutate(data.is_saved)}
          disabled={saveMutation.isPending}
        >
          {data.is_saved ? 'Saved' : 'Save job'}
        </Button>
        {!data.application_id && (
          <Button
            type="button"
            onClick={() => prepareMutation.mutate()}
            disabled={prepareMutation.isPending}
          >
            Start preparing
          </Button>
        )}
        {data.application_id ? (
          <Link to={`/jobs/applications/${data.application_id}`}>
            <Button variant="primary">View application</Button>
          </Link>
        ) : (
          <Button
            type="button"
            variant="primary"
            onClick={() => applyMutation.mutate()}
            disabled={applyMutation.isPending}
          >
            Mark applied
          </Button>
        )}
        {applyUrl && (
          <a href={applyUrl} target="_blank" rel="noopener noreferrer">
            <Button type="button">Apply externally</Button>
          </a>
        )}
        {data.company_prep_url && (
          <Link to={data.company_prep_url}>
            <Button>Company prep</Button>
          </Link>
        )}
        {data.interview_prep_url && (
          <Link to={data.interview_prep_url}>
            <Button>Interview prep</Button>
          </Link>
        )}
      </div>

      {(prepareMutation.isSuccess || applyMutation.isSuccess) && (
        <SuccessState title="Application updated" />
      )}

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="space-y-4 lg:col-span-2">
          <Card>
            <CardHeader title="Description" />
            <div className="prose prose-sm max-w-none text-sm text-[var(--color-text)] whitespace-pre-wrap">
              {data.description}
            </div>
          </Card>
          {data.requirements_text && (
            <Card>
              <CardHeader title="Requirements" />
              <p className="text-sm whitespace-pre-wrap text-[var(--color-text)]">
                {data.requirements_text}
              </p>
            </Card>
          )}
          {data.responsibilities_text && (
            <Card>
              <CardHeader title="Responsibilities" />
              <p className="text-sm whitespace-pre-wrap text-[var(--color-text)]">
                {data.responsibilities_text}
              </p>
            </Card>
          )}
        </div>

        <div className="space-y-4">
          {data.skills.length > 0 && (
            <Card>
              <CardHeader title="Skills" />
              <div className="flex flex-wrap gap-1">
                {data.skills.map((s) => (
                  <Badge key={s.id} variant={s.importance === 'required' ? 'accent' : 'default'}>
                    {s.name}
                  </Badge>
                ))}
              </div>
            </Card>
          )}
          {data.roles.length > 0 && (
            <Card>
              <CardHeader title="Roles" />
              <div className="flex flex-wrap gap-1">
                {data.roles.map((r) => (
                  <Badge key={r.id}>{r.name}</Badge>
                ))}
              </div>
            </Card>
          )}
          {data.practice_links.length > 0 && (
            <Card>
              <CardHeader title="Practice links" />
              <ul className="space-y-2 text-sm">
                {data.practice_links.map((link) => (
                  <li key={link.path}>
                    <Link to={link.path} className="text-[var(--color-accent)] hover:underline">
                      {link.label}
                    </Link>
                    {link.reason && (
                      <p className="text-xs text-[var(--color-text-muted)]">{link.reason}</p>
                    )}
                  </li>
                ))}
              </ul>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
