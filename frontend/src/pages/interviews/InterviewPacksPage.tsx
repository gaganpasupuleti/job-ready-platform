import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Button } from '@/components/common/Button'
import {
  EmptyState,
  ErrorState,
  LoadingState,
  PracticeHeader,
} from '@/components/practice-workspace/PracticeWorkspace'
import { InterviewPackCard } from '@/features/interviews/InterviewPackCard'
import { fetchInterviewPacks } from '@/services/interviewService'

export function InterviewPacksPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['interview-packs'],
    queryFn: fetchInterviewPacks,
  })

  return (
    <div className="space-y-6">
      <PracticeHeader backTo="/interviews" backLabel="Interview hub" title="Interview packs">
        <p className="text-sm text-[var(--color-text-muted)]">
          Curated question sets for study, mock, and rapid review.
        </p>
      </PracticeHeader>

      {isLoading && <LoadingState label="Loading packs" />}
      {error && <ErrorState message="Unable to load interview packs." />}

      {!isLoading && !error && (
        <>
          {data?.length ? (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {data.map((pack) => (
                <InterviewPackCard
                  key={pack.id}
                  pack={pack}
                  action={
                    <Link to={`/interviews/packs/${pack.slug}`}>
                      <Button size="sm">Open pack</Button>
                    </Link>
                  }
                />
              ))}
            </div>
          ) : (
            <EmptyState title="No packs available" description="Check back after content review." />
          )}
        </>
      )}
    </div>
  )
}
