import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Card, CardHeader } from '@/components/common/Card'
import { fetchProject } from '@/services/learnService'

export function ProjectDetailPage() {
  const { slug = '' } = useParams()
  const { data, isLoading } = useQuery({
    queryKey: ['project', slug],
    queryFn: () => fetchProject(slug),
    enabled: Boolean(slug),
  })

  if (isLoading || !data) {
    return <p className="text-sm text-[var(--color-text-muted)]">Loading project...</p>
  }

  return (
    <div className="space-y-6">
      <div>
        <Link to="/practice/projects" className="text-xs text-[var(--color-accent)] hover:underline">
          ← Projects
        </Link>
        <h2 className="mt-1 text-lg font-semibold text-[var(--color-text)]">{data.title}</h2>
        <p className="text-sm text-[var(--color-text-muted)]">{data.short_description}</p>
        <div className="mt-2 flex flex-wrap gap-2">
          <Badge>{data.difficulty}</Badge>
          <Badge>{data.category_key}</Badge>
          {data.technology && <Badge>{data.technology}</Badge>}
          <Badge variant={data.availability === 'available' ? 'success' : 'warning'}>
            {data.availability}
          </Badge>
        </div>
      </div>

      {data.description && (
        <Card>
          <p className="whitespace-pre-wrap text-sm text-[var(--color-text-muted)]">{data.description}</p>
        </Card>
      )}

      {data.modules.map((mod) => (
        <Card key={mod.id}>
          <CardHeader title={mod.title} />
          <ul className="space-y-2 text-sm">
            {mod.tasks.map((task) => (
              <li key={task.id} className="border-t border-[var(--color-border)] py-2">
                <p className="font-medium">{task.title}</p>
                {task.summary && (
                  <p className="text-[var(--color-text-muted)]">{task.summary}</p>
                )}
              </li>
            ))}
          </ul>
        </Card>
      ))}
    </div>
  )
}
