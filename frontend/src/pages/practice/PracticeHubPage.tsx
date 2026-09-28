import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { PracticeTrackNav } from '@/components/practice/PracticeTrackNav'
import { Input } from '@/components/common/Field'
import { fetchCodingProgress } from '@/services/codingService'
import {
  catalogRouteKind,
  continuationAction,
  humanLabel,
  pathIsOpen,
  practiceCountLabel,
  type CatalogState,
} from '@/lib/studentLabels'
import { fetchSqlProgress } from '@/services/sqlService'
import {
  fetchPracticeHub,
  searchPractice,
  type PracticePathCard,
} from '@/services/learnService'

function pathHref(path: PracticePathCard) {
  if (path.external_route) return path.external_route
  return `/practice/paths/${path.slug}`
}

type CatalogSnap = { state: CatalogState; count: number | null }

function catalogFor(path: PracticePathCard, catalogs: { sql: CatalogSnap; dsa: CatalogSnap }): CatalogSnap {
  const kind = catalogRouteKind(path.external_route)
  if (kind === 'sql') return catalogs.sql
  if (kind === 'dsa') return catalogs.dsa
  return { state: 'idle', count: null }
}

function pathOpen(path: PracticePathCard, catalogs: { sql: CatalogSnap; dsa: CatalogSnap }) {
  const catalog = catalogFor(path, catalogs)
  return pathIsOpen({
    availability: path.availability,
    externalRoute: path.external_route,
    catalogCount: catalog.count,
    catalogState: catalog.state,
  })
}

function pathActionLabel(path: PracticePathCard, open: boolean) {
  if (!open) return 'Soon'
  const action = continuationAction({ href: pathHref(path), progress_percent: path.progress_percent })
  if (action.label === 'Continue' || action.label === 'Start') return action.label
  return path.progress_percent > 0 ? 'Explore' : 'Start'
}

function PathRow({ path, catalogs }: { path: PracticePathCard; catalogs: { sql: CatalogSnap; dsa: CatalogSnap } }) {
  const catalog = catalogFor(path, catalogs)
  const open = pathOpen(path, catalogs)
  const action = continuationAction({ href: pathHref(path), progress_percent: path.progress_percent })
  const countLabel = practiceCountLabel({
    itemCount: path.item_count,
    externalRoute: path.external_route,
    catalogCount: catalog.count,
    catalogState: catalog.state,
    availability: open ? 'available' : path.availability,
  })
  const body = (
    <>
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-1.5">
          <strong>{path.title}</strong>
          <Badge>{humanLabel(path.difficulty)}</Badge>
          {open ? <Badge variant="success">Available</Badge> : <Badge variant="warning">Coming soon</Badge>}
        </div>
        <p className="mt-0.5 text-xs text-[var(--color-text-muted)]">{path.short_description}</p>
        <p className="mt-1 text-[11px] text-[var(--color-text-subtle)]">
          {path.language ? `${path.language} · ` : ''}
          {countLabel}
          {path.progress_percent > 0 ? ` · ${path.progress_percent}% complete` : ' · Not started'}
        </p>
        {open && action.note ? <p className="mt-1 text-[11px] text-[var(--color-text-subtle)]">{action.note}</p> : null}
      </div>
      <span className="queue-meta">{pathActionLabel(path, open)}</span>
    </>
  )
  if (!open) {
    return (
      <div className="v4-queue-row is-disabled" aria-disabled="true">
        {body}
      </div>
    )
  }
  return (
    <Link to={pathHref(path)} className="v4-queue-row">
      {body}
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
  const sqlCatalog = useQuery({ queryKey: ['sql-progress'], queryFn: fetchSqlProgress })
  const dsaCatalog = useQuery({ queryKey: ['coding-progress'], queryFn: fetchCodingProgress })

  const catalogs = useMemo(() => {
    const asSnap = (query: typeof sqlCatalog): CatalogSnap => {
      if (query.isSuccess) return { state: 'ready', count: query.data?.total_problems ?? null }
      if (query.isError) return { state: 'error', count: null }
      if (query.isPending) return { state: 'loading', count: null }
      return { state: 'idle', count: null }
    }
    return { sql: asSnap(sqlCatalog), dsa: asSnap(dsaCatalog) }
  }, [dsaCatalog, sqlCatalog])

  const recommended = useMemo(
    () => (data?.recommended ?? []).filter((path) => pathOpen(path, catalogs)),
    [catalogs, data],
  )
  const recommendedIds = useMemo(() => new Set(recommended.map((path) => path.id)), [recommended])

  const sections = useMemo(() => {
    if (!data?.sections) return []
    const visible = activeSection ? data.sections.filter((section) => section.key === activeSection) : data.sections
    return visible
      .map((section) => ({
        ...section,
        paths: [...section.paths]
          .filter((path) => !recommendedIds.has(path.id))
          .sort((left, right) => Number(pathOpen(right, catalogs)) - Number(pathOpen(left, catalogs))),
      }))
      .filter((section) => section.paths.length > 0)
  }, [activeSection, catalogs, data, recommendedIds])

  const primaryPath = recommended[0] ?? sections.flatMap((section) => section.paths).find((path) => pathOpen(path, catalogs))

  return (
    <div className="module-page practice-hub">
      <PracticeTrackNav />
      <header className="module-heading">
        <div>
          <p className="eyebrow">Practice</p>
          <h1>Practice Hub</h1>
          <p>Guided paths for languages, DSA, SQL, projects, and interview preparation.</p>
        </div>
        {primaryPath ? (
          <Link to={pathHref(primaryPath)}>
            <Button variant="primary" size="sm">
              {pathActionLabel(primaryPath, true)} {primaryPath.title}
            </Button>
          </Link>
        ) : null}
      </header>

      <Link to="/practice/typing" className="v4-queue-row">
        <div><strong>Typing practice</strong><p className="mt-0.5 text-xs text-[var(--color-text-muted)]">Build keyboard fluency with text, code, and your own passages.</p></div>
        <span className="queue-meta">Start typing →</span>
      </Link>

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
                  <span>{humanLabel(item.kind)}</span>
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
            {data!.continue_learning.map((item) => {
              const action = continuationAction(item)
              return (
                <Link key={item.href} to={item.href} className="v4-queue-row">
                  <div>
                    <strong>{item.title}</strong>
                    {item.subtitle ? (
                      <p className="mt-0.5 text-xs text-[var(--color-text-muted)]">{item.subtitle}</p>
                    ) : null}
                    {action.note ? <p className="mt-0.5 text-xs text-[var(--color-text-subtle)]">{action.note}</p> : null}
                  </div>
                  <span className="queue-meta">{action.label}</span>
                </Link>
              )
            })}
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

      {recommended.length > 0 && (
        <section className="module-panel">
          <h2>Recommended paths</h2>
          <p className="module-lede">Featured tracks to start with</p>
          <div className="queue-list">
            {recommended.map((path) => (
              <PathRow key={path.id} path={path} catalogs={catalogs} />
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
                <PathRow key={path.id} path={path} catalogs={catalogs} />
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
        <Link to="/practice/playground">Playground</Link>
        <Link to="/learn/quizzes/pack-crt-shared">CRT pack</Link>
      </nav>
    </div>
  )
}
