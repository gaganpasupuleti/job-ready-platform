import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
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

function PathCard({ path }: { path: PracticePathCard }) {
  const comingSoon = path.availability === 'coming_soon'
  return (
    <Link
      to={comingSoon ? '#' : pathHref(path)}
      className={`block rounded-[var(--radius-control)] border border-[var(--color-border)] bg-[var(--color-surface)] p-3 transition hover:border-[var(--color-accent)] ${
        comingSoon ? 'pointer-events-none opacity-60' : ''
      }`}
      onClick={(e) => comingSoon && e.preventDefault()}
    >
      <div className="mb-1.5 flex flex-wrap items-center gap-1.5">
        <h3 className="text-sm font-medium text-[var(--color-text)]">{path.title}</h3>
        <Badge>{path.difficulty}</Badge>
        {comingSoon ? <Badge variant="warning">Coming Soon</Badge> : <Badge variant="success">Available</Badge>}
      </div>
      <p className="text-xs text-[var(--color-text-muted)]">{path.short_description}</p>
      <p className="mt-1.5 text-[11px] text-[var(--color-text-subtle)]">
        {path.progress_percent > 0 ? `${path.progress_percent}% complete` : 'Not started'}
      </p>
      <div className="mt-2 flex flex-wrap items-center gap-2 text-[11px] text-[var(--color-text-subtle)]">
        {path.language && <span>{path.language}</span>}
        <span>{path.item_count} items</span>
        {path.progress_percent > 0 && !comingSoon && (
          <span className="font-medium text-[var(--color-accent)]">Continue</span>
        )}
      </div>
    </Link>
  )
}

export function PracticeHubPage() {
  const [query, setQuery] = useState('')
  const [activeSection, setActiveSection] = useState<string>('')

  const { data, isLoading } = useQuery({
    queryKey: ['practice-hub'],
    queryFn: fetchPracticeHub,
  })

  const { data: searchData } = useQuery({
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
    <div className="space-y-4">
      <div>
        <h1 className="text-base font-semibold text-[var(--color-text)] sm:text-lg">Practice Hub</h1>
        <p className="mt-0.5 text-sm text-[var(--color-text-muted)]">
          Guided paths for languages, DSA, algorithms, projects, and interview preparation.
        </p>
      </div>

      <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
        <Input
          aria-label="Search practice content"
          placeholder="Search paths, courses, projects..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <Link to="/learn">
          <Button variant="primary" size="sm">
            Browse courses
          </Button>
        </Link>
      </div>

      {query.trim().length >= 2 && (
        <Card>
          <CardHeader title="Search results" />
          <ul className="space-y-2 text-sm">
            {(searchData?.items ?? []).map((item) => (
              <li key={`${item.kind}-${item.href}`}>
                <Link to={item.href} className="text-[var(--color-accent)] hover:underline">
                  {item.title}
                </Link>
                <span className="ml-2 text-xs text-[var(--color-text-muted)]">{item.kind}</span>
              </li>
            ))}
            {!searchData?.items.length && (
              <li className="text-[var(--color-text-muted)]">No matches.</li>
            )}
          </ul>
        </Card>
      )}

      {(data?.continue_learning?.length ?? 0) > 0 && (
        <Card>
          <CardHeader title="Continue Learning" />
          <div className="grid gap-3 sm:grid-cols-2">
            {data!.continue_learning.map((item) => (
              <Link
                key={item.href}
                to={item.href}
                className="rounded-md border border-[var(--color-border)] p-3 hover:border-[var(--color-accent)]"
              >
                <p className="font-medium text-[var(--color-text)]">{item.title}</p>
                {item.subtitle && (
                  <p className="text-xs text-[var(--color-text-muted)]">{item.subtitle}</p>
                )}
                <p className="mt-1 text-xs text-[var(--color-text-subtle)]">{item.progress_percent}%</p>
              </Link>
            ))}
          </div>
        </Card>
      )}

      {(data?.recently_practiced?.length ?? 0) > 0 && (
        <Card>
          <CardHeader title="Recently Practiced" />
          <div className="flex flex-wrap gap-2">
            {data!.recently_practiced.map((item) => (
              <Link
                key={item.href}
                to={item.href}
                className="rounded-full border border-[var(--color-border)] px-3 py-1 text-xs hover:border-[var(--color-accent)]"
              >
                {item.title}
              </Link>
            ))}
          </div>
        </Card>
      )}

      {(data?.recommended?.length ?? 0) > 0 && (
        <Card>
          <CardHeader title="Recommended Paths" description="Featured tracks to start with" />
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {data!.recommended.map((path) => (
              <PathCard key={path.id} path={path} />
            ))}
          </div>
        </Card>
      )}

      <div className="flex gap-2 overflow-x-auto pb-1">
        <button
          type="button"
          className={`whitespace-nowrap rounded-full border px-3 py-1.5 text-xs ${
            !activeSection
              ? 'border-[var(--color-accent)] bg-[var(--color-accent-muted)] text-[var(--color-accent)]'
              : 'border-[var(--color-border)]'
          }`}
          onClick={() => setActiveSection('')}
        >
          All
        </button>
        {(data?.sections ?? []).map((section) => (
          <button
            key={section.key}
            type="button"
            className={`whitespace-nowrap rounded-full border px-3 py-1.5 text-xs ${
              activeSection === section.key
                ? 'border-[var(--color-accent)] bg-[var(--color-accent-muted)] text-[var(--color-accent)]'
                : 'border-[var(--color-border)]'
            }`}
            onClick={() => setActiveSection(section.key)}
          >
            {section.label}
          </button>
        ))}
      </div>

      {isLoading ? (
        <p className="text-sm text-[var(--color-text-muted)]">Loading practice hub...</p>
      ) : (
        sections.map((section) => (
          <section key={section.key} className="space-y-3">
            <h3 className="text-base font-semibold text-[var(--color-text)]">{section.label}</h3>
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {section.paths.map((path) => (
                <PathCard key={path.id} path={path} />
              ))}
            </div>
          </section>
        ))
      )}

      <div className="flex flex-wrap gap-3 text-sm">
        <Link to="/practice/dsa" className="text-[var(--color-accent)] hover:underline">
          DSA problem bank
        </Link>
        <Link to="/practice/sql" className="text-[var(--color-accent)] hover:underline">
          SQL Practice
        </Link>
        <Link to="/practice/mcq" className="text-[var(--color-accent)] hover:underline">
          Technical MCQs
        </Link>
        <Link to="/practice/projects" className="text-[var(--color-accent)] hover:underline">
          Projects hub
        </Link>
      </div>
    </div>
  )
}
