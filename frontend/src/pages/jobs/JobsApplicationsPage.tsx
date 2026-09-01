import { Link } from 'react-router-dom'
import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Card, CardHeader } from '@/components/common/Card'
import {
  EmptyState,
  ErrorState,
  LoadingState,
  PracticeHeader,
  PracticeTabs,
} from '@/components/practice-workspace/PracticeWorkspace'
import { ApplicationStatusBadge } from '@/features/jobs/ApplicationStatusBadge'
import { fetchApplications } from '@/services/jobService'
import type { ApplicationStatus, ApplicationSummary } from '@/types/job'

const PIPELINE_COLUMNS: ApplicationStatus[] = [
  'preparing',
  'applied',
  'screening',
  'assessment',
  'interview',
  'offer',
]

const CLOSED_STATUSES: ApplicationStatus[] = [
  'rejected',
  'withdrawn',
  'accepted',
  'ghosted',
]

function formatFollowUp(date: string | null) {
  if (!date) return null
  return new Date(date).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

function ApplicationCard({ app }: { app: ApplicationSummary }) {
  const followUp = formatFollowUp(app.next_follow_up_at)
  return (
    <Link
      to={`/jobs/applications/${app.id}`}
      className="block rounded-md border border-[var(--color-border)] p-3 hover:border-[var(--color-accent)]"
    >
      <p className="text-sm font-medium text-[var(--color-text)]">{app.job_title}</p>
      <p className="text-xs text-[var(--color-text-muted)]">{app.company_name}</p>
      <div className="mt-2 flex flex-wrap items-center gap-1">
        <ApplicationStatusBadge status={app.status} />
        {app.priority === 'high' && <Badge variant="warning">High priority</Badge>}
        {followUp && <Badge>Follow-up {followUp}</Badge>}
      </div>
    </Link>
  )
}

export function JobsApplicationsPage() {
  const [view, setView] = useState<'kanban' | 'list'>('kanban')
  const { data, isLoading, error } = useQuery({
    queryKey: ['applications'],
    queryFn: () => fetchApplications(),
  })

  const grouped = useMemo(() => {
    const map = new Map<ApplicationStatus, ApplicationSummary[]>()
    const allStatuses: ApplicationStatus[] = [...PIPELINE_COLUMNS, ...CLOSED_STATUSES, 'saved']
    for (const status of allStatuses) {
      map.set(status, [])
    }
    for (const app of data ?? []) {
      const list = map.get(app.status) ?? []
      list.push(app)
      map.set(app.status, list)
    }
    return map
  }, [data])

  if (isLoading) return <LoadingState label="Loading applications" />
  if (error) return <ErrorState message="Unable to load applications." />

  const total = data?.length ?? 0

  return (
    <div className="space-y-6">
      <PracticeHeader backTo="/jobs" backLabel="Jobs hub" title="Applications">
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          Track pipeline stages and follow-ups across your job search.
        </p>
      </PracticeHeader>

      <PracticeTabs
        tabs={[
          { id: 'kanban', label: 'Pipeline' },
          { id: 'list', label: 'All' },
        ]}
        value={view}
        onChange={(id) => setView(id as 'kanban' | 'list')}
      />

      {total === 0 ? (
        <EmptyState
          title="No applications yet"
          description="Mark jobs as preparing or applied from job detail pages."
        />
      ) : view === 'kanban' ? (
        <div className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {PIPELINE_COLUMNS.map((status) => {
              const items = grouped.get(status) ?? []
              return (
                <Card key={status} padding="sm">
                  <CardHeader
                    title={status.replace(/_/g, ' ')}
                    description={`${items.length} application${items.length !== 1 ? 's' : ''}`}
                  />
                  <div className="space-y-2">
                    {items.length ? (
                      items.map((app) => <ApplicationCard key={app.id} app={app} />)
                    ) : (
                      <p className="text-xs text-[var(--color-text-subtle)]">None</p>
                    )}
                  </div>
                </Card>
              )
            })}
          </div>
          {CLOSED_STATUSES.some((s) => (grouped.get(s)?.length ?? 0) > 0) && (
            <Card>
              <CardHeader title="Closed" />
              <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                {CLOSED_STATUSES.flatMap((status) =>
                  (grouped.get(status) ?? []).map((app) => (
                    <ApplicationCard key={app.id} app={app} />
                  )),
                )}
              </div>
            </Card>
          )}
        </div>
      ) : (
        <div className="space-y-2">
          {data!.map((app) => <ApplicationCard key={app.id} app={app} />)}
        </div>
      )}
    </div>
  )
}
