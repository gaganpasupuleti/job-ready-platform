import { Link } from 'react-router-dom'

import { Card, CardHeader } from '@/components/common/Card'
import { CatalogMetrics } from '@/components/practice/CatalogMetrics'
import { humanLabel } from '@/lib/studentLabels'
import type { CodingProblemListItem, ProblemProgressStatus } from '@/types/coding'

const progressLabel: Record<ProblemProgressStatus, string> = {
  unsolved: 'Unsolved',
  attempted: 'Attempted',
  solved: 'Solved',
}

interface CodingProblemListProps {
  problems: CodingProblemListItem[]
  total: number
  isLoading: boolean
  problemLinkPrefix?: string
  progressMap?: Map<string, ProblemProgressStatus | null | undefined>
}

export function CodingProblemList({
  problems,
  total,
  isLoading,
  problemLinkPrefix = '/practice/dsa',
  progressMap,
}: CodingProblemListProps) {
  return (
    <Card>
      <CardHeader title={`Problems (${total})`} />
      {isLoading ? (
        <p className="text-sm text-[var(--color-text-muted)]">Loading problems...</p>
      ) : problems.length === 0 ? (
        <p className="text-sm text-[var(--color-text-muted)]">No problems match your filters.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="problem-table w-full text-left text-sm">
            <thead className="text-xs text-[var(--color-text-subtle)]">
              <tr>
                <th className="pb-2 pr-3">Progress</th>
                <th className="pb-2 pr-3">Problem</th>
                <th className="pb-2 pr-3">Tags</th>
                <th className="pb-2 pr-3">Attempts</th>
                <th className="pb-2">Acceptance</th>
              </tr>
            </thead>
            <tbody>
              {problems.map((problem) => {
                const status =
                  progressMap?.get(problem.id) ?? problem.progress_status ?? 'unsolved'
                const safeStatus = status as ProblemProgressStatus
                return (
                  <tr
                    key={problem.id}
                    className="border-t border-[var(--color-border)] hover:bg-[var(--color-surface-muted)]"
                  >
                    <td className="py-3 pr-3 text-xs text-[var(--color-text-muted)]">
                      {progressLabel[safeStatus] ?? humanLabel(status)}
                    </td>
                    <td className="py-3 pr-3">
                      <Link
                        to={`${problemLinkPrefix}/${problem.id}`}
                        className="text-[15px] font-semibold text-[var(--color-text)] hover:underline"
                      >
                        {problem.title}
                      </Link>
                      <p className="mt-0.5 text-xs text-[var(--color-text-muted)]">
                        {humanLabel(problem.difficulty)}
                        {problem.topic_name || problem.topic_slug
                          ? ` · ${problem.topic_name ?? problem.topic_slug}`
                          : ''}
                      </p>
                    </td>
                    <td className="py-3 pr-3 text-xs text-[var(--color-text-muted)]">
                      {(problem.tags ?? []).slice(0, 3).join(', ') || '—'}
                    </td>
                    <td className="py-3 pr-3 text-[var(--color-text-muted)]">
                      {problem.attempts == null ? '—' : problem.attempts}
                    </td>
                    <td className="py-3 text-[var(--color-text-muted)]">
                      {problem.acceptance_rate != null
                        ? `${Math.round(problem.acceptance_rate * 100)}%`
                        : '—'}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  )
}

interface ProgressSummaryProps {
  progress: {
    total_problems: number
    solved_count: number
    attempted_count: number
    easy?: { solved: number; total: number; attempted: number }
    medium?: { solved: number; total: number; attempted: number }
    hard?: { solved: number; total: number; attempted: number }
  }
}

export function CodingProgressSummary({ progress }: ProgressSummaryProps) {
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

interface ProblemFiltersProps {
  search: string
  difficulty: string
  topicSlug: string
  tag: string
  status: string
  onSearchChange: (value: string) => void
  onDifficultyChange: (value: string) => void
  onTopicSlugChange: (value: string) => void
  onTagChange: (value: string) => void
  onStatusChange: (value: string) => void
}

export function ProblemFilters({
  search,
  difficulty,
  topicSlug,
  tag,
  status,
  onSearchChange,
  onDifficultyChange,
  onTopicSlugChange,
  onTagChange,
  onStatusChange,
}: ProblemFiltersProps) {
  return (
    <Card padding="md">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <input
          type="search"
          placeholder="Search problems..."
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm"
        />
        <select
          value={difficulty}
          onChange={(e) => onDifficultyChange(e.target.value)}
          className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm"
        >
          <option value="">All difficulties</option>
          <option value="easy">Easy</option>
          <option value="medium">Medium</option>
          <option value="hard">Hard</option>
        </select>
        <input
          aria-label="Topic"
          placeholder="Topic"
          value={topicSlug}
          onChange={(e) => onTopicSlugChange(e.target.value)}
          className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm"
        />
        <input
          placeholder="Tag"
          value={tag}
          onChange={(e) => onTagChange(e.target.value)}
          className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm"
        />
        <select
          value={status}
          onChange={(e) => onStatusChange(e.target.value)}
          className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm"
        >
          <option value="">All statuses</option>
          <option value="unsolved">Unsolved</option>
          <option value="attempted">Attempted</option>
          <option value="solved">Solved</option>
        </select>
      </div>
    </Card>
  )
}
