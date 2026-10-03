import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { PracticeTrackNav } from '@/components/practice/PracticeTrackNav'
import { SqlProblemFilters, SqlProblemList } from '@/features/sql/SqlProblemList'
import { SqlProgressSummary } from '@/features/sql/SqlProgressSummary'
import { SqlReviewCtas } from '@/features/sql/SqlReviewCtas'
import { capabilityNotice } from '@/lib/codingRuntime'
import { fetchMistakes } from '@/services/mistakeService'
import { fetchSqlExecutionStatus, fetchSqlProblems, fetchSqlProgress } from '@/services/sqlService'
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
  const execution = useQuery({
    queryKey: ['sql-execution-status'],
    queryFn: fetchSqlExecutionStatus,
  })
  const runtime = capabilityNotice({
    pending: execution.isPending,
    failed: execution.isError,
    available: execution.data?.available,
    kind: 'sql',
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

  const { data: sqlMistakes } = useQuery({
    queryKey: ['mistakes', 'sql', 'unresolved'],
    queryFn: () => fetchMistakes({ source_type: 'sql', view: 'unresolved' }),
  })

  const { data: unsolvedProblems } = useQuery({
    queryKey: ['sql-problems', 'unsolved-for-cta'],
    queryFn: () => fetchSqlProblems({ status: 'unsolved', limit: 5 }),
  })

  const firstMistakeHref = useMemo(() => {
    const open = sqlMistakes?.find((m) => m.retry_href)
    return open?.retry_href ?? null
  }, [sqlMistakes])

  const unsolvedHref = useMemo(() => {
    const item = unsolvedProblems?.items?.[0]
    if (!item) return '/practice/sql?status=unsolved'
    return `/practice/sql/${item.slug}`
  }, [unsolvedProblems])

  return (
    <div className="module-page space-y-4">
      <PracticeTrackNav />
      <div>
        <h1 className="text-[1.75rem] font-semibold leading-tight text-[var(--color-text)]">SQL Practice</h1>
        <p className="text-sm text-[var(--color-text-muted)]">
          Query writing exercises with schema exploration, run/submit feedback, and progress
          tracking.
        </p>
      </div>

      <p className="capability-note" role="status" data-runtime-state={runtime.state}>
        {runtime.text}
      </p>
      {progress && <SqlProgressSummary progress={progress} />}

      <SqlReviewCtas
        progress={progress}
        mistakes={sqlMistakes}
        unsolvedHref={unsolvedHref}
        firstMistakeHref={firstMistakeHref}
      />

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
