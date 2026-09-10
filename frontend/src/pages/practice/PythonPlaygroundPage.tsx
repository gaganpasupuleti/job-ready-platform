import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { CodeEditor } from '@/features/dsa/CodeEditor'
import { useAuth } from '@/hooks/useAuth'
import { fetchExecutionStatus, runPlayground } from '@/services/codingService'
import type { PlaygroundRunResponse } from '@/types/coding'

const PYTHON_LANG_ID = 71
const STARTER = `print("Hello, JobReady")\n`

function playgroundDraftKey(userId: string) {
  return `coding-playground:${userId}:python:${PYTHON_LANG_ID}`
}

export function PythonPlaygroundPage() {
  const { user } = useAuth()
  const [sourceCode, setSourceCode] = useState(STARTER)
  const [stdin, setStdin] = useState('')
  const [draftStatus, setDraftStatus] = useState<'saved' | 'editing'>('saved')
  const [history, setHistory] = useState<PlaygroundRunResponse[]>([])
  const [initialized, setInitialized] = useState(false)

  const { data: executionStatus } = useQuery({
    queryKey: ['coding-execution-status'],
    queryFn: fetchExecutionStatus,
    refetchInterval: 30_000,
  })

  const available = executionStatus?.available !== false

  useEffect(() => {
    if (!user?.id) return
    const stored = localStorage.getItem(playgroundDraftKey(user.id))
    setSourceCode(stored ?? STARTER)
    setInitialized(true)
  }, [user?.id])

  useEffect(() => {
    if (!user?.id || !initialized) return
    localStorage.setItem(playgroundDraftKey(user.id), sourceCode)
    setDraftStatus('saved')
  }, [user?.id, sourceCode, initialized])

  const runMutation = useMutation({
    mutationFn: () => runPlayground(sourceCode, PYTHON_LANG_ID, stdin),
    onSuccess: (data) => {
      setHistory((prev) => [data, ...prev].slice(0, 8))
    },
  })

  const latest = history[0] ?? runMutation.data ?? null
  const statusLabel = useMemo(() => {
    if (runMutation.isPending) return 'running'
    if (!available) return 'unavailable'
    return latest?.status ?? 'idle'
  }, [available, latest?.status, runMutation.isPending])

  return (
    <div className="flex h-[calc(100vh-2.75rem)] min-h-[520px] flex-col gap-3 px-3 py-2 sm:px-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs text-[var(--color-text-muted)]">
            <Link to="/practice/coding" className="text-[var(--color-accent)] hover:underline">
              Coding
            </Link>
            {' / '}
            Playground
          </p>
          <h1
            className="text-[22px] font-semibold leading-tight text-[var(--color-text)]"
            data-testid="python-playground-heading"
          >
            Python Playground
          </h1>
          <p className="mt-1 max-w-2xl text-[13px] text-[var(--color-text-muted)]">
            Freeform Python execution with stdin. This is not an assessed problem — use DSA/Coding
            problems for graded Run/Submit.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant={available ? 'success' : 'warning'}>
            {available ? 'Executor ready' : 'Executor unavailable'}
          </Badge>
          <Badge>{draftStatus === 'saved' ? 'Draft saved' : 'Editing'}</Badge>
          <Badge>{statusLabel}</Badge>
        </div>
      </div>

      {!available && (
        <div
          className="rounded-md border border-amber-300/60 bg-amber-50 px-3 py-2 text-[13px] text-amber-900 dark:border-amber-700/50 dark:bg-amber-950/40 dark:text-amber-100"
          role="status"
        >
          {executionStatus?.message ||
            'Judge0 is disabled or unreachable. Code will not be executed and no fake output is shown.'}
        </div>
      )}

      <div className="grid min-h-0 flex-1 gap-3 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
        <section className="flex min-h-0 flex-col overflow-hidden rounded-md border border-[var(--color-border)] bg-[var(--color-surface)]">
          <div className="flex h-10 items-center justify-between border-b border-[var(--color-border)] px-3">
            <span className="text-[13px] font-medium text-[var(--color-text)]">Editor · Python</span>
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant="ghost"
                onClick={() => {
                  if (user?.id) localStorage.removeItem(playgroundDraftKey(user.id))
                  setSourceCode(STARTER)
                  setDraftStatus('saved')
                }}
              >
                Reset
              </Button>
              <Button
                size="sm"
                variant="primary"
                disabled={!available || runMutation.isPending || !sourceCode.trim()}
                onClick={() => runMutation.mutate()}
              >
                {runMutation.isPending ? 'Running…' : 'Run'}
              </Button>
            </div>
          </div>
          <div className="min-h-0 flex-1">
            <CodeEditor
              value={sourceCode}
              onChange={(v) => {
                setDraftStatus('editing')
                setSourceCode(v)
              }}
              language="python"
              height="100%"
            />
          </div>
        </section>

        <section className="flex min-h-0 flex-col gap-3">
          <div className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] p-3">
            <label className="text-[12px] font-medium text-[var(--color-text-muted)]" htmlFor="stdin">
              Standard input
            </label>
            <textarea
              id="stdin"
              value={stdin}
              onChange={(e) => setStdin(e.target.value)}
              rows={4}
              className="mt-1 w-full rounded-md border border-[var(--color-border)] bg-[var(--color-surface-muted)] p-2 font-mono text-[12px] text-[var(--color-text)]"
              placeholder="Optional stdin for your program"
            />
          </div>

          <div className="min-h-0 flex-1 overflow-auto rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] p-3">
            <h2 className="text-[14px] font-semibold text-[var(--color-text)]">Output</h2>
            {!latest && !runMutation.isPending && (
              <p className="mt-2 text-[13px] text-[var(--color-text-muted)]">
                Run your code to see stdout, stderr, and compile diagnostics.
              </p>
            )}
            {latest && (
              <div className="mt-2 space-y-3 text-[13px]">
                <div className="flex flex-wrap gap-2">
                  <Badge variant={latest.available === false ? 'warning' : 'default'}>
                    {latest.status.replace(/_/g, ' ')}
                  </Badge>
                  {latest.execution_time_ms != null && (
                    <span className="text-[12px] text-[var(--color-text-muted)]">
                      {latest.execution_time_ms.toFixed(1)} ms
                    </span>
                  )}
                </div>
                {latest.message && (
                  <p className="text-[13px] text-amber-800 dark:text-amber-200">{latest.message}</p>
                )}
                <div>
                  <p className="text-[12px] text-[var(--color-text-muted)]">stdout</p>
                  <pre className="mt-1 overflow-x-auto rounded bg-[var(--color-surface-muted)] p-2 text-[12px]">
                    {latest.stdout || '(empty)'}
                  </pre>
                </div>
                {(latest.stderr || latest.compile_output) && (
                  <div>
                    <p className="text-[12px] text-[var(--color-danger)]">stderr / compile</p>
                    <pre className="mt-1 overflow-x-auto rounded bg-[var(--color-surface-muted)] p-2 text-[12px] text-[var(--color-danger)]">
                      {latest.compile_output || latest.stderr}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </div>

          {history.length > 1 && (
            <div className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] p-3">
              <h2 className="text-[14px] font-semibold text-[var(--color-text)]">Recent runs</h2>
              <ul className="mt-2 space-y-1 text-[12px] text-[var(--color-text-muted)]">
                {history.slice(0, 5).map((item, idx) => (
                  <li key={`${item.status}-${idx}`}>
                    #{history.length - idx}: {item.status.replace(/_/g, ' ')}
                    {!item.available ? ' · unavailable' : ''}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
