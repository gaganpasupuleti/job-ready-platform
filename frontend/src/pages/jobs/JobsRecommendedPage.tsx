import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Button } from '@/components/common/Button'
import {
  EmptyState,
  ErrorState,
  LoadingState,
  PracticeHeader,
} from '@/components/practice-workspace/PracticeWorkspace'
import { JobCardView } from '@/features/jobs/JobCard'
import { jobsRecommendationCopy } from '@/lib/studentLabels'
import { fetchJobPreferences, fetchRecommendedJobs } from '@/services/jobService'

export function JobsRecommendedPage() {
  const jobs = useQuery({
    queryKey: ['jobs-recommended'],
    queryFn: () => fetchRecommendedJobs(),
  })
  const preferences = useQuery({
    queryKey: ['job-preferences'],
    queryFn: fetchJobPreferences,
  })

  if (jobs.isLoading || preferences.isLoading) return <LoadingState label="Loading relevant jobs" />
  if (jobs.error) return <ErrorState message="Unable to load relevant jobs." />

  const targetName = preferences.data?.target_role_name
  const configured = preferences.isSuccess && Boolean(preferences.data?.target_role_slug && targetName)
  const items = jobs.data?.items ?? []
  const scored = items.some((job) => job.requirement_coverage != null)
  const recommendation = jobsRecommendationCopy({
    preferencesError: preferences.isError,
    configured,
    targetName,
    scored,
    hasItems: items.length > 0,
  })

  return (
    <div className="space-y-5">
      <PracticeHeader backTo="/jobs" backLabel="Jobs" title="Relevant jobs" size="page">
        <p className="mt-1 max-w-2xl text-sm text-[var(--color-text-muted)]">{recommendation.summary}</p>
      </PracticeHeader>

      {recommendation.showPreferencesLink && (
        <p>
          <Link to="/jobs/preferences">
            <Button type="button">Set a target role</Button>
          </Link>
        </p>
      )}

      {items.length > 0 ? (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((job) => (
            <JobCardView key={job.id} job={job} />
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          <EmptyState
            title="No relevant jobs yet"
            description={
              configured
                ? 'Nothing in the current catalog matches this target role.'
                : 'Set a target role, or browse the full catalog.'
            }
          />
          <Link to="/jobs">
            <Button type="button" variant="secondary">
              Browse all jobs
            </Button>
          </Link>
        </div>
      )}
    </div>
  )
}
