import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Card, CardHeader } from '@/components/common/Card'
import { fetchSqlSubmissions } from '@/services/sqlService'
import type { SqlSubmissionStatus } from '@/types/sql'

export function SqlSubmissionsPage() {
  const [status, setStatus] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['sql-submissions', status],
    queryFn: () =>
      fetchSqlSubmissions({
        status: (status as SqlSubmissionStatus) || undefined,
        limit: 50,
      }),
  })

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-[var(--color-text)]">SQL Submissions</h2>
        <p className="text-sm text-[var(--color-text-muted)]">
          Review your SQL query submissions across all problems.
        </p>
      </div>

      <Card padding="md">
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm"
        >
          <option value="">All statuses</option>
          <option value="accepted">Accepted</option>
          <option value="wrong_answer">Wrong Answer</option>
          <option value="sql_error">SQL Error</option>
          <option value="timeout">Timeout</option>
          <option value="execution_disabled">Execution Disabled</option>
          <option value="internal_error">Internal Error</option>
        </select>
      </Card>

      <Card>
        <CardHeader title={`Submissions (${data?.total ?? 0})`} />
        {isLoading ? (
          <p className="text-sm text-[var(--color-text-muted)]">Loading...</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs text-[var(--color-text-subtle)]">
                <tr>
                  <th className="pb-2">Status</th>
                  <th className="pb-2">Problem</th>
                  <th className="pb-2">Difficulty</th>
                  <th className="pb-2">Topic</th>
                  <th className="pb-2">Rows</th>
                  <th className="pb-2">Runtime</th>
                  <th className="pb-2">Submitted</th>
                </tr>
              </thead>
              <tbody>
                {data?.items.map((sub) => (
                  <tr key={sub.id} className="border-t border-[var(--color-border)]">
                    <td className="py-3 pr-3 capitalize">
                      <Link
                        to={`/sql/submissions/${sub.id}`}
                        className="text-[var(--color-accent)]"
                      >
                        {sub.status.replace(/_/g, ' ')}
                      </Link>
                    </td>
                    <td className="py-3 pr-3">
                      <Link
                        to={`/practice/sql/${sub.problem_slug}`}
                        className="hover:underline"
                      >
                        {sub.problem_title}
                      </Link>
                    </td>
                    <td className="py-3 pr-3 capitalize">{sub.difficulty ?? '—'}</td>
                    <td className="py-3 pr-3 text-xs text-[var(--color-text-muted)]">
                      {sub.topic_name ?? '—'}
                    </td>
                    <td className="py-3 pr-3">{sub.result_row_count ?? '—'}</td>
                    <td className="py-3 pr-3">
                      {sub.execution_time_ms != null
                        ? `${sub.execution_time_ms.toFixed(0)} ms`
                        : '—'}
                    </td>
                    <td className="py-3 text-xs text-[var(--color-text-muted)]">
                      {new Date(sub.submitted_at).toLocaleString()}
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
