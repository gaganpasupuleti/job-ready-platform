import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
import {
  ErrorState,
  LoadingState,
  PracticeHeader,
  PracticeProgress,
} from '@/components/practice-workspace/PracticeWorkspace'
import { InterviewReviewForm } from '@/features/interviews/InterviewReviewForm'
import { InterviewSessionNavigator } from '@/features/interviews/InterviewSessionNavigator'
import {
  abandonInterviewSession,
  completeInterviewSession,
  fetchInterviewSession,
  fetchInterviewSessionQuestion,
  revealInterviewAnswer,
  saveInterviewNotes,
  submitInterviewReview,
} from '@/services/interviewService'
import type { InterviewConfidence, InterviewSelfRating } from '@/types/interview'

export function InterviewSessionPage() {
  const { sessionId = '' } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [questionNumber, setQuestionNumber] = useState(1)
  const [answerText, setAnswerText] = useState('')
  const [privateNotes, setPrivateNotes] = useState('')
  const [checkedIds, setCheckedIds] = useState<string[]>([])
  const [confidence, setConfidence] = useState<InterviewConfidence | null>(null)
  const [selfRating, setSelfRating] = useState<InterviewSelfRating | null>(null)
  const [needsReview, setNeedsReview] = useState(false)
  const [startedAt] = useState(() => Date.now())

  const sessionQuery = useQuery({
    queryKey: ['interview-session', sessionId],
    queryFn: () => fetchInterviewSession(sessionId),
    enabled: Boolean(sessionId),
  })

  useEffect(() => {
    if (sessionQuery.data?.session) {
      setQuestionNumber(sessionQuery.data.session.current_question_index + 1)
    }
  }, [sessionQuery.data?.session.id]) // eslint-disable-line react-hooks/exhaustive-deps

  const questionQuery = useQuery({
    queryKey: ['interview-session-question', sessionId, questionNumber],
    queryFn: () => fetchInterviewSessionQuestion(sessionId, questionNumber),
    enabled: Boolean(sessionId) && questionNumber > 0,
  })

  const question = questionQuery.data
  const session = sessionQuery.data?.session
  const navigator = sessionQuery.data?.navigator ?? []

  useEffect(() => {
    if (!question) return
    setAnswerText(question.answer_text ?? '')
    setPrivateNotes(question.private_notes ?? '')
    setCheckedIds(question.key_points_checked ?? [])
    setConfidence(question.confidence_level)
    setSelfRating(question.self_rating)
    setNeedsReview(question.needs_review)
  }, [question?.number, question?.question_id]) // eslint-disable-line react-hooks/exhaustive-deps

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['interview-session', sessionId] })
    queryClient.invalidateQueries({
      queryKey: ['interview-session-question', sessionId, questionNumber],
    })
  }

  const notesMutation = useMutation({
    mutationFn: () =>
      saveInterviewNotes(sessionId, questionNumber, {
        answer_text: answerText,
        private_notes: privateNotes,
      }),
    onSuccess: invalidate,
  })

  const revealMutation = useMutation({
    mutationFn: async () => {
      await saveInterviewNotes(sessionId, questionNumber, {
        answer_text: answerText,
        private_notes: privateNotes,
      })
      return revealInterviewAnswer(sessionId, questionNumber)
    },
    onSuccess: invalidate,
  })

  const reviewMutation = useMutation({
    mutationFn: () => {
      if (!confidence || !selfRating) {
        return Promise.reject(new Error('confidence and self-rating required'))
      }
      return submitInterviewReview(sessionId, questionNumber, {
        key_point_ids: checkedIds,
        confidence,
        self_rating: selfRating,
        needs_review: needsReview,
        time_spent_seconds: Math.floor((Date.now() - startedAt) / 1000),
      })
    },
    onSuccess: invalidate,
  })

  const completeMutation = useMutation({
    mutationFn: () => completeInterviewSession(sessionId),
    onSuccess: () => navigate(`/interviews/sessions/${sessionId}/results`),
  })

  const abandonMutation = useMutation({
    mutationFn: () => abandonInterviewSession(sessionId),
    onSuccess: () => navigate('/interviews'),
  })

  if (sessionQuery.isLoading) return <LoadingState label="Loading session" />
  if (sessionQuery.error || !session) {
    return <ErrorState message="Unable to load interview session." />
  }

  const reviewed = session.reviewed_count
  const progressPercent =
    session.question_count > 0 ? Math.round((reviewed / session.question_count) * 100) : 0
  const revealed = Boolean(question?.answer_revealed)
  const canReview = revealed && confidence && selfRating

  return (
    <div className="space-y-4">
      <PracticeHeader backTo="/interviews" backLabel="Interview hub" title={session.title}>
        <div className="mt-2 flex flex-wrap items-center gap-2">
          <Badge>{session.mode.replace('_', ' ')}</Badge>
          <Badge variant="accent">
            Q{questionNumber}/{session.question_count}
          </Badge>
          <PracticeProgress percent={progressPercent} label={`${reviewed} reviewed`} />
        </div>
      </PracticeHeader>

      <Card padding="sm">
        <InterviewSessionNavigator
          items={navigator.map((item) => ({
            ...item,
            current: item.number === questionNumber,
          }))}
          onSelect={setQuestionNumber}
        />
      </Card>

      {questionQuery.isLoading && <LoadingState label="Loading question" />}
      {questionQuery.error && <ErrorState message="Unable to load this question." />}

      {question && (
        <div className="grid gap-4 lg:grid-cols-2">
          <Card className="space-y-4">
            <div>
              <div className="mb-2 flex flex-wrap gap-1">
                <Badge>{question.difficulty}</Badge>
                <Badge>{question.question_type}</Badge>
                <Badge>{question.experience_level}</Badge>
                {question.skills.map((s) => (
                  <Badge key={s}>{s}</Badge>
                ))}
              </div>
              <h2 className="text-base font-semibold text-[var(--color-text)]">
                {question.question_text}
              </h2>
            </div>

            <div>
              <label
                htmlFor="answer-text"
                className="mb-1 block text-sm font-medium text-[var(--color-text)]"
              >
                Your answer notes
              </label>
              <textarea
                id="answer-text"
                rows={8}
                value={answerText}
                onChange={(e) => setAnswerText(e.target.value)}
                className="w-full rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)]"
                placeholder="Outline your answer here…"
              />
            </div>

            <div>
              <label
                htmlFor="private-notes"
                className="mb-1 block text-sm font-medium text-[var(--color-text)]"
              >
                Private notes
              </label>
              <textarea
                id="private-notes"
                rows={3}
                value={privateNotes}
                onChange={(e) => setPrivateNotes(e.target.value)}
                className="w-full rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)]"
                placeholder="Reminders only you see…"
              />
            </div>

            <div className="flex flex-wrap gap-2">
              <Button
                size="sm"
                disabled={notesMutation.isPending}
                onClick={() => notesMutation.mutate()}
              >
                Save notes
              </Button>
              {!revealed && (
                <Button
                  variant="primary"
                  size="sm"
                  disabled={revealMutation.isPending}
                  onClick={() => revealMutation.mutate()}
                >
                  Review My Answer
                </Button>
              )}
            </div>
          </Card>

          <Card className="space-y-4">
            <CardHeader
              title="Self-review"
              description={
                revealed
                  ? 'Compare your notes to the expected answer, then rate yourself.'
                  : 'Reveal the expected answer when you are ready to self-review.'
              }
            />

            {!revealed && (
              <p className="text-sm text-[var(--color-text-muted)]">
                Expected answer and key points stay hidden until you click Review My Answer.
              </p>
            )}

            {revealed && (
              <>
                {question.expected_answer && (
                  <div>
                    <p className="text-xs font-medium text-[var(--color-text-muted)]">
                      Expected answer
                    </p>
                    <p className="mt-1 whitespace-pre-wrap text-sm text-[var(--color-text)]">
                      {question.expected_answer}
                    </p>
                  </div>
                )}
                {question.explanation && (
                  <div>
                    <p className="text-xs font-medium text-[var(--color-text-muted)]">Explanation</p>
                    <p className="mt-1 whitespace-pre-wrap text-sm text-[var(--color-text)]">
                      {question.explanation}
                    </p>
                  </div>
                )}
                <InterviewReviewForm
                  keyPoints={question.key_points}
                  checkedIds={checkedIds}
                  confidence={confidence}
                  selfRating={selfRating}
                  needsReview={needsReview}
                  onToggleKeyPoint={(id) =>
                    setCheckedIds((prev) =>
                      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
                    )
                  }
                  onConfidenceChange={setConfidence}
                  onSelfRatingChange={setSelfRating}
                  onNeedsReviewChange={setNeedsReview}
                />
                <Button
                  variant="primary"
                  disabled={!canReview || reviewMutation.isPending}
                  onClick={() => reviewMutation.mutate()}
                >
                  Save self-review
                </Button>
                {reviewMutation.isError && (
                  <p className="text-sm text-red-700 dark:text-red-300">
                    Choose confidence and self-rating before saving.
                  </p>
                )}
              </>
            )}
          </Card>
        </div>
      )}

      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex gap-2">
          <Button
            size="sm"
            disabled={questionNumber <= 1}
            onClick={() => setQuestionNumber((n) => Math.max(1, n - 1))}
          >
            Previous
          </Button>
          <Button
            size="sm"
            disabled={questionNumber >= session.question_count}
            onClick={() => setQuestionNumber((n) => Math.min(session.question_count, n + 1))}
          >
            Next
          </Button>
        </div>
        <div className="flex gap-2">
          <Button
            size="sm"
            disabled={abandonMutation.isPending}
            onClick={() => abandonMutation.mutate()}
          >
            Abandon
          </Button>
          <Button
            variant="primary"
            size="sm"
            disabled={completeMutation.isPending}
            onClick={() => completeMutation.mutate()}
          >
            Complete session
          </Button>
        </div>
      </div>
    </div>
  )
}
