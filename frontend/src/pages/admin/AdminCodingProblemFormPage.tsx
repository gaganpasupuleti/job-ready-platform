import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { Button } from '@/components/common/Button'
import { Card } from '@/components/common/Card'
import { SUPPORTED_LANGUAGES } from '@/constants/languages'
import { apiClient } from '@/api/client'
import { apiEndpoints } from '@/api/config'
import {
  createAdminCodingProblem,
  fetchAdminCodingProblem,
  updateAdminCodingProblem,
} from '@/services/codingService'
import type { AdminTestCase, Difficulty } from '@/types/coding'

interface TaxonomyDomain {
  id: string
  slug: string
  categories: {
    id: string
    slug: string
    topics: { id: string; slug: string; name: string }[]
  }[]
}

const DEFAULT_STARTERS: Record<number, string> = {
  71: "import sys\nprint(sys.stdin.read().strip())",
  62: 'import java.util.Scanner;\npublic class Main {\n  public static void main(String[] args) {\n    Scanner sc = new Scanner(System.in);\n    System.out.println(sc.nextLine());\n  }\n}',
  54: '#include <iostream>\nusing namespace std;\nint main() { string s; getline(cin, s); cout << s; return 0; }',
  63: "const fs = require('fs');\nconsole.log(fs.readFileSync(0, 'utf8').trim());",
}

