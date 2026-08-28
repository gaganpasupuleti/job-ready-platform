import { Badge } from '@/components/common/Badge'
import type { QuestionPublic } from '@/types/practice'

interface QuestionCardProps {
  question: QuestionPublic
  questionNumber: number
  totalQuestions: number
}

export function QuestionCard({ question, questionNumber, totalQuestions }: QuestionCardProps) {
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <Badge>
          Q{questionNumber}/{totalQuestions}
        </Badge>
        <Badge variant="accent">{question.difficulty}</Badge>
        {question.topic_name && <Badge>{question.topic_name}</Badge>}
      </div>
      {question.title && (
        <h3 className="text-sm font-medium text-[var(--color-text)]">{question.title}</h3>
      )}
      <p className="text-sm leading-relaxed text-[var(--color-text)]">{question.question_text}</p>
    </div>
  )
}
