import { Link } from 'react-router-dom'

import { Badge } from '@/components/common/Badge'
import { Card, CardHeader } from '@/components/common/Card'
import type { SqlProblemListItem, SqlProgressStatus } from '@/types/sql'

const progressLabel: Record<SqlProgressStatus, string> = {
  unsolved: 'Unsolved',
  attempted: 'Attempted',
  solved: 'Solved',
}

const progressVariant: Record<SqlProgressStatus, 'default' | 'warning' | 'success'> = {
  unsolved: 'default',
  attempted: 'warning',
  solved: 'success',
}

interface SqlProblemListProps {
  problems: SqlProblemListItem[]
  total: number
  isLoading: boolean
  progressMap?: Map<string, SqlProgressStatus | null | undefined>
}

export function SqlProblemList({ problems, total, isLoading, progressMap }: SqlProblemListProps) {
  return (
    <Card>
      <CardHeader title={`Problems (${total})`} />
      {isLoading ? (
        <p className="text-sm text-[var(--color-text-muted)]">Loading problems...</p>
      ) : problems.length === 0 ? (
        <p className="text-sm text-[var(--color-text-muted)]">No problems match your filters.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-xs text-[var(--color-text-subtle)]">
              <tr>
                <th className="pb-2 pr-3">Status</th>
                <th className="pb-2 pr-3">Title</th>
                <th className="pb-2 pr-3">Difficulty</th>
                <th className="pb-2 pr-3">Topic</th>
                <th className="pb-2 pr-3">Roles</th>
                <th className="pb-2">Acceptance</th>
              </tr>
            </thead>
            <tbody>
              {problems.map((problem) => {
                const status =
                  progressMap?.get(problem.id) ?? problem.progress_status ?? 'unsolved'
                const safeStatus = status as SqlProgressStatus
                return (
                  <tr
                    key={problem.id}
                    className="border-t border-[var(--color-border)] hover:bg-[var(--color-surface-muted)]"
                  >
                    <td className="py-3 pr-3">
                      <Badge variant={progressVariant[safeStatus] ?? 'default'}>
                        {progressLabel[safeStatus] ?? status}
                      </Badge>
                    </td>
                    <td className="py-3 pr-3">
                      <Link
                        to={`/practice/sql/${problem.slug}`}
                        className="font-medium text-[var(--color-accent)] hover:underline"
                      >
                        {problem.title}
                      </Link>
                    </td>
                    <td className="py-3 pr-3 capitalize">{problem.difficulty}</td>
                    <td className="py-3 pr-3 text-xs text-[var(--color-text-muted)]">
                      {problem.topic_name ?? problem.topic_slug ?? '—'}
                    </td>
                    <td className="py-3 pr-3">
                      <div className="flex flex-wrap gap-1">
                        {(problem.role_tags ?? []).slice(0, 3).map((tag) => (
                          <Badge key={tag}>{tag}</Badge>
                        ))}
                      </div>
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

interface SqlFiltersProps {
  search: string
  difficulty: string
  topicSlug: string
  status: string
  onSearchChange: (value: string) => void
  onDifficultyChange: (value: string) => void
  onTopicSlugChange: (value: string) => void
  onStatusChange: (value: string) => void
}

export function SqlProblemFilters({
  search,
  difficulty,
  topicSlug,
  status,
  onSearchChange,
  onDifficultyChange,
  onTopicSlugChange,
  onStatusChange,
}: SqlFiltersProps) {
  return (
    <Card padding="md">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
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
          placeholder="Topic slug"
          value={topicSlug}
          onChange={(e) => onTopicSlugChange(e.target.value)}
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
