import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { SqlProblemFilters, SqlProblemList } from '@/features/sql/SqlProblemList'
import { SqlProgressSummary } from '@/features/sql/SqlProgressSummary'
import { fetchSqlProblems, fetchSqlProgress } from '@/services/sqlService'
import type { SqlProgressStatus } from '@/types/sql'

export function SqlPage() {
  const [search, setSearch] = useState('')
  const [difficulty, setDifficulty] = useState('')
  const [topicSlug, setTopicSlug] = useState('')
  const [status, setStatus] = useState('')

  const { data: progress } = useQuery({
    queryKey: ['sql-progress'],
    queryFn: fetchSqlProgress,
  })

  const { data: problems, isLoading } = useQuery({
    queryKey: ['sql-problems', search, difficulty, topicSlug, status],
    queryFn: () =>
      fetchSqlProblems({
        search: search || undefined,
        difficulty: difficulty || undefined,
        topic_slug: topicSlug || undefined,
        status: (status as SqlProgressStatus) || undefined,
      }),
  })

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-[var(--color-text)]">SQL Practice</h2>
        <p className="text-sm text-[var(--color-text-muted)]">
          Query writing exercises with schema exploration, run/submit feedback, and progress
          tracking.
        </p>
      </div>

      {progress && <SqlProgressSummary progress={progress} />}

      <SqlProblemFilters
        search={search}
        difficulty={difficulty}
        topicSlug={topicSlug}
        status={status}
        onSearchChange={setSearch}
        onDifficultyChange={setDifficulty}
        onTopicSlugChange={setTopicSlug}
        onStatusChange={setStatus}
      />

      <SqlProblemList
        problems={problems?.items ?? []}
        total={problems?.total ?? 0}
        isLoading={isLoading}
      />
    </div>
  )
}
