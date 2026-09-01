import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { Button } from '@/components/common/Button'
import {
  EmptyState,
  ErrorState,
  LoadingState,
  PracticeHeader,
} from '@/components/practice-workspace/PracticeWorkspace'
import { JobCardView } from '@/features/jobs/JobCard'
import { fetchSavedJobs, saveJob, unsaveJob } from '@/services/jobService'

export function JobsSavedPage() {
  const queryClient = useQueryClient()
  const { data, isLoading, error } = useQuery({
    queryKey: ['jobs-saved'],
    queryFn: fetchSavedJobs,
  })

  const toggleMutation = useMutation({
    mutationFn: async ({ jobId, isSaved }: { jobId: string; isSaved: boolean }) => {
      if (isSaved) await unsaveJob(jobId)
      else await saveJob(jobId)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs-saved'] })
      queryClient.invalidateQueries({ queryKey: ['jobs-summary'] })
    },
  })

  if (isLoading) return <LoadingState label="Loading saved jobs" />
  if (error) return <ErrorState message="Unable to load saved jobs." />

  return (
    <div className="space-y-6">
      <PracticeHeader backTo="/jobs" backLabel="Jobs hub" title="Saved jobs">
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          Roles you bookmarked for later review.
        </p>
      </PracticeHeader>

      {data && data.length > 0 ? (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {data.map((item) => (
            <JobCardView
              key={item.id}
              job={item.job}
              saving={toggleMutation.isPending}
              onToggleSave={() =>
                toggleMutation.mutate({ jobId: item.job.id, isSaved: item.job.is_saved })
              }
            />
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          <EmptyState
            title="No saved jobs yet"
            description="Save jobs from browse or detail pages to track them here."
          />
          <Link to="/jobs">
            <Button>Browse jobs</Button>
          </Link>
        </div>
      )}
    </div>
  )
}
