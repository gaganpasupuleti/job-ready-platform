import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import {
  CodingProblemList,
  CodingProgressSummary,
  ProblemFilters,
} from '@/features/dsa/CodingProblemList'
import { fetchCodingProblems, fetchCodingProgress } from '@/services/codingService'
import type { ProblemProgressStatus } from '@/types/coding'

export function DsaPage() {
  const [search, setSearch] = useState('')
  const [difficulty, setDifficulty] = useState('')
  const [topicSlug, setTopicSlug] = useState('')
  const [tag, setTag] = useState('')
  const [status, setStatus] = useState('')

  const { data: progress } = useQuery({
    queryKey: ['coding-progress'],
    queryFn: fetchCodingProgress,
  })

  const { data: problems, isLoading } = useQuery({
    queryKey: ['coding-problems', search, difficulty, topicSlug, tag, status],
    queryFn: () =>
      fetchCodingProblems({
        search: search || undefined,
        difficulty: difficulty || undefined,
        topic_slug: topicSlug || undefined,
        tag: tag || undefined,
        status: (status as ProblemProgressStatus) || undefined,
      }),
  })

  const progressMap = useMemo(
    () => new Map(progress?.items.map((item) => [item.id, item.progress_status]) ?? []),
    [progress],
  )

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-[var(--color-text)]">DSA Practice</h2>
        <p className="text-sm text-[var(--color-text-muted)]">
          Topic-organized coding problems with run/submit, progress tracking, and hidden test
          evaluation.
        </p>
      </div>

      {progress && <CodingProgressSummary progress={progress} />}

      <ProblemFilters
        search={search}
        difficulty={difficulty}
        topicSlug={topicSlug}
        tag={tag}
        status={status}
        onSearchChange={setSearch}
        onDifficultyChange={setDifficulty}
        onTopicSlugChange={setTopicSlug}
        onTagChange={setTag}
        onStatusChange={setStatus}
      />

      <CodingProblemList
        problems={problems?.items ?? []}
        total={problems?.total ?? 0}
        isLoading={isLoading}
        progressMap={progressMap}
      />
    </div>
  )
}
