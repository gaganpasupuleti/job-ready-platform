import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Card, CardHeader } from '@/components/common/Card'
import { fetchPromptSubmissions } from '@/services/aiService'

export function PromptSubmissionsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['prompt-submissions'],
    queryFn: fetchPromptSubmissions,
  })

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-[var(--color-text)]">Prompt submissions</h2>
      <Card>
        <CardHeader title={`Submissions (${data?.length ?? 0})`} />
        {isLoading ? (
          <p className="text-sm text-[var(--color-text-muted)]">Loading...</p>
        ) : (
          <div className="space-y-2">
            {data?.map((item) => (
              <Link
                key={item.id}
                to={`/ai/prompt-engineering/submissions/${item.id}`}
                className="flex flex-wrap items-center justify-between gap-2 rounded border border-[var(--color-border)] px-3 py-2 text-sm"
              >
                <span>{item.challenge_title}</span>
                <span className="flex items-center gap-2 text-[var(--color-text-muted)]">
                  <Badge>{item.difficulty}</Badge>
                  {item.overall_score} · {item.passed_cases}/{item.total_cases}
                </span>
              </Link>
            ))}
            {!data?.length && <p className="text-sm text-[var(--color-text-muted)]">No submissions yet.</p>}
          </div>
        )}
      </Card>
    </div>
  )
}
