import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'

import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
import { FieldLabel, Select } from '@/components/common/Field'
import { DifficultySelector } from '@/features/practice/DifficultySelector'
import { PracticeHistory } from '@/features/practice/PracticeHistory'
import { TopicCard } from '@/features/practice/TopicCard'
import { createSession, fetchCatalog } from '@/services/practiceService'
import type { Difficulty, PracticeMode } from '@/types/practice'

interface PracticeCatalogProps {
  title: string
  description: string
  domainSlug: string
  categorySlug?: string
  topicSlugs?: string[]
  formatLabel?: string
  showIntro?: boolean
}

export function PracticeCatalog({
  title,
  description,
  domainSlug,
  categorySlug,
  topicSlugs,
  formatLabel,
  showIntro = true,
}: PracticeCatalogProps) {
  const navigate = useNavigate()
  const { data, isLoading, isError } = useQuery({
    queryKey: ['practice-catalog'],
    queryFn: fetchCatalog,
  })
  const [selectedTopicId, setSelectedTopicId] = useState<string | null>(null)
  const [selectedCategoryId, setSelectedCategoryId] = useState<string | null>(null)
  const [difficulty, setDifficulty] = useState<Difficulty | undefined>('medium')
  const [questionCount, setQuestionCount] = useState(10)
  const [mode, setMode] = useState<PracticeMode>('practice')

  const mutation = useMutation({
    mutationFn: createSession,
    onSuccess: (session) => navigate(`/practice/sessions/${session.id}`),
  })

  const domain = data?.domains.find((item) => item.slug === domainSlug)
  const categories = domain?.categories
    .filter((category) => !categorySlug || category.slug === categorySlug)
    .map((category) => ({
      ...category,
      topics: topicSlugs?.length
        ? category.topics.filter((topic) => topicSlugs.includes(topic.slug))
        : category.topics,
    }))
    .filter((category) => category.topics.length > 0)

  const selectedCategory =
    categories?.find((category) => category.id === selectedCategoryId) ?? categories?.[0]
  const selectedTopic = selectedCategory?.topics.find((topic) => topic.id === selectedTopicId)

  const handleStart = () => {
    if (!selectedCategory || !selectedTopicId) return
    mutation.mutate({
      category_id: selectedCategory.id,
      topic_id: selectedTopicId,
      difficulty,
      question_count: questionCount,
      mode,
    })
  }

  if (isLoading) {
    return <p className="text-sm text-[var(--color-text-muted)]">Loading catalog...</p>
  }

  if (isError) {
    return (
      <Card>
        <p className="text-sm text-[var(--color-danger)]" role="alert">
          Could not load this catalog. Nothing was started.
        </p>
      </Card>
    )
  }

  if (!domain || (categories?.length ?? 0) === 0) {
    return (
      <Card>
        <h1 className="text-[1.75rem] font-semibold leading-tight text-[var(--color-text)]">{title}</h1>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]" role="status">
          This subject is not available yet. No session was created.
        </p>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      {showIntro ? (
        <div>
          <h1 className="text-[1.75rem] font-semibold leading-tight text-[var(--color-text)]">{title}</h1>
          <p className="mt-1 text-sm text-[var(--color-text-muted)]">{description}</p>
          {formatLabel ? (
            <p className="mt-1 text-xs text-[var(--color-text-subtle)]">Question format: {formatLabel}</p>
          ) : null}
        </div>
      ) : formatLabel ? (
        <p className="text-xs text-[var(--color-text-subtle)]">Question format: {formatLabel}</p>
      ) : null}

      {(categories?.length ?? 0) > 1 ? (
        <div>
          <p className="mb-1 text-xs font-medium text-[var(--color-text-muted)]">Subjects</p>
          <div className="filter-chip-row" role="group" aria-label="Subjects">
            <button
              type="button"
              className="filter-chip"
              aria-pressed={!selectedCategoryId}
              onClick={() => setSelectedCategoryId(null)}
            >
              All subjects
            </button>
            {categories?.map((category) => (
              <button
                key={category.id}
                type="button"
                className="filter-chip"
                aria-pressed={selectedCategoryId === category.id}
                onClick={() => {
                  setSelectedCategoryId(category.id)
                  setSelectedTopicId(null)
                }}
              >
                {category.name}
              </button>
            ))}
          </div>
        </div>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.6fr)_minmax(16rem,1fr)]">
        <Card padding="md">
          <CardHeader title="Topics" description="Choose a topic to practice" />
          <div className="space-y-3">
            {categories
              ?.filter((category) => !selectedCategoryId || category.id === selectedCategoryId)
              .map((category) => (
              <div key={category.id}>
                <button
                  type="button"
                  className="mb-1.5 text-sm font-medium text-[var(--color-text)]"
                  onClick={() => setSelectedCategoryId(category.id)}
                >
                  {category.name}
                </button>
                <div className="grid gap-2 sm:grid-cols-2">
                  {category.topics.map((topic) => (
                    <TopicCard
                      key={topic.id}
                      name={topic.name}
                      selected={selectedTopicId === topic.id}
                      onSelect={() => {
                        setSelectedCategoryId(category.id)
                        setSelectedTopicId(topic.id)
                      }}
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card padding="md">
          <CardHeader
            title="Session setup"
            description="Difficulty and mode apply only after a topic is selected."
          />
          <p className="mb-3 text-sm text-[var(--color-text)]" role="status">
            {selectedTopic ? `Selected topic: ${selectedTopic.name}` : 'Select a topic to continue.'}
          </p>
          <div className="space-y-3">
            <DifficultySelector value={difficulty} onChange={setDifficulty} />
            <div>
              <FieldLabel htmlFor="practice-question-count">Questions</FieldLabel>
              <Select
                id="practice-question-count"
                value={questionCount}
                onChange={(e) => setQuestionCount(Number(e.target.value))}
              >
                {[5, 10, 15, 20].map((count) => (
                  <option key={count} value={count}>
                    {count} questions
                  </option>
                ))}
              </Select>
            </div>
            <div>
              <FieldLabel>Mode</FieldLabel>
              <div className="flex gap-1.5" role="group" aria-label="Practice mode">
                {(['practice', 'exam'] as PracticeMode[]).map((item) => (
                  <button
                    key={item}
                    type="button"
                    aria-pressed={mode === item}
                    onClick={() => setMode(item)}
                    className={`h-8 rounded-[var(--radius-control)] border px-3 text-xs capitalize ${
                      mode === item
                        ? 'border-[var(--color-accent)] bg-[var(--color-accent-muted)] text-[var(--color-accent)]'
                        : 'border-[var(--color-border)] text-[var(--color-text-muted)]'
                    }`}
                  >
                    {item === 'exam' ? 'Timed exam' : 'Practice'}
                  </button>
                ))}
              </div>
              {mode === 'exam' && (
                <p className="mt-1.5 text-xs text-[var(--color-text-subtle)]">
                  Answers stay hidden until you submit. An unfinished exam can be resumed from this
                  subject&apos;s history. Selections already saved on the session are restored.
                </p>
              )}
            </div>
            <Button
              variant="primary"
              className="w-full"
              disabled={!selectedTopicId || mutation.isPending}
              onClick={handleStart}
            >
              {mutation.isPending ? 'Starting...' : 'Start Session'}
            </Button>
            {mutation.error && (
              <p className="text-xs text-[var(--color-danger)]" role="alert">
                {mutation.error.message}
              </p>
            )}
          </div>
        </Card>
      </div>

      <nav className="module-footer-links" aria-label="Related practice">
        <Link to="/learn">Courses</Link>
        <Link to="/mistakes">Mistake review</Link>
      </nav>

      <PracticeHistory categoryNames={categories?.map((category) => category.name) ?? []} />
    </div>
  )
}
