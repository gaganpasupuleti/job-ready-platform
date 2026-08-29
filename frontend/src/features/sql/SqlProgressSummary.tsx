import { Card } from '@/components/common/Card'
import type { SqlProgressSummary as SqlProgressSummaryType } from '@/types/sql'

interface SqlProgressSummaryProps {
  progress: SqlProgressSummaryType
}

export function SqlProgressSummary({ progress }: SqlProgressSummaryProps) {
  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-3">
        <Card padding="md">
          <p className="text-xs text-[var(--color-text-subtle)]">Total problems</p>
          <p className="text-2xl font-semibold">{progress.total_problems}</p>
        </Card>
        <Card padding="md">
          <p className="text-xs text-[var(--color-text-subtle)]">Solved</p>
          <p className="text-2xl font-semibold text-[var(--color-success)]">
            {progress.solved_count}
          </p>
        </Card>
        <Card padding="md">
          <p className="text-xs text-[var(--color-text-subtle)]">Attempted</p>
          <p className="text-2xl font-semibold">{progress.attempted_count}</p>
        </Card>
      </div>
      {(progress.easy || progress.medium || progress.hard) && (
        <div className="grid gap-4 sm:grid-cols-3">
          {(['easy', 'medium', 'hard'] as const).map((level) => {
            const breakdown = progress[level]
            if (!breakdown) return null
            return (
              <Card key={level} padding="md">
                <p className="text-xs capitalize text-[var(--color-text-subtle)]">{level}</p>
                <p className="text-lg font-semibold">
                  {breakdown.solved}/{breakdown.total} solved
                </p>
                <p className="text-xs text-[var(--color-text-muted)]">
                  {breakdown.attempted} attempted
                </p>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
