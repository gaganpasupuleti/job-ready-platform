import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
import { apiClient } from '@/api/client'
import { apiEndpoints } from '@/api/config'
import type { CatalogResponse, Difficulty } from '@/types/practice'

interface AdminQuestionDetail {
  id: string
  question_type: string
  title: string | null
  question_text: string
  explanation: string | null
  difficulty: Difficulty
  domain_id: string
  category_id: string
  topic_id: string
  marks: number
  negative_marks: number
  estimated_time_seconds: number
  is_active: boolean
  options: Array<{ id?: string; option_text: string; is_correct: boolean; sort_order: number }>
}

export function AdminQuestionFormPage() {
  const { questionId } = useParams()
  const isEdit = Boolean(questionId)
  const navigate = useNavigate()

  const { data: catalog } = useQuery({
    queryKey: ['admin-taxonomy'],
    queryFn: async () => {
      const { data } = await apiClient.get<CatalogResponse>(apiEndpoints.admin.taxonomy)
      return data
    },
  })

  const { data: existing } = useQuery({
    queryKey: ['admin-question', questionId],
    queryFn: async () => {
      const { data } = await apiClient.get<AdminQuestionDetail>(
        apiEndpoints.admin.question(questionId!),
      )
      return data
    },
    enabled: isEdit,
  })

  const [domainId, setDomainId] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [topicId, setTopicId] = useState('')
  const [questionText, setQuestionText] = useState('')
  const [explanation, setExplanation] = useState('')
  const [difficulty, setDifficulty] = useState<Difficulty>('medium')
  const [isActive, setIsActive] = useState(true)
  const [options, setOptions] = useState([
    { option_text: '', is_correct: true, sort_order: 0 },
    { option_text: '', is_correct: false, sort_order: 1 },
    { option_text: '', is_correct: false, sort_order: 2 },
    { option_text: '', is_correct: false, sort_order: 3 },
  ])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!existing) return
    setDomainId(existing.domain_id)
    setCategoryId(existing.category_id)
    setTopicId(existing.topic_id)
    setQuestionText(existing.question_text)
    setExplanation(existing.explanation ?? '')
    setDifficulty(existing.difficulty)
    setIsActive(existing.is_active)
    setOptions(
      existing.options.map((opt, index) => ({
        id: opt.id,
        option_text: opt.option_text,
        is_correct: opt.is_correct,
        sort_order: opt.sort_order ?? index,
      })),
    )
  }, [existing])

  const selectedDomain = catalog?.domains.find((d) => d.id === domainId)
  const selectedCategory = selectedDomain?.categories.find((c) => c.id === categoryId)

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const payload = {
        question_type: 'single_choice',
        question_text: questionText,
        explanation,
        difficulty,
        domain_id: domainId,
        category_id: categoryId,
        topic_id: topicId,
        marks: existing?.marks ?? 1,
        negative_marks: existing?.negative_marks ?? 0.25,
        estimated_time_seconds: existing?.estimated_time_seconds ?? 60,
        is_active: isActive,
        options,
      }
      if (isEdit) {
        await apiClient.put(apiEndpoints.admin.question(questionId!), payload)
      } else {
        await apiClient.post(apiEndpoints.admin.questions, payload)
      }
      navigate('/admin/questions')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save question')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-[var(--color-text)]">
          {isEdit ? 'Edit Question' : 'New Question'}
        </h2>
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
          <div className="grid gap-4 sm:grid-cols-2">
            <select
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value as Difficulty)}
              className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm"
            >
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={isActive}
                onChange={(e) => setIsActive(e.target.checked)}
              />
              Active
            </label>
          </div>
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
            {loading ? 'Saving...' : isEdit ? 'Update Question' : 'Create Question'}
          </Button>
        </form>
      </Card>
    </div>
  )
}
