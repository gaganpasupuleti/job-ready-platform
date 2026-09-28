import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { PracticeTrackNav } from '@/components/practice/PracticeTrackNav'
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
  const topics = progress?.topics ?? []
  const topicsIncomplete = (progress?.total_problems ?? 0) > (progress?.items.length ?? 0)

  return (
    <div className="module-page space-y-4">
      <PracticeTrackNav />
      <div>
        <h1 className="text-lg font-semibold text-[var(--color-text)]">Programming & DSA</h1>
        <p className="text-sm text-[var(--color-text-muted)]">
          Topic-organized coding problems with run/submit, progress tracking, and hidden test
          evaluation.
        </p>
      </div>

      {progress && <CodingProgressSummary progress={progress} />}

      {topics.length > 0 ? (
        <>
          <div className="filter-chip-row" role="group" aria-label="DSA topics">
            <button
              type="button"
              className="filter-chip"
              aria-pressed={!topicSlug}
              onClick={() => setTopicSlug('')}
            >
              All topics
            </button>
            {topics.map((topic) => (
              <button
                key={topic.topic_slug}
                type="button"
                className="filter-chip"
                aria-pressed={topicSlug === topic.topic_slug}
                onClick={() =>
                  setTopicSlug(topicSlug === topic.topic_slug ? '' : topic.topic_slug)
                }
              >
                {topic.topic_name}
                <span className="practice-track-count">
                  {topic.solved}/{topic.total}
                </span>
              </button>
            ))}
          </div>
          {topicsIncomplete ? (
            <p className="filter-chip-note">
              Topic list covers the progress summary only. A dedicated topics endpoint is not
              available, so rare topics beyond that summary stay reachable from the topic field.
            </p>
          ) : null}
        </>
      ) : null}

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
