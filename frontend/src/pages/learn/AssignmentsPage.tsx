import { Link, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { LearnSubnav } from '@/components/learn/LearnSubnav'
import { fetchStudioCatalog } from '@/services/studioService'

export function AssignmentsPage() {
  const [params, setParams] = useSearchParams()
  const family = params.get('family') ?? ''
  const { data, isLoading, isError } = useQuery({
    queryKey: ['studio-catalog', { family }],
    queryFn: () => fetchStudioCatalog(family ? { family } : {}),
  })

  return (
    <div className="module-page learn-page">
      <LearnSubnav />
      <header className="module-heading">
        <div>
          <p className="eyebrow">Learn</p>
          <h1>Assignments</h1>
          <p>Draft, submit evidence, and wait for review. No deadline is added unless one is published.</p>
        </div>
      </header>
      {(data?.families.length ?? 0) > 1 ? (
        <label className="mb-4 block text-sm" htmlFor="assignment-family">
          Family
          <select
            id="assignment-family"
            className="ml-2 rounded-[5px] border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1"
            value={family}
            onChange={(event) => {
              const next = new URLSearchParams(params)
              if (event.target.value) next.set('family', event.target.value)
              else next.delete('family')
              setParams(next)
            }}
          >
            <option value="">Any</option>
            {data!.families.map((item) => (
              <option key={item.id} value={item.id}>{item.label} ({item.count})</option>
            ))}
          </select>
        </label>
      ) : null}
      {isLoading ? (
        <p role="status">Loading assignments.</p>
      ) : isError ? (
        <p role="alert">Could not load assignments. No submission was sent.</p>
      ) : (data?.assignments.length ?? 0) === 0 ? (
        <p className="text-sm text-[var(--color-text-muted)]" role="status">No published assignments match these filters.</p>
      ) : (
        <div className="course-grid">
          {data!.assignments.map((item) => (
            <Link key={item.key} to={`/learn/assignments/${item.key}`} className="course-tile">
              <strong>{item.title}</strong>
              <p>{item.mode === 'local_python' ? 'Local Python · manual review' : item.mode === 'manual_review' ? 'Local work · manual review' : 'SQL evidence'}</p>
              <span>{item.unavailable ? 'Locked' : item.in_progress ? 'Draft in progress' : 'Not started'}</span>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
