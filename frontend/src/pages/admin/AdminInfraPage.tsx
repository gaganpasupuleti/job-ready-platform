import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Card, CardHeader } from '@/components/common/Card'
import { fetchAdminInfra } from '@/services/infraService'

export function AdminInfraPage({ domain }: { domain: 'cloud' | 'devops' | 'cybersecurity' }) {
  const { data, isLoading } = useQuery({
    queryKey: ['admin-infra', domain],
    queryFn: () => fetchAdminInfra(domain),
  })
  const byTopic = (data?.mcq_by_topic ?? {}) as Record<string, number>

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold">Admin {domain}</h2>
      <p className="text-sm text-[var(--color-text-muted)]">
        MCQs use the universal question bank. Scenarios have a separate deterministic engine.
      </p>
      <div className="flex flex-wrap gap-3 text-sm">
        <Link to="/admin/questions" className="text-[var(--color-accent)] hover:underline">
          MCQs
        </Link>
        <Link to="/admin/scenarios" className="text-[var(--color-accent)] hover:underline">
          Scenarios
        </Link>
        <Link to="/admin/taxonomy" className="text-[var(--color-accent)] hover:underline">
          Taxonomy
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
          <p className="text-sm">MCQs: {String(data?.mcqs ?? 0)}</p>
          <p className="text-sm">Scenarios: {String(data?.scenarios ?? 0)}</p>
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
