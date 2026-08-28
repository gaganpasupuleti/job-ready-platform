import { Badge } from '@/components/common/Badge'
import type { AnswerFeedback } from '@/types/practice'

interface AnswerExplanationProps {
  feedback: AnswerFeedback
}

export function AnswerExplanation({ feedback }: AnswerExplanationProps) {
  return (
    <div className="mt-4 space-y-3 rounded-md border border-[var(--color-border)] bg-[var(--color-surface-muted)] p-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant={feedback.is_correct ? 'success' : 'warning'}>
          {feedback.is_correct ? 'Correct' : 'Incorrect'}
        </Badge>
        <Badge>{feedback.marks_awarded} marks</Badge>
        {feedback.topic_name && <Badge>{feedback.topic_name}</Badge>}
      </div>
      {feedback.explanation && (
        <p className="text-sm text-[var(--color-text-muted)]">{feedback.explanation}</p>
      )}
      {feedback.skills.length > 0 && (
        <p className="text-xs text-[var(--color-text-subtle)]">
          Skills: {feedback.skills.join(', ')}
        </p>
      )}
    </div>
  )
}
