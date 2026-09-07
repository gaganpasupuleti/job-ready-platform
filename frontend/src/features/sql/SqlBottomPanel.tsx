import { useEffect, useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import {
  AlertTriangle,
  History,
  MessageSquare,
  Table2,
  Target,
} from 'lucide-react'

import { Badge } from '@/components/common/Badge'
import {
  EmptyState,
  ErrorState,
  SuccessState,
} from '@/components/practice-workspace/PracticeWorkspace'
import { SqlPaneCollapseButton } from '@/features/sql/workbench/SqlPaneChrome'
import { SqlResultTable } from '@/features/sql/SqlResultTable'
import type { SqlRunResponse, SqlSubmissionListItem, SqlSubmitResponse } from '@/types/sql'
import { cn } from '@/utils/cn'
import { Button } from '@/components/common/Button'

type BottomTab = 'results' | 'expected' | 'messages' | 'submissions'

const TABS: Array<{ id: BottomTab; label: string; shortLabel: string; icon: typeof Table2 }> = [
  { id: 'results', label: 'Results', shortLabel: 'Results', icon: Table2 },
  { id: 'expected', label: 'Sample expected', shortLabel: 'Expected', icon: Target },
  { id: 'messages', label: 'Messages', shortLabel: 'Messages', icon: MessageSquare },
  { id: 'submissions', label: 'Submissions', shortLabel: 'History', icon: History },
]

interface SqlBottomPanelProps {
  runResult: SqlRunResponse | null
  submitResult: SqlSubmitResponse | null
  resultMode: 'run' | 'submit' | null
  actionError: string | null
  messages: string[]
  expectedColumns: string[]
  sampleExpectedRows: unknown[][]
  submissions?: SqlSubmissionListItem[]
  preferredTab?: BottomTab | null
  nextHref?: string | null
  onViewSolution?: () => void
  onCollapse?: () => void
  headerActions?: ReactNode
}

export function SqlBottomPanel({
  runResult,
  submitResult,
  resultMode,
  actionError,
  messages,
  expectedColumns,
  sampleExpectedRows,
  submissions,
  preferredTab,
  nextHref,
  onViewSolution,
  onCollapse,
  headerActions,
}: SqlBottomPanelProps) {
  const [tab, setTab] = useState<BottomTab>('results')

  useEffect(() => {
    if (preferredTab) setTab(preferredTab)
  }, [preferredTab])

  return (
    <div className="flex h-full min-h-0 flex-col bg-[var(--color-surface)]">
      <div className="flex items-center justify-between gap-2 border-b border-[var(--color-border)] px-2">
        <div className="flex min-w-0 flex-1 flex-wrap gap-0.5" role="tablist" aria-label="Results">
          {TABS.map((item) => {
            const Icon = item.icon
            const isActive = tab === item.id
            return (
              <button
                key={item.id}
                type="button"
                role="tab"
                aria-selected={isActive}
                onClick={() => setTab(item.id)}
                className={cn(
                  'flex shrink-0 items-center gap-1 rounded-sm px-2 py-2 text-xs font-medium transition-colors sm:text-sm',
                  isActive
                    ? 'border-b-2 border-[var(--color-accent)] text-[var(--color-accent)]'
                    : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]',
                )}
              >
                <Icon className="h-3.5 w-3.5" />
                {item.shortLabel}
              </button>
            )
          })}
        </div>
        <div className="flex items-center gap-1">
          {headerActions}
          {onCollapse && (
            <SqlPaneCollapseButton side="bottom" onClick={onCollapse} label="Results" />
          )}
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-auto p-3">
        {tab === 'results' && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-medium">Results</h3>
              {resultMode === 'run' && <Badge>Run output</Badge>}
              {resultMode === 'submit' && <Badge variant="accent">Submit verdict</Badge>}
            </div>
            {actionError && <ErrorState message={actionError} />}
            {resultMode === 'run' && runResult && (
              <div className="space-y-3">
                {runResult.error ? (
                  <ErrorState message={runResult.error} />
                ) : (
                  <>
                    <p className="text-xs text-[var(--color-text-muted)]">
                      {runResult.row_count} row{runResult.row_count === 1 ? '' : 's'}
                      {runResult.execution_time_ms != null &&
                        ` · ${runResult.execution_time_ms.toFixed(0)} ms`}
                      {runResult.truncated ? ' · truncated' : ''}
                    </p>
                    <SqlResultTable
                      columns={runResult.columns}
                      rows={runResult.rows}
                      truncated={runResult.truncated}
                    />
                  </>
                )}
              </div>
            )}
            {resultMode === 'submit' && submitResult && (
              <div className="space-y-3">
                {submitResult.status === 'accepted' ? (
                  <SuccessState title="✓ Accepted">
                    <p>
                      {submitResult.result_row_count ?? submitResult.rows.length} rows
                      {submitResult.execution_time_ms != null &&
                        ` · ${submitResult.execution_time_ms.toFixed(0)} ms`}
                    </p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {onViewSolution && (
                        <Button size="sm" onClick={onViewSolution}>
                          View Solution
                        </Button>
                      )}
                      {nextHref && (
                        <Link
                          to={nextHref}
                          className="text-sm text-[var(--color-accent)] hover:underline"
                        >
                          Next Problem
                        </Link>
                      )}
                    </div>
                  </SuccessState>
                ) : (
                  <div>
                    <Badge
                      variant={submitResult.status === 'wrong_answer' ? 'warning' : 'default'}
                    >
                      {submitResult.status.replace(/_/g, ' ')}
                    </Badge>
                    <p className="mt-2 text-sm">{submitResult.message}</p>
                    {submitResult.error && <ErrorState message={submitResult.error} />}
                    {submitResult.status === 'wrong_answer' && (
                      <p className="mt-2 text-xs text-[var(--color-text-subtle)]">
                        Expected result rows stay hidden. Use the feedback to adjust your query.
                      </p>
                    )}
                  </div>
                )}
              </div>
            )}
            {!resultMode && !actionError && (
              <EmptyState
                title="No results yet"
                description="Run shows query output. Submit compares against the expected result."
              />
            )}
          </div>
        )}

        {tab === 'expected' && (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Target className="h-4 w-4 text-[var(--color-text-muted)]" />
              <h3 className="text-sm font-medium">Sample expected rows</h3>
            </div>
            <p className="text-xs text-[var(--color-text-muted)]">
              Public sample only — full expected rows stay hidden until you solve the problem.
            </p>
            {sampleExpectedRows.length > 0 ? (
              <SqlResultTable columns={expectedColumns} rows={sampleExpectedRows} />
            ) : (
              <EmptyState
                title="No sample rows"
                description="Expected columns: " 
              />
            )}
            {expectedColumns.length > 0 && sampleExpectedRows.length === 0 && (
              <div className="flex flex-wrap gap-1">
                {expectedColumns.map((col) => (
                  <Badge key={col}>{col}</Badge>
                ))}
              </div>
            )}
          </div>
        )}

        {tab === 'messages' && (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-[var(--color-text-muted)]" />
              <h3 className="text-sm font-medium">Messages</h3>
            </div>
            {messages.length === 0 ? (
              <EmptyState title="No messages yet" description="Run or submit to see status messages." />
            ) : (
              <ul className="space-y-2">
                {messages.map((msg, index) => (
                  <li
                    key={`${index}-${msg.slice(0, 24)}`}
                    className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface-muted)] px-3 py-2 text-sm"
                  >
                    {msg}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}

        {tab === 'submissions' && (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <History className="h-4 w-4 text-[var(--color-text-muted)]" />
              <h3 className="text-sm font-medium">Submissions</h3>
            </div>
            {submissions?.length ? (
              submissions.map((sub) => (
                <Link
                  key={sub.id}
                  to={`/sql/submissions/${sub.id}`}
                  className="flex items-center justify-between rounded-md border border-[var(--color-border)] px-3 py-2 text-sm hover:bg-[var(--color-surface-muted)]"
                >
                  <div>
                    <p className="font-medium capitalize">{sub.status.replace(/_/g, ' ')}</p>
                    <p className="text-xs text-[var(--color-text-muted)]">
                      {new Date(sub.submitted_at).toLocaleString()}
                    </p>
                  </div>
                </Link>
              ))
            ) : (
              <EmptyState
                title="No submissions yet"
                description="Run and submit a query to build history."
              />
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export type { BottomTab as SqlBottomTab }
