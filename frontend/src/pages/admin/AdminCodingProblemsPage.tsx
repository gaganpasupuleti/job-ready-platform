import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
import { fetchAdminCodingProblems } from '@/services/codingService'

export function AdminCodingProblemsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['admin-coding-problems'],
    queryFn: fetchAdminCodingProblems,
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-[var(--color-text)]">Coding Problems</h2>
          <p className="text-sm text-[var(--color-text-muted)]">
            Manage DSA problems, public samples, and hidden test cases
          </p>
        </div>
        <Link to="/admin/coding/new">
          <Button variant="primary">New Problem</Button>
        </Link>
      </div>

      <Card>
        <CardHeader title={`Problems (${data?.total ?? 0})`} />
        {isLoading ? (
          <p className="text-sm text-[var(--color-text-muted)]">Loading...</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs text-[var(--color-text-subtle)]">
                <tr>
                  <th className="pb-2">Title</th>
                  <th className="pb-2">Slug</th>
                  <th className="pb-2">Difficulty</th>
                </tr>
              </thead>
              <tbody>
                {data?.items.map((problem) => (
                  <tr key={problem.id} className="border-t border-[var(--color-border)]">
                    <td className="py-3 pr-4">
                      <Link
                        to={`/admin/coding/${problem.id}`}
                        className="text-[var(--color-accent)] hover:underline"
                      >
                        {problem.title}
                      </Link>
                    </td>
                    <td className="py-3 pr-4 text-xs text-[var(--color-text-muted)]">
                      {problem.slug}
                    </td>
                    <td className="py-3">
                      <Badge>{problem.difficulty}</Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}
