import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Card, CardHeader } from '@/components/common/Card'
import { fetchPracticePath } from '@/services/learnService'

export function PracticePathPage() {
  const { slug = '' } = useParams()
  const { data, isLoading } = useQuery({
    queryKey: ['practice-path', slug],
    queryFn: () => fetchPracticePath(slug),
    enabled: Boolean(slug),
  })

  if (isLoading || !data) {
    return <p className="text-sm text-[var(--color-text-muted)]">Loading path...</p>
  }

  return (
    <div className="space-y-6">
      <div>
        <Link to="/practice" className="text-xs text-[var(--color-accent)] hover:underline">
          ← Practice Hub
        </Link>
        <h2 className="mt-1 text-lg font-semibold text-[var(--color-text)]">{data.title}</h2>
        <p className="text-sm text-[var(--color-text-muted)]">{data.short_description}</p>
        <div className="mt-2 flex flex-wrap gap-2">
          <Badge>{data.difficulty}</Badge>
          <Badge>{data.path_type}</Badge>
          <Badge variant={data.availability === 'available' ? 'success' : 'warning'}>
            {data.availability === 'available' ? 'Available' : 'Coming Soon'}
          </Badge>
          {data.progress_percent > 0 && <Badge>{data.progress_percent}% progress</Badge>}
        </div>
      </div>

      {data.description && (
        <Card>
          <p className="whitespace-pre-wrap text-sm text-[var(--color-text-muted)]">{data.description}</p>
        </Card>
      )}

      {data.external_route && (
        <Link to={data.external_route} className="text-sm text-[var(--color-accent)] hover:underline">
          Open linked practice area →
        </Link>
      )}

      {data.sections.map((section) => (
        <Card key={section.id}>
          <CardHeader title={section.title} />
          <ul className="space-y-2">
            {section.items.map((item) => (
              <li
                key={item.id}
                className="flex items-center justify-between gap-2 border-t border-[var(--color-border)] py-2 text-sm"
              >
                <span>{item.title ?? item.item_type}</span>
                {item.href ? (
                  <Link to={item.href} className="text-[var(--color-accent)] hover:underline">
                    Open
                  </Link>
                ) : (
                  <span className="text-xs text-[var(--color-text-muted)]">Coming soon</span>
                )}
              </li>
            ))}
            {!section.items.length && (
              <li className="text-sm text-[var(--color-text-muted)]">
                No items yet — path shell ready for content.
              </li>
            )}
          </ul>
        </Card>
      ))}
    </div>
  )
}
