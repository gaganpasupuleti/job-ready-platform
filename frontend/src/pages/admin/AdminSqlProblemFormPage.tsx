import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiClient } from '@/api/client'
import { apiEndpoints } from '@/api/config'
import { Button } from '@/components/common/Button'
import { Card } from '@/components/common/Card'
import {
  createAdminSqlProblem,
  fetchAdminSqlProblem,
  updateAdminSqlProblem,
  validateAdminSqlProblem,
} from '@/services/sqlService'
import type { AdminSqlValidateResponse, Difficulty } from '@/types/sql'

interface TaxonomyDomain {
  id: string
  slug: string
  categories: {
    id: string
    slug: string
    topics: { id: string; slug: string; name: string }[]
  }[]
}

const DEFAULT_TABLES_JSON = `[
  {
    "table_name": "employees",
    "display_name": "Employees",
    "description": "Sample employees table",
    "sort_order": 0,
    "columns": [
      { "column_name": "id", "data_type": "INTEGER", "is_nullable": false, "sort_order": 0 },
      { "column_name": "name", "data_type": "TEXT", "is_nullable": false, "sort_order": 1 }
    ],
    "rows": [
      { "id": 1, "name": "Alice" },
      { "id": 2, "name": "Bob" }
    ]
  }
]`

export function AdminSqlProblemFormPage() {
  const { problemId } = useParams()
  const isEdit = Boolean(problemId)
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [slug, setSlug] = useState('')
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [scenario, setScenario] = useState('')
  const [taskDescription, setTaskDescription] = useState('')
  const [difficulty, setDifficulty] = useState<Difficulty>('easy')
  const [domainId, setDomainId] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [topicId, setTopicId] = useState('')
  const [tagsText, setTagsText] = useState('')
  const [roleTagsText, setRoleTagsText] = useState('')
  const [expectedColumnsText, setExpectedColumnsText] = useState('')
  const [orderSensitive, setOrderSensitive] = useState(false)
  const [solutionQuery, setSolutionQuery] = useState('')
  const [solutionExplanation, setSolutionExplanation] = useState('')
  const [alternateSolution, setAlternateSolution] = useState('')
  const [keyConceptsText, setKeyConceptsText] = useState('')
  const [hintsText, setHintsText] = useState('')
  const [sampleExpectedRowsJson, setSampleExpectedRowsJson] = useState('[]')
  const [expectedRowsJson, setExpectedRowsJson] = useState('[]')
  const [tablesJson, setTablesJson] = useState(DEFAULT_TABLES_JSON)
  const [estimatedTimeSeconds, setEstimatedTimeSeconds] = useState(300)
  const [isActive, setIsActive] = useState(true)
  const [isSample, setIsSample] = useState(true)
  const [formError, setFormError] = useState<string | null>(null)
  const [validateResult, setValidateResult] = useState<AdminSqlValidateResponse | null>(null)

  const { data: taxonomy } = useQuery({
    queryKey: ['admin-taxonomy'],
    queryFn: async () => {
      const { data } = await apiClient.get<{ domains: TaxonomyDomain[] }>(
        apiEndpoints.admin.taxonomy,
      )
      return data.domains
    },
  })

  const { data: existing } = useQuery({
    queryKey: ['admin-sql-problem', problemId],
    queryFn: () => fetchAdminSqlProblem(problemId!),
    enabled: isEdit,
  })

  useEffect(() => {
    if (!existing) return
    setSlug(existing.slug)
    setTitle(existing.title)
    setDescription(existing.description)
    setScenario(existing.scenario ?? '')
    setTaskDescription(existing.task_description)
    setDifficulty(existing.difficulty)
    setDomainId(existing.domain_id)
    setCategoryId(existing.category_id)
    setTopicId(existing.topic_id)
    setTagsText((existing.tags ?? []).join(', '))
    setRoleTagsText((existing.role_tags ?? []).join(', '))
    setExpectedColumnsText((existing.expected_columns ?? []).join(', '))
    setOrderSensitive(existing.order_sensitive)
    setSolutionQuery(existing.solution_query)
    setSolutionExplanation(existing.solution_explanation ?? '')
    setAlternateSolution(existing.alternate_solution ?? '')
    setKeyConceptsText((existing.key_concepts ?? []).join(', '))
    setHintsText((existing.hints ?? []).join('\n'))
    setSampleExpectedRowsJson(JSON.stringify(existing.sample_expected_rows ?? [], null, 2))
    setExpectedRowsJson(JSON.stringify(existing.expected_rows ?? [], null, 2))
    setTablesJson(JSON.stringify(existing.tables ?? [], null, 2))
    setEstimatedTimeSeconds(existing.estimated_time_seconds)
    setIsActive(existing.is_active)
    setIsSample(existing.is_sample)
  }, [existing])

  useEffect(() => {
    if (!taxonomy || domainId) return
    const technical = taxonomy.find((d) => d.slug === 'technical')
    const sqlCat =
      technical?.categories.find((c) => c.slug === 'sql') ??
      technical?.categories.find((c) => c.slug.includes('sql'))
    if (technical && sqlCat) {
      setDomainId(technical.id)
      setCategoryId(sqlCat.id)
      setTopicId(sqlCat.topics[0]?.id ?? '')
    }
  }, [taxonomy, domainId])

  const buildPayload = () => {
    const tables = JSON.parse(tablesJson)
    const expectedRows = JSON.parse(expectedRowsJson)
    const sampleExpectedRows = JSON.parse(sampleExpectedRowsJson)
    const tags = tagsText
      .split(',')
      .map((t) => t.trim())
      .filter(Boolean)
    const roleTags = roleTagsText
      .split(',')
      .map((t) => t.trim())
      .filter(Boolean)
    const expectedColumns = expectedColumnsText
      .split(',')
      .map((t) => t.trim())
      .filter(Boolean)
    const keyConcepts = keyConceptsText
      .split(',')
      .map((t) => t.trim())
      .filter(Boolean)
    const hints = hintsText
      .split('\n')
      .map((t) => t.trim())
      .filter(Boolean)

    return {
      slug,
      title,
      description,
      difficulty,
      domain_id: domainId,
      category_id: categoryId,
      topic_id: topicId,
      tags,
      role_tags: roleTags,
      scenario: scenario || null,
      task_description: taskDescription,
      expected_columns: expectedColumns,
      order_sensitive: orderSensitive,
      solution_query: solutionQuery,
      solution_explanation: solutionExplanation || null,
      alternate_solution: alternateSolution || null,
      key_concepts: keyConcepts,
      hints,
      sample_expected_rows: sampleExpectedRows,
      estimated_time_seconds: estimatedTimeSeconds,
      is_active: isActive,
      is_sample: isSample,
      tables,
      expected_rows: expectedRows,
    }
  }

  const saveMutation = useMutation({
    mutationFn: async () => {
      setFormError(null)
      try {
        const payload = buildPayload()
        if (isEdit) return updateAdminSqlProblem(problemId!, payload)
        return createAdminSqlProblem(payload)
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Invalid JSON in form fields'
        setFormError(message)
        throw err
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-sql-problems'] })
      navigate('/admin/sql')
    },
  })

  const validateMutation = useMutation({
    mutationFn: () => validateAdminSqlProblem(problemId!),
    onSuccess: (data) => setValidateResult(data),
  })

  const selectedDomain = taxonomy?.find((d) => d.id === domainId)
  const categories = selectedDomain?.categories ?? []
  const topics = categories.find((c) => c.id === categoryId)?.topics ?? []

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <Link to="/admin/sql" className="text-xs text-[var(--color-accent)] hover:underline">
          ← Back to SQL problems
        </Link>
        <h2 className="text-lg font-semibold text-[var(--color-text)]">
          {isEdit ? 'Edit SQL problem' : 'New SQL problem'}
        </h2>
      </div>

      <Card padding="lg" className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Slug">
            <input
              value={slug}
              onChange={(e) => setSlug(e.target.value)}
              className="input-field"
              disabled={isEdit}
            />
          </Field>
          <Field label="Title">
            <input value={title} onChange={(e) => setTitle(e.target.value)} className="input-field" />
          </Field>
        </div>

        <Field label="Description">
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={4}
            className="input-field"
          />
        </Field>
        <Field label="Scenario">
          <textarea
            value={scenario}
            onChange={(e) => setScenario(e.target.value)}
            rows={3}
            className="input-field"
          />
        </Field>
        <Field label="Task description">
          <textarea
            value={taskDescription}
            onChange={(e) => setTaskDescription(e.target.value)}
            rows={3}
            className="input-field"
          />
        </Field>

        <div className="grid gap-4 sm:grid-cols-3">
          <Field label="Difficulty">
            <select
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value as Difficulty)}
              className="input-field"
            >
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>
          </Field>
          <Field label="Estimated time (seconds)">
            <input
              type="number"
              value={estimatedTimeSeconds}
              onChange={(e) => setEstimatedTimeSeconds(Number(e.target.value))}
              className="input-field"
            />
          </Field>
          <Field label="Expected columns (comma-separated)">
            <input
              value={expectedColumnsText}
              onChange={(e) => setExpectedColumnsText(e.target.value)}
              className="input-field"
            />
          </Field>
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          <Field label="Domain">
            <select
              value={domainId}
              onChange={(e) => {
                setDomainId(e.target.value)
                setCategoryId('')
                setTopicId('')
              }}
              className="input-field"
            >
              <option value="">Select domain</option>
              {taxonomy?.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.slug}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Category">
            <select
              value={categoryId}
              onChange={(e) => {
                setCategoryId(e.target.value)
                setTopicId('')
              }}
              className="input-field"
            >
              <option value="">Select category</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.slug}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Topic">
            <select
              value={topicId}
              onChange={(e) => setTopicId(e.target.value)}
              className="input-field"
            >
              <option value="">Select topic</option>
              {topics.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
          </Field>
        </div>

        <Field label="Tags (comma-separated)">
          <input value={tagsText} onChange={(e) => setTagsText(e.target.value)} className="input-field" />
        </Field>
        <Field label="Role tags (comma-separated)">
          <input
            value={roleTagsText}
            onChange={(e) => setRoleTagsText(e.target.value)}
            className="input-field"
          />
        </Field>
        <Field label="Key concepts (comma-separated)">
          <input
            value={keyConceptsText}
            onChange={(e) => setKeyConceptsText(e.target.value)}
            className="input-field"
          />
        </Field>
        <Field label="Hints (one per line)">
          <textarea
            value={hintsText}
            onChange={(e) => setHintsText(e.target.value)}
            rows={3}
            className="input-field"
          />
        </Field>

        <Field label="Solution query">
          <textarea
            value={solutionQuery}
            onChange={(e) => setSolutionQuery(e.target.value)}
            rows={6}
            className="input-field font-mono text-xs"
          />
        </Field>
        <Field label="Solution explanation">
          <textarea
            value={solutionExplanation}
            onChange={(e) => setSolutionExplanation(e.target.value)}
            rows={3}
            className="input-field"
          />
        </Field>
        <Field label="Alternate solution">
          <textarea
            value={alternateSolution}
            onChange={(e) => setAlternateSolution(e.target.value)}
            rows={4}
            className="input-field font-mono text-xs"
          />
        </Field>

        <Field label="Tables JSON">
          <textarea
            value={tablesJson}
            onChange={(e) => setTablesJson(e.target.value)}
            rows={12}
            className="input-field font-mono text-xs"
          />
        </Field>
        <Field label="Expected rows JSON">
          <textarea
            value={expectedRowsJson}
            onChange={(e) => setExpectedRowsJson(e.target.value)}
            rows={6}
            className="input-field font-mono text-xs"
          />
        </Field>
        <Field label="Sample expected rows JSON (visible to students)">
          <textarea
            value={sampleExpectedRowsJson}
            onChange={(e) => setSampleExpectedRowsJson(e.target.value)}
            rows={4}
            className="input-field font-mono text-xs"
          />
        </Field>

        <div className="flex flex-wrap gap-4 text-sm">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={orderSensitive}
              onChange={(e) => setOrderSensitive(e.target.checked)}
            />
            Order sensitive
          </label>
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={isActive} onChange={(e) => setIsActive(e.target.checked)} />
            Active
          </label>
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={isSample} onChange={(e) => setIsSample(e.target.checked)} />
            Sample
          </label>
        </div>

        {formError && <p className="text-sm text-red-600 dark:text-red-400">{formError}</p>}

        {validateResult && (
          <div className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface-muted)] p-3 text-sm">
            <p className="font-medium">{validateResult.valid ? 'Valid' : 'Invalid'}</p>
            {validateResult.errors.length > 0 && (
              <ul className="mt-2 list-inside list-disc text-red-600 dark:text-red-400">
                {validateResult.errors.map((err) => (
                  <li key={err}>{err}</li>
                ))}
              </ul>
            )}
            {validateResult.warnings.length > 0 && (
              <ul className="mt-2 list-inside list-disc text-amber-700 dark:text-amber-300">
                {validateResult.warnings.map((w) => (
                  <li key={w}>{w}</li>
                ))}
              </ul>
            )}
            {validateResult.solution_row_count != null && (
              <p className="mt-2 text-[var(--color-text-muted)]">
                Solution returns {validateResult.solution_row_count} rows
                {validateResult.solution_columns.length > 0 &&
                  ` · columns: ${validateResult.solution_columns.join(', ')}`}
              </p>
            )}
          </div>
        )}

        <div className="flex flex-wrap gap-2">
          {isEdit && (
            <Button
              variant="secondary"
              disabled={validateMutation.isPending}
              onClick={() => validateMutation.mutate()}
            >
              {validateMutation.isPending ? 'Validating...' : 'Validate'}
            </Button>
          )}
          <Button
            variant="primary"
            disabled={saveMutation.isPending}
            onClick={() => saveMutation.mutate()}
          >
            {saveMutation.isPending ? 'Saving...' : isEdit ? 'Update problem' : 'Create problem'}
          </Button>
        </div>
      </Card>

      <style>{`.input-field { width: 100%; border-radius: 0.375rem; border: 1px solid var(--color-border); background: var(--color-surface); padding: 0.5rem 0.75rem; font-size: 0.875rem; }`}</style>
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-medium text-[var(--color-text-muted)]">{label}</span>
      {children}
    </label>
  )
}
