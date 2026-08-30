import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
import { fetchScenario, submitScenario, type ScenarioSubmitResponse } from '@/services/infraService'

export function ScenarioWorkspacePage() {
  const { slug = '' } = useParams()
  const queryClient = useQueryClient()
  const { data, isLoading } = useQuery({
    queryKey: ['scenario', slug],
    queryFn: () => fetchScenario(slug),
    enabled: Boolean(slug),
  })
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [result, setResult] = useState<ScenarioSubmitResponse | null>(null)

  const mutation = useMutation({
    mutationFn: () =>
      submitScenario(
        slug,
        Object.entries(answers).map(([step_id, option_id]) => ({ step_id, option_id })),
      ),
    onSuccess: (body) => {
      setResult(body)
      queryClient.invalidateQueries({ queryKey: ['scenario', slug] })
    },
  })

  if (isLoading || !data) {
    return <p className="text-sm text-[var(--color-text-muted)]">Loading scenario...</p>
  }

  const ready = data.steps.every((step) => answers[step.id])

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-[var(--color-text)]">{data.title}</h2>
        <div className="mt-1 flex flex-wrap gap-2">
          <Badge>{data.difficulty}</Badge>
          <Badge>{data.scenario_type}</Badge>
          <Badge>{data.domain_key}</Badge>
          {data.unofficial_cert_tag && <Badge>{data.unofficial_cert_tag}</Badge>}
        </div>
        <p className="mt-2 text-xs text-[var(--color-text-subtle)]">{data.unofficial_disclaimer}</p>
      </div>

      <Card>
        <CardHeader title="Scenario" />
        <p className="text-sm">{data.description}</p>
      </Card>
      <Card>
        <CardHeader title="Context" />
        <p className="whitespace-pre-wrap text-sm">{data.context_text}</p>
        {Object.keys(data.evidence_json || {}).length > 0 && (
          <pre className="mt-2 overflow-x-auto rounded bg-[var(--color-surface-muted)] p-2 text-xs">
            {JSON.stringify(data.evidence_json, null, 2)}
          </pre>
        )}
      </Card>

      {data.steps.map((step, index) => (
        <Card key={step.id}>
          <CardHeader title={`Step ${index + 1}${step.is_critical ? ' · critical' : ''}`} />
          {step.context_snippet && (
            <p className="mb-2 text-xs text-[var(--color-text-muted)]">{step.context_snippet}</p>
          )}
          <p className="mb-3 text-sm">{step.prompt}</p>
          <div className="space-y-2">
            {step.options.map((option) => (
              <label key={option.id} className="flex cursor-pointer items-start gap-2 text-sm">
                <input
                  type="radio"
                  name={step.id}
                  checked={answers[step.id] === option.id}
                  onChange={() => setAnswers((prev) => ({ ...prev, [step.id]: option.id }))}
                />
                <span>{option.label}</span>
              </label>
            ))}
          </div>
        </Card>
      ))}

      <Button disabled={!ready || mutation.isPending} onClick={() => mutation.mutate()}>
        Submit decisions
      </Button>
      {mutation.isError && <p className="text-sm text-[var(--color-danger)]">Could not submit. Try again.</p>}

      {result && (
        <Card>
          <CardHeader title="Score" />
          <p className="text-sm">
            {result.overall_score} · {result.correct_decisions}/{result.total_steps} correct
            {result.mastered ? ' · mastered' : ''}
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
          <ul className="mt-3 space-y-2 text-sm">
            {result.step_results.map((row) => (
              <li key={row.step_id}>
                {row.is_correct ? 'Correct' : 'Incorrect'}: {row.explanation}
              </li>
            ))}
          </ul>
        </Card>
      )}

      <Link to={`/${data.domain_key}`} className="text-sm text-[var(--color-accent)] hover:underline">
        Back to {data.domain_key}
      </Link>
    </div>
  )
}
