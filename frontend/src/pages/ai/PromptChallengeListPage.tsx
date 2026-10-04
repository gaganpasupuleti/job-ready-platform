import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { humanLabel } from '@/lib/studentLabels'
import { fetchPromptChallenges } from '@/services/aiService'

export function PromptChallengeListPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['prompt-challenges'],
    queryFn: () => fetchPromptChallenges(),
  })

  return (
    <div className="space-y-6">
      <div className="reading-shell">
        <h1 className="text-lg font-semibold text-[var(--color-text)]">Prompt challenges</h1>
        <p className="text-sm text-[var(--color-text-muted)]">
          Write a prompt and check it against saved cases. There is no hosted model.
        </p>
        <Link to="/ai/prompt-engineering/submissions" className="text-sm text-[var(--color-accent)] hover:underline">
          View submissions
        </Link>
      </div>
      {isLoading ? (
        <p className="text-sm text-[var(--color-text-muted)]" role="status">Loading challenges.</p>
      ) : isError ? (
        <p className="text-sm text-[var(--color-danger)]" role="alert">Could not load prompt challenges.</p>
      ) : (data?.length ?? 0) === 0 ? (
        <p className="text-sm text-[var(--color-text-muted)]" role="status">No prompt challenges are published.</p>
      ) : (
        <div className="reading-shell space-y-3">
          {data?.map((item) => (
            <Link
              key={item.id}
              to={`/ai/prompt-engineering/challenges/${item.slug}`}
              className="block rounded-md border border-[var(--color-border)] px-3 py-3 hover:border-[var(--color-accent)]"
            >
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-medium text-[var(--color-text)]">{item.title}</span>
                <Badge>{humanLabel(item.difficulty)}</Badge>
                <Badge>{humanLabel(item.task_type)}</Badge>
                {item.status ? <Badge>{humanLabel(item.status)}</Badge> : null}
              </div>
              <p className="mt-1 text-sm text-[var(--color-text-muted)]">{item.description}</p>
              <p className="mt-1 text-xs text-[var(--color-text-subtle)]">
                {item.status ? `Best score ${item.best_score}` : 'No attempt yet'}
              </p>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
