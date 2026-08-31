import { Link, useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { Card } from '@/components/common/Card'
import {
  EmptyState,
  ErrorState,
  LoadingState,
  PracticeHeader,
} from '@/components/practice-workspace/PracticeWorkspace'
import {
  createInterviewSession,
  fetchInterviewReviewQueue,
  markInterviewQuestionReviewed,
} from '@/services/interviewService'

export function InterviewReviewPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { data, isLoading, error } = useQuery({
    queryKey: ['interview-review-queue'],
    queryFn: fetchInterviewReviewQueue,
  })

  const markMutation = useMutation({
    mutationFn: markInterviewQuestionReviewed,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['interview-review-queue'] }),
  })

  const retryMutation = useMutation({
    mutationFn: (questionIds: string[]) =>
      createInterviewSession({
        mode: 'rapid_review',
        source_type: 'retry_review',
        question_ids: questionIds,
        question_count: questionIds.length,
      }),
    onSuccess: (detail) => navigate(`/interviews/sessions/${detail.session.id}`),
  })

  return (
    <div className="space-y-6">
      <PracticeHeader backTo="/interviews" backLabel="Interview hub" title="Needs review">
        <p className="text-sm text-[var(--color-text-muted)]">
          Questions you flagged or rated as needing another pass.
        </p>
      </PracticeHeader>

      {isLoading && <LoadingState label="Loading review queue" />}
      {error && <ErrorState message="Unable to load review queue." />}

      {!isLoading && !error && (
        <>
          {(data?.length ?? 0) > 0 && (
            <Button
              variant="primary"
              disabled={retryMutation.isPending}
              onClick={() => retryMutation.mutate((data ?? []).map((item) => item.question_id))}
            >
              Retry all in rapid review
            </Button>
          )}

          {data?.length ? (
            <div className="space-y-3">
              {data.map((item) => (
                <Card key={item.question_id} padding="md">
                  <p className="font-medium text-[var(--color-text)]">{item.question_text}</p>
                  <div className="mt-2 flex flex-wrap gap-1">
                    {item.self_rating && <Badge>{item.self_rating.replace('_', ' ')}</Badge>}
                    {item.confidence_level && <Badge>{item.confidence_level} confidence</Badge>}
                    {item.skills.map((s) => (
                      <Badge key={s}>{s}</Badge>
                    ))}
                  </div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <Link to={`/interviews/session/new?question_ids=${item.question_id}`}>
                      <Button size="sm">Practice again</Button>
                    </Link>
                    <Button
                      size="sm"
                      disabled={markMutation.isPending}
                      onClick={() => markMutation.mutate(item.question_id)}
                    >
                      Mark reviewed
                    </Button>
                  </div>
                </Card>
              ))}
            </div>
          ) : (
            <EmptyState title="Queue empty" description="Nothing flagged for review right now." />
          )}
        </>
      )}
    </div>
  )
}
