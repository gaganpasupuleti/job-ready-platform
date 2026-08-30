import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Card, CardHeader } from '@/components/common/Card'
import { fetchPromptSubmission } from '@/services/aiService'

export function PromptSubmissionDetailPage() {
  const { id = '' } = useParams()
  const { data, isLoading, error } = useQuery({
    queryKey: ['prompt-submission', id],
    queryFn: () => fetchPromptSubmission(id),
    enabled: Boolean(id),
  })

  if (isLoading) return <p className="text-sm text-[var(--color-text-muted)]">Loading...</p>
  if (error || !data) {
    return <p className="text-sm text-[var(--color-text-muted)]">Submission not found or not yours.</p>
  }

  return (
    <div className="space-y-4">
      <Link to="/ai/prompt-engineering/submissions" className="text-sm text-[var(--color-accent)] hover:underline">
        Back to submissions
      </Link>
      <h2 className="text-lg font-semibold">{data.challenge_title}</h2>
      <div className="flex gap-2">
        <Badge>{data.difficulty}</Badge>
        <Badge>{data.overall_score}</Badge>
      </div>
      <Card>
        <CardHeader title="Prompt" />
        <pre className="whitespace-pre-wrap text-sm">{data.prompt_text}</pre>
      </Card>
      <Card>
        <CardHeader title="Score" />
        <p className="text-sm">
          {data.passed_cases}/{data.total_cases} cases · {new Date(data.created_at).toLocaleString()}
        </p>
        <div className="mt-2 grid gap-2 sm:grid-cols-3">
          {Object.entries(data.rubric_breakdown).map(([key, value]) => (
            <div key={key} className="rounded border border-[var(--color-border)] px-2 py-1 text-xs">
              {key}: {value}
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
