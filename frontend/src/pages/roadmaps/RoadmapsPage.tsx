import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Card } from '@/components/common/Card'
import { fetchRoadmapCatalog } from '@/services/roadmapService'

export function RoadmapsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['roadmap-catalog'],
    queryFn: fetchRoadmapCatalog,
    retry: false,
  })

  const roadmaps = data?.roadmaps ?? []

  return (
    <div className="module-page space-y-6">
      <header className="module-heading">
        <div>
          <p className="eyebrow">Career</p>
          <h1>Career roadmaps</h1>
          <p className="mt-1 max-w-2xl text-sm text-[var(--color-text-muted)]">
            {roadmaps.length > 0
              ? `${roadmaps.length} interactive career paths. Open any card for the full map and topic notes.`
              : 'Interactive career paths. Open any card for the full map and topic notes.'}
          </p>
        </div>
      </header>

      {data?.source === 'bundle' ? (
        <p className="text-xs text-[var(--color-text-muted)]" role="status">
          Using bundled roadmap list — start the backend to sync the latest catalog from your repo.
        </p>
      ) : null}

      {isLoading ? <p className="text-sm text-[var(--color-text-muted)]">Loading roadmaps…</p> : null}

      <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {roadmaps.map((item) => (
          <li key={item.family_slug}>
            <Card className="h-full">
              <Link
                to={`/roadmaps/${item.family_slug}`}
                className="flex h-full flex-col gap-2 p-4 no-underline"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <h2 className="text-base font-semibold text-[var(--color-text)]">{item.title}</h2>
                  {item.source === 'official' || item.source === 'roadmap.sh' ? (
                    <Badge variant="success">Career path</Badge>
                  ) : null}
                </div>
                <p className="text-sm text-[var(--color-text-muted)] line-clamp-2">{item.description}</p>
                <span className="mt-auto text-sm text-[var(--color-accent)]">Open roadmap →</span>
              </Link>
            </Card>
          </li>
        ))}
      </ul>

      {!isLoading && roadmaps.length === 0 ? (
        <p className="text-sm text-[var(--color-text-muted)]">No roadmaps are published yet.</p>
      ) : null}
    </div>
  )
}
