import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Bookmark, Flag } from 'lucide-react'

import { Button } from '@/components/common/Button'
import { Card } from '@/components/common/Card'
import { AnswerExplanation } from '@/features/practice/AnswerExplanation'
import { QuestionCard } from '@/features/practice/QuestionCard'
import { QuestionOption } from '@/features/practice/QuestionOption'
import {
  completeSession,
  fetchSession,
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
  const [feedback, setFeedback] = useState<AnswerFeedback | null>(null)
  const [answered, setAnswered] = useState(false)
  const [startTime] = useState(Date.now())

  const sessionQuery = useQuery({
    queryKey: ['practice-session', sessionId],
    queryFn: () => fetchSession(sessionId),
    enabled: Boolean(sessionId),
  })

  const questionQuery = useQuery({
    queryKey: ['practice-question', sessionId, questionNumber],
    queryFn: () => fetchSessionQuestion(sessionId, questionNumber),
    enabled: Boolean(sessionId),
  })

  useEffect(() => {
    setSelectedOptionId(null)
    setFeedback(null)
    setAnswered(Boolean(questionQuery.data?.answered))
  }, [questionNumber, questionQuery.data?.answered])

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

  if (sessionQuery.isLoading || questionQuery.isLoading) {
    return <p className="text-sm text-[var(--color-text-muted)]">Loading session...</p>
  }

  const session = sessionQuery.data
  const data = questionQuery.data
  if (!session || !data) {
    return <p className="text-sm text-[var(--color-danger)]">Session not found.</p>
  }

  const isPractice = session.mode === 'practice'
  const canSubmit = !answered && selectedOptionId
  const isLast = questionNumber >= session.question_count

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <div className="flex items-center justify-between text-xs text-[var(--color-text-muted)]">
        <span>
          {session.mode} mode · {session.answered_count}/{session.question_count} answered
        </span>
        <span>{Math.round((questionNumber / session.question_count) * 100)}% complete</span>
      </div>

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
                disabled={answered}
                variant={variant}
                onSelect={() => setSelectedOptionId(option.id)}
              />
            )
          })}
        </div>

        {feedback && isPractice && <AnswerExplanation feedback={feedback} />}

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
          <Button variant="ghost" size="sm" disabled title="Coming soon">
            <Flag className="h-4 w-4" />
            Report
          </Button>
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
          </div>
        </div>
      </Card>
    </div>
  )
}
