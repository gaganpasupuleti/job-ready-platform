import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'

import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
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
}

export function PracticeCatalog({
  title,
  description,
  domainSlug,
  categorySlug,
}: PracticeCatalogProps) {
  const navigate = useNavigate()
  const { data, isLoading, error } = useQuery({
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
  const categories = domain?.categories.filter(
    (category) => !categorySlug || category.slug === categorySlug,
  )

  const selectedCategory =
    categories?.find((category) => category.id === selectedCategoryId) ?? categories?.[0]

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

  if (error || !domain) {
    return (
      <Card>
        <p className="text-sm text-[var(--color-danger)]">
          Unable to load practice catalog. Ensure you are logged in and the API is running.
        </p>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-[var(--color-text)]">{title}</h2>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">{description}</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
        <Card>
          <CardHeader title="Topics" description="Choose a topic to practice" />
          <div className="space-y-4">
            {categories?.map((category) => (
              <div key={category.id}>
                <button
                  type="button"
                  className="mb-2 text-sm font-medium text-[var(--color-text)]"
                  onClick={() => setSelectedCategoryId(category.id)}
                >
                  {category.name}
                </button>
                <div className="grid gap-3 sm:grid-cols-2">
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

        <Card>
          <CardHeader title="Session Setup" />
          <div className="space-y-4">
            <DifficultySelector value={difficulty} onChange={setDifficulty} />
            <div>
              <label className="mb-1 block text-xs font-medium text-[var(--color-text-muted)]">
                Questions
              </label>
              <select
                className="w-full rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm"
                value={questionCount}
                onChange={(e) => setQuestionCount(Number(e.target.value))}
              >
                {[5, 10, 15, 20].map((count) => (
                  <option key={count} value={count}>
                    {count} questions
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-[var(--color-text-muted)]">
                Mode
              </label>
              <div className="flex gap-2">
                {(['practice', 'exam'] as PracticeMode[]).map((item) => (
                  <button
                    key={item}
                    type="button"
                    onClick={() => setMode(item)}
                    className={`rounded-md border px-3 py-2 text-xs capitalize ${
                      mode === item
                        ? 'border-[var(--color-accent)] bg-[var(--color-accent-muted)] text-[var(--color-accent)]'
                        : 'border-[var(--color-border)] text-[var(--color-text-muted)]'
                    }`}
                  >
                    {item}
                  </button>
                ))}
              </div>
              {mode === 'exam' && (
                <p className="mt-2 text-xs text-[var(--color-text-subtle)]">
                  Answers and explanations are hidden until you submit the exam.
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
              <p className="text-xs text-[var(--color-danger)]">{mutation.error.message}</p>
            )}
          </div>
        </Card>
      </div>

      <PracticeHistory />
    </div>
  )
}
