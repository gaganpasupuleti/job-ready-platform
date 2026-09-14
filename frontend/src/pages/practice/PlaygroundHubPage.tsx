import { Lock } from 'lucide-react'
import { Link } from 'react-router-dom'

export function PlaygroundHubPage() {
  return (
    <div className="module-page">
      <header className="module-heading">
        <div>
          <p className="eyebrow">Playground</p>
          <h1>Playground</h1>
          <p>SQL Studio is available. Python execution is not.</p>
        </div>
      </header>
      <div className="course-grid">
        <Link to="/practice/sql" className="course-tile">
          <strong>SQL Studio</strong>
          <p>Choose a dataset, inspect the schema, run a query, and submit only when the problem asks for it.</p>
          <span>Available</span>
        </Link>
        <Link to="/practice/python" className="course-tile" aria-disabled="true">
          <strong className="inline-flex items-center gap-2">
            <Lock size={16} aria-hidden />
            Python
          </strong>
          <p>Coming soon.</p>
        </Link>
      </div>
    </div>
  )
}
