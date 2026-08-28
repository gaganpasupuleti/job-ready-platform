import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
import { apiClient } from '@/api/client'
import { apiEndpoints } from '@/api/config'
import type { CatalogResponse } from '@/types/practice'

export function AdminQuestionFormPage() {
  const navigate = useNavigate()
  const { data: catalog } = useQuery({
    queryKey: ['admin-taxonomy'],
    queryFn: async () => {
      const { data } = await apiClient.get<CatalogResponse>(apiEndpoints.admin.taxonomy)
      return data
    },
  })

  const [domainId, setDomainId] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [topicId, setTopicId] = useState('')
  const [questionText, setQuestionText] = useState('')
  const [explanation, setExplanation] = useState('')
  const [difficulty, setDifficulty] = useState('medium')
  const [options, setOptions] = useState([
    { option_text: '', is_correct: true, sort_order: 0 },
    { option_text: '', is_correct: false, sort_order: 1 },
    { option_text: '', is_correct: false, sort_order: 2 },
    { option_text: '', is_correct: false, sort_order: 3 },
  ])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const selectedDomain = catalog?.domains.find((d) => d.id === domainId)
  const selectedCategory = selectedDomain?.categories.find((c) => c.id === categoryId)

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    setLoading(true)
    setError(null)
    try {
      await apiClient.post(apiEndpoints.admin.questions, {
        question_type: 'single_choice',
        question_text: questionText,
        explanation,
        difficulty,
        domain_id: domainId,
        category_id: categoryId,
        topic_id: topicId,
        marks: 1,
        negative_marks: 0.25,
        estimated_time_seconds: 60,
        is_active: true,
        options,
      })
      navigate('/admin/questions')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create question')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-[var(--color-text)]">New Question</h2>
        <Link to="/admin/questions">
          <Button variant="secondary">Back</Button>
        </Link>
      </div>
      <Card padding="lg">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-3">
            <select
              required
              value={domainId}
              onChange={(e) => {
                setDomainId(e.target.value)
                setCategoryId('')
                setTopicId('')
              }}
              className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm"
            >
              <option value="">Domain</option>
              {catalog?.domains.map((domain) => (
                <option key={domain.id} value={domain.id}>
                  {domain.name}
                </option>
              ))}
            </select>
            <select
              required
              value={categoryId}
              onChange={(e) => {
                setCategoryId(e.target.value)
                setTopicId('')
              }}
              className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm"
            >
              <option value="">Category</option>
              {selectedDomain?.categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
            <select
              required
              value={topicId}
              onChange={(e) => setTopicId(e.target.value)}
              className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm"
            >
              <option value="">Topic</option>
              {selectedCategory?.topics.map((topic) => (
                <option key={topic.id} value={topic.id}>
                  {topic.name}
                </option>
              ))}
            </select>
          </div>
          <textarea
            required
            rows={4}
            placeholder="Question text"
            value={questionText}
            onChange={(e) => setQuestionText(e.target.value)}
            className="w-full rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm"
          />
          <textarea
            rows={3}
            placeholder="Explanation"
            value={explanation}
            onChange={(e) => setExplanation(e.target.value)}
            className="w-full rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm"
          />
          <select
            value={difficulty}
            onChange={(e) => setDifficulty(e.target.value)}
            className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm"
          >
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </select>
          <CardHeader title="Options" description="Mark one option as correct" />
          {options.map((option, index) => (
            <div key={index} className="flex gap-2">
              <input
                required
                value={option.option_text}
                onChange={(e) =>
                  setOptions((prev) =>
                    prev.map((item, i) =>
                      i === index ? { ...item, option_text: e.target.value } : item,
                    ),
                  )
                }
                className="flex-1 rounded-md border border-[var(--color-border)] px-3 py-2 text-sm"
              />
              <label className="flex items-center gap-1 text-xs">
                <input
                  type="radio"
                  checked={option.is_correct}
                  onChange={() =>
                    setOptions((prev) =>
                      prev.map((item, i) => ({ ...item, is_correct: i === index })),
                    )
                  }
                />
                Correct
              </label>
            </div>
          ))}
          {error && <p className="text-xs text-[var(--color-danger)]">{error}</p>}
          <Button type="submit" variant="primary" disabled={loading}>
            {loading ? 'Saving...' : 'Create Question'}
          </Button>
        </form>
      </Card>
    </div>
  )
}
