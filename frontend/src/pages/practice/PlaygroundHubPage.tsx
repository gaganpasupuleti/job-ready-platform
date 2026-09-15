import { Lock } from 'lucide-react'
import { Link } from 'react-router-dom'

export function PlaygroundHubPage() {
  return (
    <div className="module-page">
      <header className="module-heading">
        <div>
          <p className="eyebrow">Playground</p>
          <h1>Playground</h1>
          <p>SQL IDE is available. Python execution is not part of this release.</p>
        </div>
      </header>
      <div className="course-grid">
        <Link to="/practice/playground/sql" className="course-tile" data-testid="sql-playground-tile">
          <strong>SQL</strong>
          <p>Open the standalone SQL IDE with sample datasets. No assessed problem required.</p>
          <span>Available</span>
        </Link>
        <Link to="/practice/python" className="course-tile" data-testid="python-coming-soon-tile">
          <strong className="inline-flex items-center gap-2">
            <Lock size={16} aria-hidden />
            Python — Coming soon
          </strong>
          <p>Locked for this release. Saved drafts stay in this browser.</p>
        </Link>
      </div>
      <p className="mt-4 text-sm text-[var(--color-text-muted)]">
        Need graded SQL work? Use{' '}
        <Link to="/practice/sql" className="text-[var(--color-accent)] hover:underline">
          SQL Practice
        </Link>
        .
      </p>
    </div>
  )
}
