import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Card } from '@/components/common/Card'
import { SqlEditor } from '@/features/sql/SqlEditor'
import { fetchSqlSubmission } from '@/services/sqlService'

export function SqlSubmissionDetailPage() {
  const { submissionId = '' } = useParams()

  const { data, isLoading } = useQuery({
    queryKey: ['sql-submission', submissionId],
    queryFn: () => fetchSqlSubmission(submissionId),
    enabled: Boolean(submissionId),
  })

  if (isLoading || !data) {
    return <p className="text-sm text-[var(--color-text-muted)]">Loading submission...</p>
  }

  return (
    <div className="space-y-6">
      <div>
        <Link
          to="/sql/submissions"
          className="text-xs text-[var(--color-accent)] hover:underline"
        >
          ← Back to submissions
        </Link>
        <h2 className="text-lg font-semibold text-[var(--color-text)]">{data.problem_title}</h2>
        <div className="mt-2 flex flex-wrap gap-2">
          <Badge
            variant={
              data.status === 'accepted'
                ? 'success'
                : data.status === 'wrong_answer'
                  ? 'warning'
                  : 'default'
            }
          >
            {data.status.replace(/_/g, ' ')}
          </Badge>
          {data.difficulty && <Badge>{data.difficulty}</Badge>}
        </div>
        <p className="mt-1 text-xs text-[var(--color-text-muted)]">
          Submitted {new Date(data.submitted_at).toLocaleString()}
          {data.result_row_count != null && ` · ${data.result_row_count} rows`}
          {data.execution_time_ms != null && ` · ${data.execution_time_ms.toFixed(0)} ms`}
        </p>
        <Link
          to={`/practice/sql/${data.problem_slug}`}
          className="mt-2 inline-block text-xs text-[var(--color-accent)] hover:underline"
        >
          Open problem →
        </Link>
      </div>

      <Card padding="md">
        <h3 className="mb-3 text-sm font-medium">Query</h3>
        <div className="h-64 overflow-hidden rounded-md border border-[var(--color-border)]">
          <SqlEditor value={data.query_text} onChange={() => {}} readOnly height="100%" />
        </div>
      </Card>

      {(data.error_message || data.feedback) && (
        <Card padding="md">
          <h3 className="mb-3 text-sm font-medium">Feedback</h3>
          {data.error_message && (
            <p className="text-sm text-red-600 dark:text-red-400">{data.error_message}</p>
          )}
          {data.feedback && (
            <p className="text-sm text-[var(--color-text-muted)]">
              {typeof data.feedback.message === 'string'
                ? data.feedback.message
                : JSON.stringify(data.feedback)}
            </p>
          )}
        </Card>
      )}
    </div>
  )
}
