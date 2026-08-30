import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Button } from '@/components/common/Button'
import { createAdminScenario, fetchAdminScenario, updateAdminScenario } from '@/services/infraService'

const EMPTY_STEPS = `[
  {
    "prompt": "What should you do first?",
    "context_snippet": "",
    "is_critical": true,
    "explanation": "Explain the correct decision.",
    "scoring_weight": 1,
    "options": [
      {"label": "Correct action", "is_correct": true, "explanation": ""},
      {"label": "Unsafe or irrelevant action", "is_correct": false, "explanation": ""}
    ]
  }
]`

export function AdminScenarioFormPage() {
  const { id } = useParams()
  const isEdit = Boolean(id)
  const navigate = useNavigate()
  const { data } = useQuery({
    queryKey: ['admin-scenario', id],
    queryFn: () => fetchAdminScenario(id!),
    enabled: isEdit,
  })

  const [title, setTitle] = useState('')
  const [slug, setSlug] = useState('')
  const [domain, setDomain] = useState('cloud')
  const [scenarioType, setScenarioType] = useState('architecture')
  const [difficulty, setDifficulty] = useState('medium')
  const [context, setContext] = useState('')
  const [description, setDescription] = useState('')
  const [tag, setTag] = useState('')
  const [mastery, setMastery] = useState(80)
  const [active, setActive] = useState(false)
  const [stepsJson, setStepsJson] = useState(EMPTY_STEPS)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!data) return
    setTitle(String(data.title ?? ''))
    setSlug(String(data.slug ?? ''))
    setDomain(String(data.domain_key ?? 'cloud'))
    setScenarioType(String(data.scenario_type ?? 'architecture'))
    setDifficulty(String(data.difficulty ?? 'medium'))
    setContext(String(data.context_text ?? ''))
    setDescription(String(data.description ?? ''))
    setTag(String(data.unofficial_cert_tag ?? ''))
    setMastery(Number(data.mastery_threshold ?? 80))
    setActive(Boolean(data.is_active))
    if (data.steps) setStepsJson(JSON.stringify(data.steps, null, 2))
  }, [data])

  async function onSave() {
    setError('')
    let steps
    try {
      steps = JSON.parse(stepsJson)
    } catch {
      setError('Steps must be valid JSON')
      return
    }
    const body = {
      slug,
      title,
      description,
      domain_key: domain,
      scenario_type: scenarioType,
      difficulty,
      context_text: context,
      unofficial_cert_tag: tag || null,
      mastery_threshold: mastery,
      is_active: active,
      steps,
    }
    try {
      if (isEdit && id) {
        await updateAdminScenario(id, body)
      } else {
        await createAdminScenario(body)
      }
      navigate('/admin/scenarios')
    } catch {
      setError('Save failed. Check validation and unique slug.')
    }
  }

  return (
    <div className="space-y-4">
      <Link to="/admin/scenarios" className="text-sm text-[var(--color-accent)] hover:underline">
        Back
      </Link>
      <h2 className="text-lg font-semibold">{isEdit ? 'Edit scenario' : 'New scenario'}</h2>
      <p className="text-xs text-[var(--color-text-subtle)]">
        Unofficial preparation. Not affiliated with any certification vendor. Cyber content must stay defensive.
      </p>
      {error && <p className="text-sm text-[var(--color-danger)]">{error}</p>}
      <div className="grid gap-3 md:grid-cols-2">
        <input className="rounded border p-2 text-sm" placeholder="Title" value={title} onChange={(e) => setTitle(e.target.value)} />
        <input className="rounded border p-2 text-sm" placeholder="Slug" value={slug} onChange={(e) => setSlug(e.target.value)} disabled={isEdit} />
        <select className="rounded border p-2 text-sm" value={domain} onChange={(e) => setDomain(e.target.value)}>
          <option value="cloud">cloud</option>
          <option value="devops">devops</option>
          <option value="cybersecurity">cybersecurity</option>
        </select>
        <select className="rounded border p-2 text-sm" value={scenarioType} onChange={(e) => setScenarioType(e.target.value)}>
          <option value="architecture">architecture</option>
          <option value="troubleshooting">troubleshooting</option>
          <option value="incident_response">incident_response</option>
          <option value="security_review">security_review</option>
          <option value="deployment">deployment</option>
          <option value="observability">observability</option>
          <option value="decision_tree">decision_tree</option>
        </select>
        <select className="rounded border p-2 text-sm" value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
          <option value="easy">easy</option>
          <option value="medium">medium</option>
          <option value="hard">hard</option>
        </select>
        <input className="rounded border p-2 text-sm" placeholder="Unofficial cert tag" value={tag} onChange={(e) => setTag(e.target.value)} />
      </div>
      <textarea className="h-24 w-full rounded border p-2 text-sm" placeholder="Description" value={description} onChange={(e) => setDescription(e.target.value)} />
      <textarea className="h-32 w-full rounded border p-2 text-sm" placeholder="Context" value={context} onChange={(e) => setContext(e.target.value)} />
      <label className="flex items-center gap-2 text-sm">
        <input type="checkbox" checked={active} onChange={(e) => setActive(e.target.checked)} /> Active
      </label>
      <label className="text-sm">
        Mastery threshold
        <input
          className="ml-2 rounded border p-1"
          type="number"
          value={mastery}
          onChange={(e) => setMastery(Number(e.target.value))}
        />
      </label>
      <textarea className="h-64 w-full rounded border p-2 font-mono text-xs" value={stepsJson} onChange={(e) => setStepsJson(e.target.value)} />
      <Button onClick={onSave}>Save</Button>
    </div>
  )
}
