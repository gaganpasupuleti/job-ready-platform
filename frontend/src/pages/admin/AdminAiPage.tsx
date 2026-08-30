import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Card, CardHeader } from '@/components/common/Card'
import { fetchAdminAiCoverage } from '@/services/aiService'

export function AdminAiPage() {
  const { data, isLoading } = useQuery({ queryKey: ['admin-ai'], queryFn: fetchAdminAiCoverage })
  const byTopic = (data?.mcq_by_topic ?? {}) as Record<string, number>

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold">Admin AI</h2>
      <p className="text-sm text-[var(--color-text-muted)]">
        AI MCQs reuse the universal question bank. Prompt challenges have a separate deterministic engine.
      </p>
      <div className="flex flex-wrap gap-3 text-sm">
        <Link to="/admin/questions" className="text-[var(--color-accent)] hover:underline">
          AI MCQs
        </Link>
        <Link to="/admin/ai/prompts" className="text-[var(--color-accent)] hover:underline">
          Prompt Challenges
        </Link>
        <Link to="/admin/ai/taxonomy" className="text-[var(--color-accent)] hover:underline">
          AI taxonomy
        </Link>
        <Link to="/admin/content" className="text-[var(--color-accent)] hover:underline">
          Content Factory
        </Link>
      </div>
      {isLoading ? (
        <p className="text-sm">Loading coverage...</p>
      ) : (
        <Card>
          <CardHeader title="Coverage" />
          <p className="text-sm">AI MCQs: {String(data?.ai_mcqs ?? 0)}</p>
          <p className="text-sm">
            Prompt challenges: {String(data?.prompt_challenges ?? 0)} (active{' '}
            {String(data?.active_prompt_challenges ?? 0)})
          </p>
          <div className="mt-3 space-y-1 text-xs text-[var(--color-text-muted)]">
            {Object.entries(byTopic).map(([slug, count]) => (
              <div key={slug}>
                {slug}: {count}
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}
