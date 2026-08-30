import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Card } from '@/components/common/Card'
import { fetchProjects } from '@/services/learnService'

export function ProjectsPage() {
  const [category, setCategory] = useState('')
  const { data, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: fetchProjects,
  })

  const categories = useMemo(() => {
    const keys = new Set((data ?? []).map((p) => p.category_key))
    return [...keys].sort()
  }, [data])

  const visible = (data ?? []).filter((p) => !category || p.category_key === category)

  return (
    <div className="space-y-6">
      <div>
        <Link to="/practice" className="text-xs text-[var(--color-accent)] hover:underline">
          ← Practice Hub
        </Link>
        <h2 className="mt-1 text-lg font-semibold text-[var(--color-text)]">Projects</h2>
        <p className="text-sm text-[var(--color-text-muted)]">
          Guided builds that reuse coding, SQL, and MCQ engines. Original Job Ready content.
        </p>
      </div>

      <div className="flex gap-2 overflow-x-auto pb-1">
        <button
          type="button"
          className={`whitespace-nowrap rounded-full border px-3 py-1.5 text-xs ${
            !category
              ? 'border-[var(--color-accent)] bg-[var(--color-accent-muted)] text-[var(--color-accent)]'
              : 'border-[var(--color-border)]'
          }`}
          onClick={() => setCategory('')}
        >
          All
        </button>
        {categories.map((key) => (
          <button
            key={key}
            type="button"
            className={`whitespace-nowrap rounded-full border px-3 py-1.5 text-xs ${
              category === key
                ? 'border-[var(--color-accent)] bg-[var(--color-accent-muted)] text-[var(--color-accent)]'
                : 'border-[var(--color-border)]'
            }`}
            onClick={() => setCategory(key)}
          >
            {key}
          </button>
        ))}
      </div>

      {isLoading ? (
        <p className="text-sm text-[var(--color-text-muted)]">Loading projects...</p>
      ) : (
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {visible.map((project) => {
            const soon = project.availability === 'coming_soon'
            const href = project.href || `/projects/${project.slug}`
            return (
              <Link
                key={project.id}
                to={soon ? '#' : href}
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
                    {project.technology ?? project.category_key}
                    {project.estimated_minutes ? ` · ${project.estimated_minutes} min` : ''}
                    {` · ${project.task_count} tasks`}
                    {project.progress_percent > 0 ? ` · ${project.progress_percent}%` : ''}
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
