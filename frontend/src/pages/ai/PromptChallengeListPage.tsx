import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Card, CardHeader } from '@/components/common/Card'
import { fetchPromptChallenges } from '@/services/aiService'

export function PromptChallengeListPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['prompt-challenges'],
    queryFn: () => fetchPromptChallenges(),
  })

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-[var(--color-text)]">Prompt Challenges</h2>
        <p className="text-sm text-[var(--color-text-muted)]">
          Write reusable prompts with template variables. Scoring is deterministic — no hosted model.
        </p>
        <Link to="/ai/prompt-engineering/submissions" className="text-sm text-[var(--color-accent)] hover:underline">
          View submissions
        </Link>
      </div>
      <Card>
        <CardHeader title={`Challenges (${data?.length ?? 0})`} />
        {isLoading ? (
          <p className="text-sm text-[var(--color-text-muted)]">Loading...</p>
        ) : (
          <div className="space-y-3">
            {data?.map((item) => (
              <Link
                key={item.id}
                to={`/ai/prompt-engineering/challenges/${item.slug}`}
                className="block rounded-md border border-[var(--color-border)] px-3 py-3 hover:border-[var(--color-accent)]"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-medium text-[var(--color-text)]">{item.title}</span>
                  <Badge>{item.difficulty}</Badge>
                  <Badge>{item.task_type}</Badge>
                  {item.status && <Badge>{item.status}</Badge>}
                </div>
                <p className="mt-1 text-sm text-[var(--color-text-muted)]">{item.description}</p>
                <p className="mt-1 text-xs text-[var(--color-text-subtle)]">Best score {item.best_score}</p>
              </Link>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}
