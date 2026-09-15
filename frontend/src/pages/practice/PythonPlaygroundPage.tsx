import { useState } from 'react'
import { Lock } from 'lucide-react'
import { Link } from 'react-router-dom'

import { Button } from '@/components/common/Button'
import { useLockExecutionShortcuts } from '@/components/practice-workspace/practiceWorkspaceUtils'
import { useAuth } from '@/hooks/useAuth'

const PYTHON_LANG_ID = 71

function playgroundDraftKey(userId: string) {
  return `coding-playground:${userId}:python:${PYTHON_LANG_ID}`
}

export function PythonPlaygroundPage() {
  const { user } = useAuth()
  const [draft, setDraft] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  useLockExecutionShortcuts(true)

  function showDraft() {
    if (!user?.id) return
    setDraft(localStorage.getItem(playgroundDraftKey(user.id)))
  }

  async function copyDraft() {
    if (!draft) return
    await navigator.clipboard.writeText(draft)
    setCopied(true)
  }

  return (
    <div className="module-page">
      <header className="module-heading">
        <div>
          <p className="text-xs text-[var(--color-text-muted)]">
            <Link to="/practice/playground" className="text-[var(--color-accent)] hover:underline">
              Playground
            </Link>
            {' / '}
            <Link to="/practice/playground/sql" className="text-[var(--color-accent)] hover:underline">
              SQL IDE
            </Link>
          </p>
          <h1
            className="inline-flex items-center gap-2 text-base font-semibold leading-tight text-[var(--color-text)] sm:text-lg"
            data-testid="python-playground-heading"
          >
            <Lock size={18} aria-hidden />
            Python — Coming soon
          </h1>
          <p role="status" className="mt-0.5 max-w-2xl text-sm text-[var(--color-text-muted)]">
            Python execution is locked. This page does not run or grade code.
          </p>
        </div>
      </header>
      <div className="rounded-[5px] border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
        <p className="text-sm text-[var(--color-text-muted)]">
          Saved drafts stay on this browser. Viewing a draft does not mount the editor, stdin, output,
          or Run controls. Use the SQL IDE when the task is SQL.
        </p>
        <Button className="mt-3" variant="secondary" onClick={showDraft}>
          View saved draft
        </Button>
        {draft !== null && (
          <div className="mt-3">
            {draft ? (
              <>
                <pre className="overflow-x-auto rounded bg-[var(--color-surface-muted)] p-3 text-xs">{draft}</pre>
                <Button className="mt-2" variant="ghost" onClick={() => void copyDraft()}>
                  {copied ? 'Copied' : 'Copy draft'}
                </Button>
              </>
            ) : (
              <p className="mt-2 text-sm text-[var(--color-text-muted)]">No saved draft.</p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
