import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Card } from '@/components/common/Card'
import { CodeEditor } from '@/features/dsa/CodeEditor'
import { ExecutionResults } from '@/features/dsa/ExecutionResults'
import { getMonacoLanguage } from '@/constants/languages'
import { fetchSubmission } from '@/services/codingService'

export function SubmissionDetailPage() {
  const { submissionId = '' } = useParams()

  const { data, isLoading } = useQuery({
    queryKey: ['submission', submissionId],
    queryFn: () => fetchSubmission(submissionId),
    enabled: Boolean(submissionId),
  })

  if (isLoading || !data) {
    return <p className="text-sm text-[var(--color-text-muted)]">Loading submission...</p>
  }

  return (
    <div className="space-y-6">
      <div>
        <Link to="/submissions" className="text-xs text-[var(--color-accent)] hover:underline">
          ← Back to submissions
        </Link>
        <h2 className="text-lg font-semibold text-[var(--color-text)]">{data.problem_title}</h2>
        <div className="mt-2 flex flex-wrap gap-2">
          <Badge>{data.status.replace(/_/g, ' ')}</Badge>
          <Badge>{data.language_name}</Badge>
          {data.problem_difficulty && <Badge>{data.problem_difficulty}</Badge>}
        </div>
        <p className="mt-1 text-xs text-[var(--color-text-muted)]">
          Submitted {new Date(data.created_at).toLocaleString()} · {data.passed_tests}/
          {data.total_tests} tests passed
          {data.execution_time_ms != null && ` · ${data.execution_time_ms.toFixed(0)} ms`}
        </p>
        {data.hidden_summary && (
          <p className="mt-2 text-sm text-[var(--color-text-muted)]">{data.hidden_summary}</p>
        )}
      </div>

      <Card padding="md">
        <h3 className="mb-3 text-sm font-medium">Source code</h3>
        <div className="h-64 overflow-hidden rounded-md border border-[var(--color-border)]">
          <CodeEditor
            value={data.source_code}
            language={getMonacoLanguage(data.language_id)}
            onChange={() => {}}
            readOnly
            height="100%"
          />
        </div>
      </Card>

      <Card padding="md">
        <h3 className="mb-3 text-sm font-medium">Test results</h3>
        <ExecutionResults
          results={data.results}
          passedTests={data.passed_tests}
          totalTests={data.total_tests}
          status={data.status}
        />
      </Card>
    </div>
  )
}
