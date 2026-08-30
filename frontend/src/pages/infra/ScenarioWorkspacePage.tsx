import { useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
import {
  ErrorState,
  LoadingState,
  PracticeProgress,
  PracticeStatusBadge,
  apiErrorMessage,
} from '@/components/practice-workspace/PracticeWorkspace'
import { fetchScenario, fetchScenarios, submitScenario, type ScenarioSubmitResponse } from '@/services/infraService'

function EvidenceCards({ evidence }: { evidence: Record<string, unknown> }) {
  const entries = Object.entries(evidence || {})
  if (!entries.length) return null
  return (
    <div className="grid gap-2 sm:grid-cols-2">
      {entries.map(([key, value]) => {
        const label = key.replace(/_/g, ' ')
        if (value && typeof value === 'object' && !Array.isArray(value)) {
          return (
            <div key={key} className="rounded-md border border-[var(--color-border)] p-3 text-sm">
              <p className="text-xs uppercase text-[var(--color-text-subtle)]">{label}</p>
              {Object.entries(value as Record<string, unknown>).map(([k, v]) => (
                <p key={k}>
                  {k}: {String(v)}
                </p>
              ))}
            </div>
          )
        }
        return (
          <div key={key} className="rounded-md border border-[var(--color-border)] p-3 text-sm">
            <p className="text-xs uppercase text-[var(--color-text-subtle)]">{label}</p>
            <p className="font-medium">{Array.isArray(value) ? value.join('\n') : String(value)}</p>
          </div>
        )
      })}
    </div>
  )
}

export function ScenarioWorkspacePage() {
  const { slug = '' } = useParams()
  const queryClient = useQueryClient()
  const { data, isLoading, error } = useQuery({
    queryKey: ['scenario', slug],
    queryFn: () => fetchScenario(slug),
    enabled: Boolean(slug),
  })
  const { data: siblings } = useQuery({
    queryKey: ['scenarios', data?.domain_key],
    queryFn: () => fetchScenarios(data!.domain_key),
    enabled: Boolean(data?.domain_key),
  })
  const [stepIndex, setStepIndex] = useState(0)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [confirmed, setConfirmed] = useState<Record<string, boolean>>({})
  const [result, setResult] = useState<ScenarioSubmitResponse | null>(null)

  const mutation = useMutation({
    mutationFn: () =>
      submitScenario(
        slug,
        Object.entries(answers).map(([step_id, option_id]) => ({ step_id, option_id })),
      ),
    onSuccess: (body) => {
      setResult(body)
      void queryClient.invalidateQueries({ queryKey: ['scenario', slug] })
    },
  })

  const nextScenario = useMemo(() => {
    if (!siblings || !data) return null
    const idx = siblings.findIndex((item) => item.slug === data.slug)
    return idx >= 0 ? siblings[idx + 1] ?? null : siblings[0] ?? null
  }, [siblings, data])

  if (isLoading) return <LoadingState label="Loading scenario" />
  if (error || !data) return <ErrorState message={apiErrorMessage(error, 'Scenario not found.')} />

  const step = data.steps[stepIndex]
  const selected = step ? answers[step.id] : undefined
  const shownResult = result?.step_results.find((row) => row.step_id === step?.id)

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-semibold">{data.title}</h1>
        <div className="mt-1 flex flex-wrap gap-2">
          <Badge>{data.difficulty}</Badge>
          <Badge>{data.domain_key}</Badge>
          <PracticeStatusBadge status={data.status} />
        </div>
        <div className="mt-3 max-w-sm">
          <PracticeProgress
            percent={Math.round(((stepIndex + (confirmed[step?.id] ? 1 : 0)) / Math.max(data.steps.length, 1)) * 100)}
            label={`Step ${stepIndex + 1} of ${data.steps.length}`}
          />
        </div>
        <div className="mt-2 flex gap-1" aria-label="Step progress">
          {data.steps.map((s, i) => (
            <span key={s.id}>{i < stepIndex || confirmed[s.id] ? '●' : i === stepIndex ? '●' : '○'}</span>
          ))}
        </div>
      </div>

      <Card>
        <CardHeader title="Context" />
        <p className="whitespace-pre-wrap text-sm">{data.context_text}</p>
        <div className="mt-3">
          <EvidenceCards evidence={data.evidence_json || {}} />
        </div>
      </Card>

      {step && !result && (
        <Card>
          <CardHeader title={`Current step${step.is_critical ? ' · critical' : ''}`} />
          {step.context_snippet && <p className="mb-2 text-xs text-[var(--color-text-muted)]">{step.context_snippet}</p>}
          <p className="mb-3 text-sm">{step.prompt}</p>
          <div className="space-y-2">
            {step.options.map((option) => (
              <label key={option.id} className="flex cursor-pointer items-start gap-2 text-sm">
                <input
                  type="radio"
                  name={step.id}
                  checked={selected === option.id}
                  onChange={() => setAnswers((prev) => ({ ...prev, [step.id]: option.id }))}
                  disabled={Boolean(confirmed[step.id])}
                />
                <span>{option.label}</span>
              </label>
            ))}
          </div>
          {!confirmed[step.id] ? (
            <Button
              className="mt-3"
              disabled={!selected}
              onClick={() => setConfirmed((prev) => ({ ...prev, [step.id]: true }))}
            >
              Confirm Decision
            </Button>
          ) : (
            <div className="mt-3 space-y-2">
              <p className="text-sm font-medium">Decision saved for this step.</p>
              {stepIndex + 1 < data.steps.length ? (
                <Button onClick={() => setStepIndex((n) => n + 1)}>Next Step</Button>
              ) : (
                <Button disabled={mutation.isPending} onClick={() => mutation.mutate()}>
                  {mutation.isPending ? 'Submitting...' : 'Submit scenario'}
                </Button>
              )}
            </div>
          )}
        </Card>
      )}

      {mutation.isError && <ErrorState message={apiErrorMessage(mutation.error, 'Could not submit scenario.')} />}

      {result && (
        <Card>
          <CardHeader title={result.mastered ? 'Mastered' : 'Needs Review'} />
          <p className="text-sm">
            Score {result.overall_score} · {result.correct_decisions}/{result.total_steps} correct decisions
          </p>
          <p className="mt-2 text-sm">{result.explanation}</p>
          {result.missed_critical.length > 0 && (
            <div className="mt-2">
              <p className="text-sm font-medium">Missed critical actions</p>
              <ul className="list-disc pl-5 text-sm">
                {result.missed_critical.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          )}
          {shownResult && <p className="mt-2 text-sm">{shownResult.explanation}</p>}
          <div className="mt-3 flex flex-wrap gap-2">
            <Button
              variant="secondary"
              onClick={() => {
                setResult(null)
                setAnswers({})
                setConfirmed({})
                setStepIndex(0)
              }}
            >
              Retry Scenario
            </Button>
            {nextScenario && (
              <Link to={`/scenarios/${nextScenario.slug}`}>
                <Button>Next Scenario</Button>
              </Link>
            )}
          </div>
        </Card>
      )}

      <Link to={`/${data.domain_key}`} className="text-sm text-[var(--color-accent)] hover:underline">
        Back to {data.domain_key}
      </Link>
    </div>
  )
}
