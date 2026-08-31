import { useQuery } from '@tanstack/react-query'

import {
  EmptyState,
  ErrorState,
  LoadingState,
  PracticeHeader,
} from '@/components/practice-workspace/PracticeWorkspace'
import { InterviewSessionRow } from '@/features/interviews/InterviewSessionRow'
import { fetchInterviewHistory } from '@/services/interviewService'

export function InterviewHistoryPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['interview-history'],
    queryFn: () => fetchInterviewHistory({ limit: 50 }),
  })

  return (
    <div className="space-y-6">
      <PracticeHeader backTo="/interviews" backLabel="Interview hub" title="Interview history">
        <p className="text-sm text-[var(--color-text-muted)]">Past study, mock, and rapid review sessions.</p>
      </PracticeHeader>

      {isLoading && <LoadingState label="Loading history" />}
      {error && <ErrorState message="Unable to load interview history." />}

      {!isLoading && !error && (
        <>
          {data?.length ? (
            <div className="space-y-2">
              {data.map((session) => (
                <InterviewSessionRow key={session.id} session={session} />
              ))}
            </div>
          ) : (
            <EmptyState title="No history yet" description="Complete a session to see it here." />
          )}
        </>
      )}
    </div>
  )
}
