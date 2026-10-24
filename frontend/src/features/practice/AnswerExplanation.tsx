import { useState } from 'react'

import { Badge } from '@/components/common/Badge'
import type { AnswerFeedback } from '@/types/practice'

interface AnswerExplanationProps {
  feedback: AnswerFeedback
}

export function AnswerExplanation({ feedback }: AnswerExplanationProps) {
  const [showAll, setShowAll] = useState(false)

  return (
    <div className="mt-4 space-y-3 rounded-md border border-[var(--color-border)] bg-[var(--color-surface-muted)] p-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant={feedback.is_correct ? 'success' : 'warning'}>
          {feedback.is_correct ? 'Correct' : 'Incorrect'}
        </Badge>
        <Badge>{feedback.marks_awarded} marks</Badge>
        {feedback.topic_name && <Badge>{feedback.topic_name}</Badge>}
      </div>
      {feedback.selected_option_texts.length > 0 && (
        <p className="text-sm text-[var(--color-text)]">
          Your answer: <strong>{feedback.selected_option_texts.join(', ')}</strong>
        </p>
      )}
      {feedback.correct_option_texts.length > 0 && (
        <p className="text-sm text-[var(--color-text)]">
          Correct answer: <strong>{feedback.correct_option_texts.join(', ')}</strong>
        </p>
      )}
      {feedback.selected_option_explanation && (
        <p className="text-sm text-[var(--color-text-muted)]">{feedback.selected_option_explanation}</p>
      )}
      {feedback.explanation && (
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-text-subtle)]">
            Worked solution
          </p>
          <p className="text-sm text-[var(--color-text-muted)]">{feedback.explanation}</p>
        </div>
      )}
      {feedback.options.length > 0 && (
        <div>
          <button
            type="button"
            className="text-sm font-medium text-[var(--color-accent)] hover:underline"
            onClick={() => setShowAll((value) => !value)}
          >
            {showAll ? 'Hide all option explanations' : 'Show all option explanations'}
          </button>
          {showAll && (
            <ul className="mt-2 space-y-2">
              {feedback.options.map((opt) => (
                <li
                  key={opt.id}
                  className="rounded border border-[var(--color-border)] bg-[var(--color-surface)] p-2 text-sm"
                >
                  <span className="font-medium">{opt.option_text}</span>
                  {opt.explanation && (
                    <p className="mt-1 text-[var(--color-text-muted)]">{opt.explanation}</p>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
      {feedback.skills.length > 0 && (
        <p className="text-xs text-[var(--color-text-subtle)]">
          Skills: {feedback.skills.join(', ')}
        </p>
      )}
    </div>
  )
}