export function AdminCodingProblemFormPage() {
  const { problemId } = useParams()
  const isEdit = Boolean(problemId)
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [slug, setSlug] = useState('')
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [constraints, setConstraints] = useState('')
  const [inputFormat, setInputFormat] = useState('')
  const [outputFormat, setOutputFormat] = useState('')
  const [tagsText, setTagsText] = useState('')
  const [difficulty, setDifficulty] = useState<Difficulty>('easy')
  const [domainId, setDomainId] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [topicId, setTopicId] = useState('')
  const [timeLimitMs, setTimeLimitMs] = useState(2000)
  const [memoryLimitKb, setMemoryLimitKb] = useState(262144)
  const [isActive, setIsActive] = useState(true)
  const [starterCode, setStarterCode] = useState<Record<string, string>>({
    '71': DEFAULT_STARTERS[71],
  })
  const [supportedLanguageIds, setSupportedLanguageIds] = useState<number[]>([71])
  const [testCases, setTestCases] = useState<AdminTestCase[]>([
    { name: 'Sample', input: '', expected_output: '', is_hidden: false, is_sample: true },
  ])

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
    queryKey: ['admin-coding-problem', problemId],
    queryFn: () => fetchAdminCodingProblem(problemId!),
    enabled: isEdit,
  })

  useEffect(() => {
    if (!existing) return
    setSlug(existing.slug)
    setTitle(existing.title)
    setDescription(existing.description)
    setConstraints(existing.constraints ?? '')
    setInputFormat(existing.input_format ?? '')
    setOutputFormat(existing.output_format ?? '')
    setTagsText((existing.tags ?? []).join(', '))
    setDifficulty(existing.difficulty)
    setDomainId(existing.domain_id)
    setCategoryId(existing.category_id)
    setTopicId(existing.topic_id)
    setTimeLimitMs(existing.time_limit_ms)
    setMemoryLimitKb(existing.memory_limit_kb)
    setIsActive(existing.is_active)
    setStarterCode(existing.starter_code)
    setSupportedLanguageIds(existing.supported_language_ids?.length ? existing.supported_language_ids : [71])
    setTestCases(
      existing.test_cases.map((tc) => ({
        name: tc.name,
        input: tc.input,
        expected_output: tc.expected_output,
        is_hidden: tc.is_hidden,
        is_sample: tc.is_sample,
        sort_order: tc.sort_order,
        explanation: tc.explanation,
      })),
    )
  }, [existing])

  useEffect(() => {
    if (!taxonomy || domainId) return
    const technical = taxonomy.find((d) => d.slug === 'technical')
    const dsa = technical?.categories.find((c) => c.slug === 'dsa')
    if (technical && dsa) {
      setDomainId(technical.id)
      setCategoryId(dsa.id)
      setTopicId(dsa.topics[0]?.id ?? '')
    }
  }, [taxonomy, domainId])

  const toggleLanguage = (langId: number) => {
    setSupportedLanguageIds((prev) => {
      const next = prev.includes(langId) ? prev.filter((id) => id !== langId) : [...prev, langId]
      if (!next.includes(langId) && prev.includes(langId)) {
        setStarterCode((starters) => {
          const copy = { ...starters }
          delete copy[String(langId)]
          return copy
        })
      } else if (next.includes(langId) && !starterCode[String(langId)]) {
        setStarterCode((starters) => ({
          ...starters,
          [String(langId)]: DEFAULT_STARTERS[langId] ?? '',
        }))
      }
      return next.length ? next : [71]
    })
  }

  const saveMutation = useMutation({
    mutationFn: async () => {
      const tags = tagsText
        .split(',')
        .map((t) => t.trim())
        .filter(Boolean)
      const payload = {
        slug,
        title,
        description,
        difficulty,
        domain_id: domainId,
        category_id: categoryId,
        topic_id: topicId,
        constraints: constraints || null,
        input_format: inputFormat || null,
        output_format: outputFormat || null,
        tags,
        supported_language_ids: supportedLanguageIds,
        time_limit_ms: timeLimitMs,
        memory_limit_kb: memoryLimitKb,
        is_active: isActive,
        starter_code: starterCode,
        test_cases: testCases,
      }
      if (isEdit) return updateAdminCodingProblem(problemId!, payload)
      return createAdminCodingProblem(payload)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-coding-problems'] })
      navigate('/admin/coding')
    },
  })

  const selectedDomain = taxonomy?.find((d) => d.id === domainId)
  const categories = selectedDomain?.categories ?? []
  const topics = categories.find((c) => c.id === categoryId)?.topics ?? []

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <Link to="/admin/coding" className="text-xs text-[var(--color-accent)] hover:underline">
          ← Back to coding problems
        </Link>
        <h2 className="text-lg font-semibold text-[var(--color-text)]">
          {isEdit ? 'Edit coding problem' : 'New coding problem'}
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
            rows={5}
            className="input-field"
          />
        </Field>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Input format">
            <textarea
              value={inputFormat}
              onChange={(e) => setInputFormat(e.target.value)}
              rows={3}
              className="input-field"
            />
          </Field>
          <Field label="Output format">
            <textarea
              value={outputFormat}
              onChange={(e) => setOutputFormat(e.target.value)}
              rows={3}
              className="input-field"
            />
          </Field>
        </div>
        <Field label="Constraints">
          <textarea
            value={constraints}
            onChange={(e) => setConstraints(e.target.value)}
            rows={2}
            className="input-field"
          />
        </Field>
        <Field label="Tags (comma-separated)">
          <input value={tagsText} onChange={(e) => setTagsText(e.target.value)} className="input-field" />
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
          <Field label="Time limit (ms)">
            <input
              type="number"
              value={timeLimitMs}
              onChange={(e) => setTimeLimitMs(Number(e.target.value))}
              className="input-field"
            />
          </Field>
          <Field label="Memory limit (KB)">
            <input
              type="number"
              value={memoryLimitKb}
              onChange={(e) => setMemoryLimitKb(Number(e.target.value))}
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
            <select value={topicId} onChange={(e) => setTopicId(e.target.value)} className="input-field">
              <option value="">Select topic</option>
              {topics.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
          </Field>
        </div>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={isActive} onChange={(e) => setIsActive(e.target.checked)} />
          Active
        </label>

        <div>
          <h3 className="mb-2 text-sm font-medium">Supported languages</h3>
          <div className="flex flex-wrap gap-2">
            {SUPPORTED_LANGUAGES.map((lang) => (
              <label key={lang.id} className="flex items-center gap-1 text-sm">
                <input
                  type="checkbox"
                  checked={supportedLanguageIds.includes(lang.id)}
                  onChange={() => toggleLanguage(lang.id)}
                />
                {lang.shortLabel}
              </label>
            ))}
          </div>
        </div>

        <div className="space-y-4">
          <h3 className="text-sm font-medium">Starter code</h3>
          {supportedLanguageIds.map((langId) => {
            const lang = SUPPORTED_LANGUAGES.find((l) => l.id === langId)
            return (
              <Field key={langId} label={lang?.name ?? `Language ${langId}`}>
                <textarea
                  value={starterCode[String(langId)] ?? ''}
                  onChange={(e) =>
                    setStarterCode((prev) => ({ ...prev, [String(langId)]: e.target.value }))
                  }
                  rows={8}
                  className="input-field font-mono text-xs"
                />
              </Field>
            )
          })}
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium">Test cases</h3>
            <Button
              variant="secondary"
              onClick={() =>
                setTestCases((prev) => [
                  ...prev,
                  {
                    name: `Case ${prev.length + 1}`,
                    input: '',
                    expected_output: '',
                    is_hidden: false,
                    is_sample: false,
                  },
                ])
              }
            >
              Add test case
            </Button>
          </div>
          {testCases.map((tc, index) => (
            <div
              key={index}
              className="space-y-2 rounded-md border border-[var(--color-border)] p-3"
            >
              <input
                value={tc.name ?? ''}
                onChange={(e) =>
                  setTestCases((prev) =>
                    prev.map((item, i) => (i === index ? { ...item, name: e.target.value } : item)),
                  )
                }
                placeholder="Name"
                className="input-field"
              />
              <textarea
                value={tc.input}
                onChange={(e) =>
                  setTestCases((prev) =>
                    prev.map((item, i) => (i === index ? { ...item, input: e.target.value } : item)),
                  )
                }
                placeholder="Input"
                rows={2}
                className="input-field font-mono text-xs"
              />
              <textarea
                value={tc.expected_output}
                onChange={(e) =>
                  setTestCases((prev) =>
                    prev.map((item, i) =>
                      i === index ? { ...item, expected_output: e.target.value } : item,
                    ),
                  )
                }
                placeholder="Expected output"
                rows={2}
                className="input-field font-mono text-xs"
              />
              <div className="flex gap-4 text-sm">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={tc.is_sample}
                    onChange={(e) =>
                      setTestCases((prev) =>
                        prev.map((item, i) =>
                          i === index ? { ...item, is_sample: e.target.checked } : item,
                        ),
                      )
                    }
                  />
                  Sample (visible to students)
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={tc.is_hidden}
                    onChange={(e) =>
                      setTestCases((prev) =>
                        prev.map((item, i) =>
                          i === index ? { ...item, is_hidden: e.target.checked } : item,
                        ),
                      )
                    }
                  />
                  Hidden
                </label>
              </div>
            </div>
          ))}
        </div>

        <Button variant="primary" disabled={saveMutation.isPending} onClick={() => saveMutation.mutate()}>
          {saveMutation.isPending ? 'Saving...' : isEdit ? 'Update problem' : 'Create problem'}
        </Button>
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
