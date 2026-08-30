import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Card } from '@/components/common/Card'
import { fetchProjects } from '@/services/learnService'

export function ProjectsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: fetchProjects,
  })

  return (
    <div className="space-y-6">
      <div>
        <Link to="/practice" className="text-xs text-[var(--color-accent)] hover:underline">
          ← Practice Hub
        </Link>
        <h2 className="mt-1 text-lg font-semibold text-[var(--color-text)]">Projects</h2>
        <p className="text-sm text-[var(--color-text-muted)]">
          Build-from-scratch practice. Categories without full content stay marked Coming Soon.
        </p>
      </div>

      {isLoading ? (
        <p className="text-sm text-[var(--color-text-muted)]">Loading projects...</p>
      ) : (
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {(data ?? []).map((project) => {
            const soon = project.availability === 'coming_soon'
            return (
              <Link
                key={project.id}
                to={soon ? '#' : `/practice/projects/${project.slug}`}
                onClick={(e) => soon && e.preventDefault()}
                className={soon ? 'pointer-events-none opacity-60' : ''}
              >
                <Card className="h-full transition hover:border-[var(--color-accent)]">
                  <div className="mb-2 flex flex-wrap gap-2">
                    <h3 className="font-medium">{project.title}</h3>
                    <Badge>{project.difficulty}</Badge>
                    <Badge variant={soon ? 'warning' : 'success'}>
                      {soon ? 'Coming Soon' : 'Available'}
                    </Badge>
                  </div>
                  <p className="text-sm text-[var(--color-text-muted)]">{project.short_description}</p>
                  <p className="mt-2 text-xs text-[var(--color-text-subtle)]">
                    {project.category_key}
                    {project.technology ? ` · ${project.technology}` : ''}
                    {` · ${project.task_count} tasks`}
                  </p>
                </Card>
              </Link>
            )
          })}
        </div>
      )}
    </div>
  )
}
