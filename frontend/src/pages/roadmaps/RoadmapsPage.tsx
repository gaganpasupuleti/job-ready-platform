import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { fetchRoadmapCatalog } from '@/services/roadmapService'

function categoryForSlug(slug: string): string {
  if (slug.includes('ai') || slug.includes('ml') || slug.includes('data')) return 'Data & AI'
  if (slug.includes('frontend') || slug.includes('react') || slug.includes('vue')) return 'Frontend'
  if (slug.includes('backend') || slug.includes('devops') || slug.includes('cloud')) return 'Platform'
  if (slug.includes('design') || slug.includes('product') || slug.includes('ux')) return 'Design & product'
  return 'Engineering'
}

export function RoadmapsPage() {
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState<string>('all')

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['roadmap-catalog'],
    queryFn: fetchRoadmapCatalog,
    retry: false,
  })

  const roadmaps = data?.roadmaps ?? []

  const categories = useMemo(() => {
    const set = new Set(roadmaps.map((item) => categoryForSlug(item.family_slug)))
    return ['all', ...Array.from(set).sort()]
  }, [roadmaps])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return roadmaps.filter((item) => {
      if (category !== 'all' && categoryForSlug(item.family_slug) !== category) return false
      if (!q) return true
      return (
        item.title.toLowerCase().includes(q) ||
        item.family_slug.includes(q) ||
        item.description.toLowerCase().includes(q)
      )
    })
  }, [roadmaps, query, category])

  return (
    <div className="module-page space-y-6">
      <header className="module-heading">
        <div>
          <p className="eyebrow">Career</p>
          <h1>Career roadmaps</h1>
          <p className="mt-1 max-w-2xl text-sm text-[var(--color-text-muted)]">
            {data?.meta?.total
              ? `${data.meta.total} paths in catalog. ${data.meta.with_graph_cache ?? '—'} cached on server; others fetch from roadmap.sh on first open. Articles need local syllabus content.`
              : 'Interactive career paths with map and topic notes.'}
          </p>
        </div>
      </header>

      {data?.source === 'bundle' ? (
        <p className="text-xs text-[var(--color-text-muted)]" role="status">
          Using bundled catalog while the API is unavailable.
        </p>
      ) : null}

      <div className="roadmap-catalog-tools flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-end">
        <label className="flex min-w-[12rem] flex-1 flex-col gap-1 text-sm">
          <span className="font-semibold">Search</span>
          <input
            className="jr-control px-3 py-2"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Role or skill…"
            aria-label="Search roadmaps"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className="font-semibold">Category</span>
          <select
            className="jr-control px-3 py-2"
            value={category}
            onChange={(event) => setCategory(event.target.value)}
            aria-label="Filter by category"
          >
            {categories.map((value) => (
              <option key={value} value={value}>
                {value === 'all' ? 'All categories' : value}
              </option>
            ))}
          </select>
        </label>
      </div>

      {isLoading ? <p className="text-sm text-[var(--color-text-muted)]">Loading roadmaps…</p> : null}
      {isError ? (
        <div className="space-y-2">
          <p className="text-sm text-[var(--color-danger)]" role="alert">Could not load roadmaps.</p>
          <Button type="button" variant="secondary" size="sm" onClick={() => refetch()}>
            Retry
          </Button>
        </div>
      ) : null}

      <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {filtered.map((item) => (
          <li key={item.family_slug}>
            <Link
              to={`/roadmaps/${item.family_slug}`}
              className="roadmap-catalog-card block h-full rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] p-4 no-underline transition-colors hover:border-[var(--color-border-strong)]"
            >
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-base font-semibold text-[var(--color-text)]">{item.title}</h2>
                {item.preview_only ? <Badge variant="warning">Preview</Badge> : null}
                {!item.student_eligible ? <Badge variant="default">Staff</Badge> : null}
                {item.graph_available === false ? (
                  <Badge variant="warning">Fetch on open</Badge>
                ) : item.source === 'official' || item.source === 'roadmap.sh' ? (
                  <Badge variant="success">Cached map</Badge>
                ) : null}
              </div>
              <p className="mt-2 text-sm text-[var(--color-text-muted)] line-clamp-2">{item.description}</p>
              <p className="mt-3 text-xs text-[var(--color-text-subtle)]">
                {item.articles_available ? 'Map + articles' : 'Map only (articles not provisioned)'}
              </p>
              <span className="mt-3 inline-block text-sm font-semibold text-[var(--color-accent)]">
                Open roadmap →
              </span>
            </Link>
          </li>
        ))}
      </ul>

      {!isLoading && !isError && filtered.length === 0 ? (
        <p className="text-sm text-[var(--color-text-muted)]">
          No roadmaps match your search. Try another keyword or category.
        </p>
      ) : null}
    </div>
  )
}
