import { Link } from 'react-router-dom'
import { Target } from 'lucide-react'

import { Button } from '@/components/common/Button'
import { Card } from '@/components/common/Card'
import { mistakeAction, sqlWeakTopic } from '@/lib/studentLabels'
import type { SqlProgressSummary } from '@/types/sql'
import type { MistakeItem } from '@/types/readiness'

interface SqlReviewCtasProps {
  progress?: SqlProgressSummary
  mistakes?: MistakeItem[]
  unsolvedHref?: string | null
  firstMistakeHref?: string | null
}

export function SqlReviewCtas({
  progress,
  mistakes,
  unsolvedHref,
  firstMistakeHref,
}: SqlReviewCtasProps) {
  const progressKnown = progress != null
  const attempted = progress?.attempted_count ?? 0
  const solved = progress?.solved_count ?? 0
  const total = progress?.total_problems ?? 0
  const unfinished = Math.max(0, total - solved)
  const openMistakes = mistakes?.filter((item) => item.source_type === 'sql' && item.status !== 'resolved').length
  const weakTopic = sqlWeakTopic(mistakes)
  const mistakeLink = mistakeAction(firstMistakeHref)

  return (
    <Card padding="md" className="space-y-3">
      <div className="flex items-center gap-2 text-sm font-medium text-[var(--color-text)]">
        <Target className="h-4 w-4 text-[var(--color-accent)]" />
        SQL practice
      </div>
      <p className="text-xs text-[var(--color-text-muted)]">
        {progressKnown ? `${solved}/${total} solved · ${attempted} attempted` : 'SQL progress is still loading.'}
        {openMistakes != null ? ` · ${openMistakes} open SQL mistakes` : ''}
      </p>
      {weakTopic?.empty && (
        <p className="text-xs text-[var(--color-text-muted)]">No open SQL mistakes.</p>
      )}
      {weakTopic && !weakTopic.empty && (
        <p className="text-xs text-[var(--color-text-muted)]">
          Most repeated SQL mistake:{' '}
          <span className="font-medium text-[var(--color-text)]">{weakTopic.title}</span>
          {` (${weakTopic.count} ${weakTopic.count === 1 ? 'miss' : 'misses'})`}
        </p>
      )}
      <div className="flex flex-wrap gap-2">
        {mistakeLink && (
          <Link to={mistakeLink.href} title={mistakeLink.note ?? undefined}>
            <Button size="sm" variant="secondary">
              {mistakeLink.label}
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
      {mistakeLink?.note && <p className="text-xs text-[var(--color-text-muted)]">{mistakeLink.note}</p>}
    </Card>
  )
}
