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
  const [selectedOptionIds, setSelectedOptionIds] = useState<string[]>([])
  const [markedForReview, setMarkedForReview] = useState(false)
  const [feedback, setFeedback] = useState<AnswerFeedback | null>(null)
  const [answered, setAnswered] = useState(false)
  const [startTime] = useState(Date.now())
  const autoSubmittedRef = useRef(false)
  const timerArmedRef = useRef(false)
  const saveSeqRef = useRef(0)
  const pendingSaveRef = useRef<Promise<unknown> | null>(null)
  const selectedRef = useRef<string[]>([])
  const markedRef = useRef(false)
  const questionNumberRef = useRef(1)
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved'>('idle')
  const [confirmSubmit, setConfirmSubmit] = useState(false)

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
    if (session?.status === 'completed' && sessionId) {
      navigate(`/practice/sessions/${sessionId}/results`, { replace: true })
    }
  }, [session?.status, sessionId, navigate])

  useEffect(() => {
    selectedRef.current = selectedOptionIds
  }, [selectedOptionIds])
  useEffect(() => {
    markedRef.current = markedForReview
  }, [markedForReview])
  useEffect(() => {
    questionNumberRef.current = questionNumber
  }, [questionNumber])

  useEffect(() => {
    const data = questionQuery.data
    if (!data) return
    setSelectedOptionIds(data.selected_option_ids ?? [])
    setMarkedForReview(Boolean(data.marked_for_review))
    setFeedback(null)
    setAnswered(Boolean(data.answered))
  }, [questionNumber, questionQuery.data])

  const queueAutosave = (payload: {
    selectedOptionIds: string[]
    markedForReview: boolean
    questionNumber?: number
  }) => {
    const seq = ++saveSeqRef.current
    const qn = payload.questionNumber ?? questionNumberRef.current
    setSaveStatus('saving')
    const request = autosaveAnswer(
      sessionId,
      qn,
      payload.selectedOptionIds,
      payload.markedForReview,
      Math.floor((Date.now() - startTime) / 1000),
    )
      .then(() => {
        if (seq !== saveSeqRef.current) return
        setSaveStatus('saved')
        void queryClient.invalidateQueries({ queryKey: ['practice-navigator', sessionId] })
        void queryClient.invalidateQueries({ queryKey: ['practice-session', sessionId] })
      })
      .catch(() => {
        if (seq === saveSeqRef.current) setSaveStatus('idle')
      })
    pendingSaveRef.current = request
    return request
  }

  const flushAutosave = async () => {
    if (!isExam) return
    const settle = async (pending: Promise<unknown> | null) => {
      if (!pending) return
      await Promise.race([
        pending,
        new Promise<void>((resolve) => {
          window.setTimeout(resolve, 4000)
        }),
      ])
    }
    await settle(pendingSaveRef.current)
    await queueAutosave({
      selectedOptionIds: selectedRef.current,
      markedForReview: markedRef.current,
      questionNumber: questionNumberRef.current,
    })
    await settle(pendingSaveRef.current)
  }

  useEffect(() => {
    if (isExam && secondsLeft != null && secondsLeft > 0) {
      timerArmedRef.current = true
    }
  }, [isExam, secondsLeft])

  useEffect(() => {
    if (
      !isExam ||
      !session?.expires_at ||
      session.status !== 'active' ||
      !timerArmedRef.current ||
      secondsLeft == null ||
      secondsLeft > 0 ||
      autoSubmittedRef.current
    ) {
      return
    }
    autoSubmittedRef.current = true
    void (async () => {
      try {
        await flushAutosave()
      } catch {
        /* expire path still completes */
      }
      await completeSession(sessionId)
      navigate(`/practice/sessions/${sessionId}/results`)
    })()
    // eslint-disable-next-line react-hooks/exhaustive-deps -- flush uses latest refs
  }, [isExam, secondsLeft, sessionId, navigate, session?.expires_at, session?.status])

  const answerMutation = useMutation({
    mutationFn: () =>
      submitAnswer(
        sessionId,
        questionNumber,
        selectedOptionIds,
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

  const completeMutation = useMutation({
    mutationFn: async () => {
      try {
        await flushAutosave()
      } catch {
        /* still finalize with last known server autosaves */
      }
      return completeSession(sessionId)
    },
    onSuccess: () => navigate(`/practice/sessions/${sessionId}/results`),
  })

  const bookmarkMutation = useMutation({
    mutationFn: () => toggleBookmark(questionQuery.data!.question.id),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ['practice-question', sessionId, questionNumber] }),
  })

  const goToQuestion = async (next: number) => {
    if (isExam) await flushAutosave()
    setQuestionNumber(next)
  }

  const handleSelectOption = (optionId: string, multi: boolean) => {
    if (!isExam && answered) return
    setSelectedOptionIds((prev) => {
      const next = multi
        ? prev.includes(optionId)
          ? prev.filter((id) => id !== optionId)
          : [...prev, optionId]
        : [optionId]
      selectedRef.current = next
      if (isExam) {
        void queueAutosave({
          selectedOptionIds: next,
          markedForReview: markedRef.current,
        })
      }
      return next
    })
  }

  const handleToggleReview = () => {
    const next = !markedForReview
    setMarkedForReview(next)
    markedRef.current = next
    if (isExam) {
      void queueAutosave({
        selectedOptionIds: selectedRef.current,
        markedForReview: next,
      })
    }
  }

  if (sessionQuery.isLoading || questionQuery.isLoading) {
    return <p className="text-sm text-[var(--color-text-muted)]">Loading session...</p>
  }

  if (sessionQuery.isError || questionQuery.isError) {
    return (
      <p className="text-sm text-[var(--color-danger)]">
        Unable to load this session. It may have expired or been submitted — check Recent Practice.
      </p>
    )
  }

  const data = questionQuery.data
  if (!session || !data) {
    return <p className="text-sm text-[var(--color-danger)]">Session not found.</p>
  }

  const isPractice = session.mode === 'practice'
  const isMulti = data.question.question_type === 'multiple_choice'
  const canSubmit = !answered && selectedOptionIds.length > 0
  const isLast = questionNumber >= session.question_count
  const answeredCount = Math.min(session.answered_count ?? 0, session.question_count)
  const answeredPct = Math.round((answeredCount / Math.max(session.question_count, 1)) * 100)

  return (
    <div
      className={
        isExam
          ? 'mx-auto max-w-5xl space-y-3 px-1 py-2'
          : 'mx-auto max-w-5xl space-y-4 px-1 py-2'
      }
    >
      <div
        className={
          isExam
            ? 'sticky top-0 z-10 -mx-1 flex flex-wrap items-center justify-between gap-2 border-b border-[var(--color-border)] bg-[var(--color-surface)]/95 px-2 py-2 text-xs text-[var(--color-text-muted)] backdrop-blur'
            : 'flex flex-wrap items-center justify-between gap-2 text-xs text-[var(--color-text-muted)]'
        }
      >
        <span>
          {session.mode} mode · {answeredCount}/{session.question_count} answered
          {isMulti ? ' · select all that apply' : ''}
        </span>
        <div className="flex flex-wrap items-center gap-3">
          {isExam && secondsLeft != null && (
            <span
              className={`font-mono text-sm ${
                secondsLeft <= 60 ? 'text-[var(--color-danger)]' : 'text-[var(--color-text)]'
              }`}
            >
              Time left: {formatCountdown(secondsLeft)}
            </span>
          )}
          {isExam && saveStatus === 'saving' && (
            <span className="text-[var(--color-text-subtle)]" role="status">
              Saving…
            </span>
          )}
          {isExam && saveStatus === 'saved' && (
            <span className="text-[var(--color-text-subtle)]" role="status">
              Saved
            </span>
          )}
          <span>
            Question {questionNumber}/{session.question_count} · {answeredPct}% answered
          </span>
        </div>
      </div>

      <div className="grid gap-3 lg:grid-cols-[1fr_200px]">
        <Card padding="md">
          <QuestionCard
            question={data.question}
            questionNumber={data.question_number}
            totalQuestions={data.total_questions}
          />

          <div className="mt-3 space-y-1.5" role="group" aria-label="Answer options">
            {data.question.options.map((option) => {
              let variant: 'default' | 'correct' | 'incorrect' = 'default'
              const selected = selectedOptionIds.includes(option.id)
              if (feedback) {
                const match = feedback.options.find((item) => item.id === option.id)
                if (match?.is_correct) variant = 'correct'
                else if (selected) variant = 'incorrect'
              }
              return (
                <QuestionOption
                  key={option.id}
                  id={option.id}
                  text={option.option_text}
                  selected={selected}
                  disabled={!isExam && answered}
                  variant={variant}
                  onSelect={() => handleSelectOption(option.id, isMulti)}
                />
              )
            })}
          </div>

          {feedback && isPractice && <AnswerExplanation feedback={feedback} />}

          {answerMutation.isError && (
            <p className="mt-3 text-sm text-[var(--color-danger)]">
              {answerMutation.error instanceof Error
                ? answerMutation.error.message
                : 'Could not submit answer.'}
            </p>
          )}
          <div className="mt-4 flex flex-wrap items-center gap-2">
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

          <div className="mt-4 flex flex-wrap justify-between gap-2">
            <Button
              variant="secondary"
              size="sm"
              disabled={questionNumber <= 1 || completeMutation.isPending}
              onClick={() => void goToQuestion(questionNumber - 1)}
            >
              Previous
            </Button>

            <div className="flex flex-wrap gap-2">
              {selectedOptionIds.length > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setSelectedOptionIds([])
                    selectedRef.current = []
                    if (isExam) {
                      void queueAutosave({
                        selectedOptionIds: [],
                        markedForReview: markedRef.current,
                      })
                    }
                  }}
                >
                  Clear Selection
                </Button>
              )}
              {isExam ? (
                <>
                  {!isLast && (
                    <Button
                      variant="primary"
                      size="sm"
                      disabled={completeMutation.isPending}
                      onClick={() => void goToQuestion(questionNumber + 1)}
                    >
                      Next
                    </Button>
                  )}
                  {isLast && (
                    <>
                      {!confirmSubmit ? (
                        <Button
                          variant="primary"
                          size="sm"
                          disabled={completeMutation.isPending}
                          onClick={() => setConfirmSubmit(true)}
                        >
                          Submit Exam
                        </Button>
                      ) : (
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="text-xs text-[var(--color-text-muted)]">
                            Submit final answers?
                          </span>
                          <Button
                            variant="ghost"
                            size="sm"
                            disabled={completeMutation.isPending}
                            onClick={() => setConfirmSubmit(false)}
                          >
                            Cancel
                          </Button>
                          <Button
                            variant="primary"
                            size="sm"
                            disabled={completeMutation.isPending}
                            onClick={() => completeMutation.mutate()}
                          >
                            {completeMutation.isPending ? 'Submitting...' : 'Confirm submit'}
                          </Button>
                        </div>
                      )}
                    </>
                  )}
                </>
              ) : (
                <>
                  {!answered && (
                    <Button
                      variant="primary"
                      size="sm"
                      disabled={!canSubmit || answerMutation.isPending}
                      onClick={() => answerMutation.mutate()}
                    >
                      Submit Answer
                    </Button>
                  )}
                  {answered && !isLast && (
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => void goToQuestion(questionNumber + 1)}
                    >
                      Next
                    </Button>
                  )}
                  {answered && isLast && (
                    <Button
                      variant="primary"
                      size="sm"
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
            <h3 className="mb-2 text-sm font-medium">Question navigator</h3>
            <div className="grid grid-cols-5 gap-1.5">
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
                    disabled={completeMutation.isPending}
                    onClick={() => void goToQuestion(item.question_number)}
                    aria-label={`Question ${item.question_number}${item.answered ? ', answered' : ', unanswered'}${item.question_number === questionNumber ? ', current' : ''}`}
                  >
                    {item.question_number}
                  </button>
                )
              })}
            </div>
            <div className="mt-3 space-y-1 text-xs text-[var(--color-text-muted)]">
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
