import { Badge } from '@/components/common/Badge'
import type { TestResult } from '@/types/coding'

const statusVariant: Record<string, 'success' | 'warning' | 'default'> = {
  accepted: 'success',
  wrong_answer: 'warning',
  compilation_error: 'warning',
  runtime_error: 'warning',
  time_limit_exceeded: 'warning',
  internal_error: 'warning',
}

interface ExecutionResultsProps {
  results: TestResult[]
  passedTests: number
  totalTests: number
  status: string
}

export function ExecutionResults({
  results,
  passedTests,
  totalTests,
  status,
}: ExecutionResultsProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Badge variant={statusVariant[status] ?? 'default'}>{status.replace(/_/g, ' ')}</Badge>
        <span className="text-sm text-[var(--color-text-muted)]">
          {passedTests}/{totalTests} tests passed
        </span>
      </div>
      <div className="space-y-2">
        {results.map((result) => (
          <div
            key={result.test_number}
            className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface-muted)] p-3 text-sm"
          >
            <div className="mb-2 flex items-center justify-between">
              <span className="font-medium">
                {result.name ?? `Test ${result.test_number}`}
                {result.is_hidden && (
                  <span className="ml-2 text-xs text-[var(--color-text-subtle)]">(hidden)</span>
                )}
              </span>
              <Badge variant={statusVariant[result.status] ?? 'default'}>{result.status}</Badge>
            </div>
            {!result.is_hidden && result.input != null && (
              <div className="mb-1">
                <span className="text-xs text-[var(--color-text-subtle)]">Input</span>
                <pre className="mt-1 overflow-x-auto rounded bg-[var(--color-surface)] p-2 text-xs">
                  {result.input}
                </pre>
              </div>
            )}
            {!result.is_hidden && result.expected_output != null && (
              <div className="mb-1">
                <span className="text-xs text-[var(--color-text-subtle)]">Expected</span>
                <pre className="mt-1 overflow-x-auto rounded bg-[var(--color-surface)] p-2 text-xs">
                  {result.expected_output}
                </pre>
              </div>
            )}
            {!result.is_hidden && result.stdout != null && (
              <div className="mb-1">
                <span className="text-xs text-[var(--color-text-subtle)]">Output</span>
                <pre className="mt-1 overflow-x-auto rounded bg-[var(--color-surface)] p-2 text-xs">
                  {result.stdout || '(empty)'}
                </pre>
              </div>
            )}
            {!result.is_hidden && result.stderr && (
              <div>
                <span className="text-xs text-[var(--color-danger)]">Error</span>
                <pre className="mt-1 overflow-x-auto rounded bg-[var(--color-surface)] p-2 text-xs text-[var(--color-danger)]">
                  {result.stderr}
                </pre>
              </div>
            )}
            {result.is_hidden && result.status !== 'accepted' && (
              <p className="text-xs text-[var(--color-text-muted)]">
                Hidden test failed — input and output are not shown.
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
