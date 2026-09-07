import { BookOpen } from 'lucide-react'

import { Badge } from '@/components/common/Badge'
import { buildQuestionLearningContext } from '@/features/sql/utils/sqlQuestionLearningGuide'
import type { SqlProblemDetail } from '@/types/sql'

interface SqlQuestionLearningGuideProps {
  problem: SqlProblemDetail
}

export function SqlQuestionLearningGuide({ problem }: SqlQuestionLearningGuideProps) {
  const guide = buildQuestionLearningContext(problem)

  return (
    <div className="space-y-3 rounded-md border border-[var(--color-border)] bg-[var(--color-surface-muted)] p-3">
      <div className="flex items-center gap-2 text-sm font-medium text-[var(--color-text)]">
        <BookOpen className="h-4 w-4 text-[var(--color-accent)]" />
        How to approach this
      </div>
      <p className="text-xs text-[var(--color-text-muted)]">
        Concept: <span className="text-[var(--color-text)]">{guide.concept}</span>
        {guide.tables.length > 0 && (
          <>
            {' '}
            · Tables: <span className="font-mono text-[var(--color-text)]">{guide.tables.join(', ')}</span>
          </>
        )}
      </p>
      {guide.sqlSkills.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {guide.sqlSkills.map((skill) => (
            <Badge key={skill}>{skill}</Badge>
          ))}
        </div>
      )}
      <ol className="list-decimal space-y-1 pl-4 text-sm text-[var(--color-text-muted)]">
        {guide.steps.map((step) => (
          <li key={step}>{step}</li>
        ))}
      </ol>
      <p className="rounded border border-amber-300/60 bg-amber-50 px-2 py-1.5 text-xs text-amber-900 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-100">
        Common mistake: {guide.commonMistake}
      </p>
      {guide.conceptGuides.map((item) => (
        <div key={item.title} className="text-xs">
          <p className="font-medium text-[var(--color-text)]">{item.title}</p>
          <p className="mt-0.5 text-[var(--color-text-muted)]">{item.body}</p>
        </div>
      ))}
    </div>
  )
}
