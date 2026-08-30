import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
import {
  createAdminPrompt,
  fetchAdminPrompt,
  updateAdminPrompt,
  validateAdminPrompt,
} from '@/services/aiService'

const EMPTY_CASES = `[
  {
    "input_text": "",
    "variables": {"ticket_text": "Need a refund"},
    "is_hidden": false,
    "hide_input": false,
    "weight": 1,
    "evaluation_config": {
      "require_all": true,
      "checks": [
        {"type": "variable_used", "names": ["ticket_text"]},
        {"type": "contains", "value": "json"}
      ]
    }
  }
]`

export function AdminPromptFormPage() {
  const { id } = useParams()
  const isEdit = Boolean(id)
  const navigate = useNavigate()
  const { data } = useQuery({
    queryKey: ['admin-prompt', id],
    queryFn: () => fetchAdminPrompt(id!),
    enabled: isEdit,
  })

  const [title, setTitle] = useState('')
  const [slug, setSlug] = useState('')
  const [difficulty, setDifficulty] = useState('easy')
  const [taskType, setTaskType] = useState('classification')
  const [scenario, setScenario] = useState('')
  const [instructions, setInstructions] = useState('')
  const [starter, setStarter] = useState('')
  const [mastery, setMastery] = useState(80)
  const [active, setActive] = useState(false)
  const [casesJson, setCasesJson] = useState(EMPTY_CASES)
  const [rubricJson, setRubricJson] = useState('{"task_accuracy":30,"format_compliance":20,"robustness":15,"instruction_following":15,"safety":10,"efficiency":10}')
  const [error, setError] = useState('')
  const [validation, setValidation] = useState('')

  useEffect(() => {
    if (!data) return
    setTitle(String(data.title ?? ''))
    setSlug(String(data.slug ?? ''))
    setDifficulty(String(data.difficulty ?? 'easy'))
    setTaskType(String(data.task_type ?? 'classification'))
    setScenario(String(data.scenario ?? ''))
    setInstructions(String(data.instructions ?? ''))
    setStarter(String(data.starter_prompt ?? ''))
    setMastery(Number(data.mastery_threshold ?? 80))
    setActive(Boolean(data.is_active))
    if (data.cases) setCasesJson(JSON.stringify(data.cases, null, 2))
    if (data.rubric_weights) setRubricJson(JSON.stringify(data.rubric_weights))
  }, [data])

  async function onSave() {
    setError('')
    let cases
    let rubric
    try {
      cases = JSON.parse(casesJson)
      rubric = JSON.parse(rubricJson)
    } catch {
      setError('Cases and rubric must be valid JSON')
      return
    }
    const payload = {
      slug,
      title,
      description: scenario,
      difficulty,
      task_type: taskType,
      scenario,
      instructions,
      starter_prompt: starter,
      mastery_threshold: mastery,
      rubric_weights: rubric,
      is_active: active,
      cases,
    }
    try {
      if (isEdit && id) {
        await updateAdminPrompt(id, payload)
        navigate('/admin/ai/prompts')
      } else {
        await createAdminPrompt(payload)
        navigate('/admin/ai/prompts')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Save failed')
    }
  }

  async function onValidate() {
    if (!id) return
    const result = await validateAdminPrompt(id)
    setValidation(result.ok ? 'Valid' : result.errors.join('; '))
  }

  return (
    <div className="space-y-4">
      <Link to="/admin/ai/prompts" className="text-sm text-[var(--color-accent)] hover:underline">
        Back
      </Link>
      <h2 className="text-lg font-semibold">{isEdit ? 'Edit challenge' : 'New challenge'}</h2>
      {error && <p className="text-sm text-red-600">{error}</p>}
      {validation && <p className="text-sm">{validation}</p>}
      <Card>
        <CardHeader title="Metadata" />
        <div className="grid gap-3 sm:grid-cols-2">
          <input className="rounded border border-[var(--color-border)] bg-transparent px-3 py-2 text-sm" placeholder="Title" value={title} onChange={(e) => setTitle(e.target.value)} />
          <input className="rounded border border-[var(--color-border)] bg-transparent px-3 py-2 text-sm" placeholder="Slug" value={slug} onChange={(e) => setSlug(e.target.value)} />
          <input className="rounded border border-[var(--color-border)] bg-transparent px-3 py-2 text-sm" placeholder="Difficulty" value={difficulty} onChange={(e) => setDifficulty(e.target.value)} />
          <input className="rounded border border-[var(--color-border)] bg-transparent px-3 py-2 text-sm" placeholder="Task type" value={taskType} onChange={(e) => setTaskType(e.target.value)} />
          <input className="rounded border border-[var(--color-border)] bg-transparent px-3 py-2 text-sm" type="number" value={mastery} onChange={(e) => setMastery(Number(e.target.value))} />
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={active} onChange={(e) => setActive(e.target.checked)} />
            Active
          </label>
        </div>
        <textarea className="mt-3 min-h-[80px] w-full rounded border border-[var(--color-border)] bg-transparent p-2 text-sm" placeholder="Scenario" value={scenario} onChange={(e) => setScenario(e.target.value)} />
        <textarea className="mt-3 min-h-[80px] w-full rounded border border-[var(--color-border)] bg-transparent p-2 text-sm" placeholder="Instructions" value={instructions} onChange={(e) => setInstructions(e.target.value)} />
        <textarea className="mt-3 min-h-[80px] w-full rounded border border-[var(--color-border)] bg-transparent p-2 text-sm" placeholder="Starter prompt" value={starter} onChange={(e) => setStarter(e.target.value)} />
      </Card>
      <Card>
        <CardHeader title="Cases JSON (public + hidden)" />
        <textarea className="min-h-[220px] w-full rounded border border-[var(--color-border)] bg-transparent p-2 font-mono text-xs" value={casesJson} onChange={(e) => setCasesJson(e.target.value)} />
      </Card>
      <Card>
        <CardHeader title="Rubric weights JSON" />
        <textarea className="min-h-[80px] w-full rounded border border-[var(--color-border)] bg-transparent p-2 font-mono text-xs" value={rubricJson} onChange={(e) => setRubricJson(e.target.value)} />
      </Card>
      <div className="flex gap-2">
        <Button onClick={onSave}>Save</Button>
        {isEdit && (
          <Button variant="secondary" onClick={onValidate}>
            Validate
          </Button>
        )}
      </div>
    </div>
  )
}
