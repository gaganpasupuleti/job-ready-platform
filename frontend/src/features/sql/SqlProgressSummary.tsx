import { CatalogMetrics } from '@/components/practice/CatalogMetrics'
import { humanLabel } from '@/lib/studentLabels'
import type { SqlProgressSummary as SqlProgressSummaryType } from '@/types/sql'

interface SqlProgressSummaryProps {
  progress: SqlProgressSummaryType
}

export function SqlProgressSummary({ progress }: SqlProgressSummaryProps) {
  const metrics = [
    { label: 'Problems', value: String(progress.total_problems) },
    { label: 'Solved', value: String(progress.solved_count) },
    { label: 'Attempted', value: String(progress.attempted_count) },
  ]
  for (const level of ['easy', 'medium', 'hard'] as const) {
    const breakdown = progress[level]
    if (!breakdown) continue
    metrics.push({ label: humanLabel(level), value: `${breakdown.solved}/${breakdown.total}` })
  }
  return <CatalogMetrics metrics={metrics} />
}
