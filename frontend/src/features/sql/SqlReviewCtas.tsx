import { Link } from 'react-router-dom'
import { Lightbulb, Target } from 'lucide-react'

import { Button } from '@/components/common/Button'
import { Card } from '@/components/common/Card'
import type { SqlProgressSummary } from '@/types/sql'
import type { MistakeItem, MistakeSummary } from '@/types/readiness'

interface SqlReviewCtasProps {
  progress?: SqlProgressSummary
  mistakes?: MistakeItem[]
  mistakeSummary?: MistakeSummary
  unsolvedHref?: string | null
  firstMistakeHref?: string | null
}

export function SqlReviewCtas({
  progress,
  mistakes,
  mistakeSummary,
  unsolvedHref,
  firstMistakeHref,
}: SqlReviewCtasProps) {
  const attempted = progress?.attempted_count ?? 0
  const solved = progress?.solved_count ?? 0
  const total = progress?.total_problems ?? 0
  const unfinished = Math.max(0, total - solved)
  const openMistakes = mistakes?.filter((m) => m.status !== 'resolved').length ?? 0
  const weakTopic = mistakeSummary?.top_weak_topics?.[0]

  return (
    <Card padding="md" className="space-y-3">
      <div className="flex items-center gap-2 text-sm font-medium text-[var(--color-text)]">
        <Target className="h-4 w-4 text-[var(--color-accent)]" />
        Practice recommendations
      </div>
      <p className="text-xs text-[var(--color-text-muted)]">
        {solved}/{total} solved · {attempted} attempted · {openMistakes} open SQL mistakes
      </p>
      {weakTopic && (
        <p className="flex items-start gap-2 text-xs text-[var(--color-text-muted)]">
          <Lightbulb className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-500" />
          Weak topic: <span className="font-medium text-[var(--color-text)]">{weakTopic.title}</span>
          {typeof weakTopic.count === 'number' ? ` (${weakTopic.count} misses)` : ''}
        </p>
      )}
      <div className="flex flex-wrap gap-2">
        {firstMistakeHref && (
          <Link to={firstMistakeHref}>
            <Button size="sm" variant="secondary">
              Retry a mistake
            </Button>
          </Link>
        )}
        {unsolvedHref && unfinished > 0 && (
          <Link to={unsolvedHref}>
            <Button size="sm" variant="secondary">
              Continue unfinished
            </Button>
          </Link>
        )}
        <Link to="/mistakes?source_type=sql">
          <Button size="sm" variant="ghost">
            Open Mistake Book
          </Button>
        </Link>
        <Link to="/practice/sql">
          <Button size="sm" variant="ghost">
            Browse catalog
          </Button>
        </Link>
      </div>
    </Card>
  )
}
