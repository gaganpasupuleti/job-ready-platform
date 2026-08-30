import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Bookmark, Flag } from 'lucide-react'

import { Button } from '@/components/common/Button'
import { Card } from '@/components/common/Card'
import { AnswerExplanation } from '@/features/practice/AnswerExplanation'
import { QuestionCard } from '@/features/practice/QuestionCard'
import { QuestionOption } from '@/features/practice/QuestionOption'
import { formatCountdown, useCountdown } from '@/hooks/useCountdown'
import {
  autosaveAnswer,
  completeSession,
  fetchSession,
  fetchSessionOverview,
  fetchSessionQuestion,
  submitAnswer,
  toggleBookmark,
} from '@/services/practiceService'
import type { AnswerFeedback } from '@/types/practice'

export function PracticeSessionPage() {
  const { sessionId = '' } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [questionNumber, setQuestionNumber] = useState(1)
  const [selectedOptionId, setSelectedOptionId] = useState<string | null>(null)
  const [markedForReview, setMarkedForReview] = useState(false)
  const [feedback, setFeedback] = useState<AnswerFeedback | null>(null)
  const [answered, setAnswered] = useState(false)
  const [startTime] = useState(Date.now())
  const autoSubmittedRef = useRef(false)

  const sessionQuery = useQuery({
    queryKey: ['practice-session', sessionId],
    queryFn: () => fetchSession(sessionId),
    enabled: Boolean(sessionId),
    refetchInterval: (query) => (query.state.data?.mode === 'exam' ? 15000 : false),
  })

  const navigatorQuery = useQuery({
    queryKey: ['practice-navigator', sessionId],
    queryFn: () => fetchSessionOverview(sessionId),
    enabled: Boolean(sessionId) && sessionQuery.data?.mode === 'exam',
  })

  const questionQuery = useQuery({
    queryKey: ['practice-question', sessionId, questionNumber],
    queryFn: () => fetchSessionQuestion(sessionId, questionNumber),
    enabled: Boolean(sessionId),
  })

  const session = sessionQuery.data
  const isExam = session?.mode === 'exam'
  const secondsLeft = useCountdown(session?.expires_at, session?.remaining_seconds)

  useEffect(() => {
    const data = questionQuery.data
    if (!data) return
    setSelectedOptionId(data.selected_option_ids?.[0] ?? null)
    setMarkedForReview(Boolean(data.marked_for_review))
    setFeedback(null)
    setAnswered(Boolean(data.answered))
  }, [questionNumber, questionQuery.data])

  useEffect(() => {
    if (!isExam || secondsLeft == null || secondsLeft > 0 || autoSubmittedRef.current) return
    autoSubmittedRef.current = true
    completeSession(sessionId).then(() => navigate(`/practice/sessions/${sessionId}/results`))
  }, [isExam, secondsLeft, sessionId, navigate])

  const answerMutation = useMutation({
    mutationFn: () =>
      submitAnswer(
        sessionId,
        questionNumber,
        selectedOptionId ? [selectedOptionId] : [],
        Math.floor((Date.now() - startTime) / 1000),
      ),
    onSuccess: (response) => {
      setAnswered(true)
      setFeedback(response.feedback ?? null)
      queryClient.invalidateQueries({ queryKey: ['practice-session', sessionId] })
      queryClient.invalidateQueries({ queryKey: ['practice-navigator', sessionId] })
    },
    onError: () => setFeedback(null),
  })

  const autosaveMutation = useMutation({
    mutationFn: (payload: { selectedOptionIds: string[]; markedForReview: boolean }) =>
      autosaveAnswer(
        sessionId,
        questionNumber,
        payload.selectedOptionIds,
        payload.markedForReview,
        Math.floor((Date.now() - startTime) / 1000),
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['practice-navigator', sessionId] })
    },
  })

  const completeMutation = useMutation({
    mutationFn: () => completeSession(sessionId),
    onSuccess: () => navigate(`/practice/sessions/${sessionId}/results`),
  })

  const bookmarkMutation = useMutation({
    mutationFn: () => toggleBookmark(questionQuery.data!.question.id),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ['practice-question', sessionId, questionNumber] }),
  })

  const handleSelectOption = (optionId: string) => {
    if (!isExam && answered) return
    setSelectedOptionId(optionId)
    if (isExam) {
      autosaveMutation.mutate({
        selectedOptionIds: [optionId],
        markedForReview: markedForReview,
      })
    }
  }

  const handleToggleReview = () => {
    const next = !markedForReview
    setMarkedForReview(next)
    if (isExam) {
      autosaveMutation.mutate({
        selectedOptionIds: selectedOptionId ? [selectedOptionId] : [],
        markedForReview: next,
      })
    }
  }

  if (sessionQuery.isLoading || questionQuery.isLoading) {
    return <p className="text-sm text-[var(--color-text-muted)]">Loading session...</p>
  }

  const data = questionQuery.data
  if (!session || !data) {
    return <p className="text-sm text-[var(--color-danger)]">Session not found.</p>
  }

  const isPractice = session.mode === 'practice'
  const canSubmit = !answered && selectedOptionId
  const isLast = questionNumber >= session.question_count

  return (
    <div className="mx-auto max-w-5xl space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-[var(--color-text-muted)]">
        <span>
          {session.mode} mode · {session.answered_count}/{session.question_count} answered
        </span>
        <div className="flex items-center gap-3">
          {isExam && secondsLeft != null && (
            <span
              className={`font-mono text-sm ${
                secondsLeft <= 60 ? 'text-[var(--color-danger)]' : 'text-[var(--color-text)]'
              }`}
            >
              Time left: {formatCountdown(secondsLeft)}
            </span>
          )}
          <span>{Math.round((questionNumber / session.question_count) * 100)}% complete</span>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1fr_220px]">
        <Card padding="lg">
          <QuestionCard
            question={data.question}
            questionNumber={data.question_number}
            totalQuestions={data.total_questions}
          />

          <div className="mt-4 space-y-2">
            {data.question.options.map((option) => {
              let variant: 'default' | 'correct' | 'incorrect' = 'default'
              if (feedback) {
                const match = feedback.options.find((item) => item.id === option.id)
                if (match?.is_correct) variant = 'correct'
                else if (selectedOptionId === option.id) variant = 'incorrect'
              }
              return (
                <QuestionOption
                  key={option.id}
                  id={option.id}
                  text={option.option_text}
                  selected={selectedOptionId === option.id}
                  disabled={!isExam && answered}
                  variant={variant}
                  onSelect={() => handleSelectOption(option.id)}
                />
              )
            })}
          </div>

          {feedback && isPractice && <AnswerExplanation feedback={feedback} />}

          {answerMutation.isError && (
            <p className="mt-3 text-sm text-[var(--color-danger)]">
              {answerMutation.error instanceof Error ? answerMutation.error.message : 'Could not submit answer.'}
            </p>
          )}
          <div className="mt-6 flex flex-wrap items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => bookmarkMutation.mutate()}
              disabled={bookmarkMutation.isPending}
            >
              <Bookmark className="h-4 w-4" />
              {data.bookmarked ? 'Bookmarked' : 'Bookmark'}
            </Button>
            {isExam && (
              <Button variant="ghost" size="sm" onClick={handleToggleReview}>
                <Flag className="h-4 w-4" />
                {markedForReview ? 'Marked for review' : 'Mark for review'}
              </Button>
            )}
            {!isExam && (
              <Button variant="ghost" size="sm" disabled title="Coming soon">
                <Flag className="h-4 w-4" />
                Report
              </Button>
            )}
          </div>

          <div className="mt-6 flex flex-wrap justify-between gap-2">
            <Button
              variant="secondary"
              disabled={questionNumber <= 1}
              onClick={() => setQuestionNumber((n) => n - 1)}
            >
              Previous
            </Button>

            <div className="flex gap-2">
              {selectedOptionId && (
                <Button
                  variant="ghost"
                  onClick={() => {
                    setSelectedOptionId(null)
                    if (isExam) {
                      autosaveMutation.mutate({ selectedOptionIds: [], markedForReview })
                    }
                  }}
                >
                  Clear Selection
                </Button>
              )}
              {isExam ? (
                <>
                  {!isLast && (
                    <Button variant="primary" onClick={() => setQuestionNumber((n) => n + 1)}>
                      Next
                    </Button>
                  )}
                  {isLast && (
                    <Button
                      variant="primary"
                      disabled={completeMutation.isPending}
                      onClick={() => {
                        if (window.confirm('Submit this exam? You cannot change answers after submitting.')) {
                          completeMutation.mutate()
                        }
                      }}
                    >
                      {completeMutation.isPending ? 'Submitting...' : 'Submit Exam'}
                    </Button>
                  )}
                </>
              ) : (
                <>
                  {!answered && (
                    <Button
                      variant="primary"
                      disabled={!canSubmit || answerMutation.isPending}
                      onClick={() => answerMutation.mutate()}
                    >
                      Submit Answer
                    </Button>
                  )}
                  {answered && !isLast && (
                    <Button variant="primary" onClick={() => setQuestionNumber((n) => n + 1)}>
                      Next
                    </Button>
                  )}
                  {answered && isLast && (
                    <Button
                      variant="primary"
                      disabled={completeMutation.isPending}
                      onClick={() => completeMutation.mutate()}
                    >
                      Complete Session
                    </Button>
                  )}
                </>
              )}
            </div>
          </div>
        </Card>

        {isExam && (
          <Card padding="md" className="h-fit">
            <h3 className="mb-3 text-sm font-medium">Question navigator</h3>
            <div className="grid grid-cols-5 gap-2">
              {navigatorQuery.data?.questions.map((item) => {
                let cls =
                  'rounded border px-2 py-1 text-xs text-center cursor-pointer transition-colors'
                if (item.question_number === questionNumber) {
                  cls += ' border-[var(--color-accent)] bg-[var(--color-accent-muted)]'
                } else if (item.marked_for_review) {
                  cls += ' border-amber-400 bg-amber-50 dark:bg-amber-950'
                } else if (item.answered) {
                  cls += ' border-green-400 bg-green-50 dark:bg-green-950'
                } else {
                  cls += ' border-[var(--color-border)] hover:bg-[var(--color-surface-muted)]'
                }
                return (
                  <button
                    key={item.question_number}
                    type="button"
                    className={cls}
                    onClick={() => setQuestionNumber(item.question_number)}
                    aria-label={`Question ${item.question_number}${item.answered ? ', answered' : ', unanswered'}${item.question_number === questionNumber ? ', current' : ''}`}
                  >
                    {item.question_number}
                  </button>
                )
              })}
            </div>
            <div className="mt-4 space-y-1 text-xs text-[var(--color-text-muted)]">
              <p>
                <span className="inline-block h-2 w-2 rounded-full bg-green-400" /> Answered
              </p>
              <p>
                <span className="inline-block h-2 w-2 rounded-full bg-amber-400" /> Marked for review
              </p>
            </div>
          </Card>
        )}
      </div>
    </div>
  )
}
