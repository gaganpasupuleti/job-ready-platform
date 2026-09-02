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
import { fetchRecommendedJobs } from '@/services/jobService'

export function JobsRecommendedPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['jobs-recommended'],
    queryFn: () => fetchRecommendedJobs(),
  })

  if (isLoading) return <LoadingState label="Loading relevant jobs" />
  if (error) return <ErrorState message="Unable to load relevant jobs." />

  return (
    <div className="space-y-6">
      <PracticeHeader backTo="/jobs" backLabel="Jobs hub" title="Relevant Jobs">
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          Recommended based on your target role and recorded skill evidence — requirement coverage
          only, not a hiring probability.
        </p>
      </PracticeHeader>

      {data && data.items.length > 0 ? (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {data.items.map((job) => (
            <JobCardView key={job.id} job={job} />
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          <EmptyState
            title="No relevant jobs yet"
            description="Update your job preferences or complete more practice to improve recommendations."
          />
          <Link to="/jobs">
            <Button>Browse all jobs</Button>
          </Link>
        </div>
      )}
    </div>
  )
}
