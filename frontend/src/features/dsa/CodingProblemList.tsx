import { Link } from 'react-router-dom'

import { Badge } from '@/components/common/Badge'
import { Card, CardHeader } from '@/components/common/Card'
import type { CodingProblemListItem, ProblemProgressStatus } from '@/types/coding'

const progressLabel: Record<ProblemProgressStatus, string> = {
  unsolved: 'Unsolved',
  attempted: 'Attempted',
  solved: 'Solved',
}

const progressVariant: Record<ProblemProgressStatus, 'default' | 'warning' | 'success'> = {
  unsolved: 'default',
  attempted: 'warning',
  solved: 'success',
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
          <table className="w-full text-left text-sm">
            <thead className="text-xs text-[var(--color-text-subtle)]">
              <tr>
                <th className="pb-2 pr-3">Status</th>
                <th className="pb-2 pr-3">Title</th>
                <th className="pb-2 pr-3">Difficulty</th>
                <th className="pb-2 pr-3">Topic</th>
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
                    <td className="py-3 pr-3">
                      <Badge variant={progressVariant[safeStatus] ?? 'default'}>
                        {progressLabel[safeStatus] ?? status}
                      </Badge>
                    </td>
                    <td className="py-3 pr-3">
                      <Link
                        to={`${problemLinkPrefix}/${problem.id}`}
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
                        {(problem.tags ?? []).slice(0, 3).map((tag) => (
                          <Badge key={tag}>{tag}</Badge>
                        ))}
                      </div>
                    </td>
                    <td className="py-3 pr-3 text-[var(--color-text-muted)]">
                      {problem.attempts ?? 0}
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
          placeholder="Topic slug"
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
