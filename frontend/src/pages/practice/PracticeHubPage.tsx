import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { PracticeTrackNav } from '@/components/practice/PracticeTrackNav'
import { Input } from '@/components/common/Field'
import {
  fetchPracticeHub,
  searchPractice,
  type PracticePathCard,
} from '@/services/learnService'

function pathHref(path: PracticePathCard) {
  if (path.external_route) return path.external_route
  return `/practice/paths/${path.slug}`
}

function PathRow({ path }: { path: PracticePathCard }) {
  const comingSoon = path.availability === 'coming_soon'
  return (
    <Link
      to={comingSoon ? '#' : pathHref(path)}
      className={`v4-queue-row ${comingSoon ? 'is-disabled' : ''}`}
      onClick={(e) => comingSoon && e.preventDefault()}
      aria-disabled={comingSoon}
    >
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-1.5">
          <strong>{path.title}</strong>
          <Badge>{path.difficulty}</Badge>
          {comingSoon ? (
            <Badge variant="warning">Coming Soon</Badge>
          ) : (
            <Badge variant="success">Available</Badge>
          )}
        </div>
        <p className="mt-0.5 text-xs text-[var(--color-text-muted)]">{path.short_description}</p>
        <p className="mt-1 text-[11px] text-[var(--color-text-subtle)]">
          {path.language ? `${path.language} · ` : ''}
          {path.item_count} items
          {path.progress_percent > 0 ? ` · ${path.progress_percent}% complete` : ' · Not started'}
        </p>
      </div>
      <span className="queue-meta">
        {path.progress_percent > 0 && !comingSoon ? 'Continue' : comingSoon ? 'Soon' : 'Start'}
      </span>
    </Link>
  )
}

export function PracticeHubPage() {
  const [query, setQuery] = useState('')
  const [activeSection, setActiveSection] = useState<string>('')

  const { data, isLoading, isError } = useQuery({
    queryKey: ['practice-hub'],
    queryFn: fetchPracticeHub,
  })

  const { data: searchData, isFetching: searching } = useQuery({
    queryKey: ['practice-search', query],
    queryFn: () => searchPractice(query),
    enabled: query.trim().length >= 2,
  })

  const sections = useMemo(() => {
    if (!data?.sections) return []
    if (!activeSection) return data.sections
    return data.sections.filter((s) => s.key === activeSection)
  }, [data, activeSection])

  return (
    <div className="module-page practice-hub">
      <PracticeTrackNav />
      <header className="module-heading">
        <div>
          <p className="eyebrow">Practice</p>
          <h1>Practice Hub</h1>
          <p>Guided paths for languages, DSA, SQL, projects, and interview preparation.</p>
        </div>
        <Link to="/learn">
          <Button variant="primary" size="sm">
            Browse courses
          </Button>
        </Link>
      </header>

      <div className="problem-toolbar">
        <Input
          aria-label="Search practice content"
          placeholder="Search paths, courses, projects..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>

      {query.trim().length >= 2 && (
        <section className="module-panel" aria-live="polite">
          <h2>Search results</h2>
          {searching ? (
            <p className="text-sm text-[var(--color-text-muted)]">Searching…</p>
          ) : (
            <ul className="result-list">
              {(searchData?.items ?? []).map((item) => (
                <li key={`${item.kind}-${item.href}`}>
                  <Link to={item.href}>{item.title}</Link>
                  <span>{item.kind}</span>
                </li>
              ))}
              {!searchData?.items.length && (
                <li className="empty-row">No matches.</li>
              )}
            </ul>
          )}
        </section>
      )}

      {(data?.continue_learning?.length ?? 0) > 0 && (
        <section className="module-panel">
          <h2>Continue learning</h2>
          <div className="queue-list">
            {data!.continue_learning.map((item) => (
              <Link key={item.href} to={item.href} className="v4-queue-row">
                <div>
                  <strong>{item.title}</strong>
                  {item.subtitle ? (
                    <p className="mt-0.5 text-xs text-[var(--color-text-muted)]">{item.subtitle}</p>
                  ) : null}
                </div>
                <span className="queue-meta">{item.progress_percent}%</span>
              </Link>
            ))}
          </div>
        </section>
      )}

      {(data?.recently_practiced?.length ?? 0) > 0 && (
        <section className="module-panel">
          <h2>Recently practiced</h2>
          <div className="chip-row">
            {data!.recently_practiced.map((item) => (
              <Link key={item.href} to={item.href} className="chip-link">
                {item.title}
              </Link>
            ))}
          </div>
        </section>
      )}

      {(data?.recommended?.length ?? 0) > 0 && (
        <section className="module-panel">
          <h2>Recommended paths</h2>
          <p className="module-lede">Featured tracks to start with</p>
          <div className="queue-list">
            {data!.recommended.map((path) => (
              <PathRow key={path.id} path={path} />
            ))}
          </div>
        </section>
      )}

      <div className="track-selectors" role="tablist" aria-label="Practice sections">
        <button
          type="button"
          role="tab"
          aria-selected={!activeSection}
          className={`track-selector ${!activeSection ? 'selected' : ''}`}
          onClick={() => setActiveSection('')}
        >
          <strong>All</strong>
        </button>
        {(data?.sections ?? []).map((section) => (
          <button
            key={section.key}
            type="button"
            role="tab"
            aria-selected={activeSection === section.key}
            className={`track-selector ${activeSection === section.key ? 'selected' : ''}`}
            onClick={() => setActiveSection(section.key)}
          >
            <strong>{section.label}</strong>
          </button>
        ))}
      </div>

      {isLoading ? (
        <p className="text-sm text-[var(--color-text-muted)]">Loading practice hub...</p>
      ) : isError ? (
        <p className="text-sm text-[var(--color-danger)]" role="alert">
          Unable to load practice hub.
        </p>
      ) : sections.length === 0 ? (
        <p className="text-sm text-[var(--color-text-muted)]">No practice paths in this section.</p>
      ) : (
        sections.map((section) => (
          <section key={section.key} className="module-panel">
            <h2>{section.label}</h2>
            <div className="queue-list">
              {section.paths.map((path) => (
                <PathRow key={path.id} path={path} />
              ))}
            </div>
          </section>
        ))
      )}

      <nav className="module-footer-links" aria-label="Practice banks">
        <Link to="/practice/aptitude">Aptitude & Reasoning</Link>
        <Link to="/practice/sql">SQL</Link>
        <Link to="/practice/dsa">Programming & DSA</Link>
        <Link to="/practice/mcq">Subject quizzes</Link>
        <Link to="/practice/projects">Projects</Link>
        <Link to="/practice/projects">Projects hub</Link>
        <Link to="/practice/playground">Playground</Link>
        <Link to="/learn/quizzes/pack-crt-shared">CRT pack</Link>
      </nav>
    </div>
  )
}
