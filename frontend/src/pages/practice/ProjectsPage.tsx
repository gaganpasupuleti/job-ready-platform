import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Card } from '@/components/common/Card'
import { PracticeTrackNav } from '@/components/practice/PracticeTrackNav'
import { ManualAssignmentSection } from '@/features/projects/ManualAssignmentSection'
import { humanLabel } from '@/lib/studentLabels'
import { fetchProjects } from '@/services/learnService'

export function ProjectsPage() {
  const [category, setCategory] = useState('')
  const { data, isLoading, isError } = useQuery({
    queryKey: ['projects'],
    queryFn: fetchProjects,
  })

  const categories = useMemo(() => {
    const keys = new Set((data ?? []).map((p) => p.category_key))
    return [...keys].sort()
  }, [data])

  const visible = (data ?? [])
    .filter((p) => !category || p.category_key === category)
    .slice()
    .sort((a, b) => Number(a.availability === 'coming_soon') - Number(b.availability === 'coming_soon'))

  return (
    <div className="module-page space-y-4">
      <PracticeTrackNav />
      <div>
        <Link to="/practice" className="text-xs text-[var(--color-accent)] hover:underline">
          ← Practice Hub
        </Link>
        <h1 className="mt-1 text-lg font-semibold text-[var(--color-text)]">Projects</h1>
        <p className="text-sm text-[var(--color-text-muted)]">
          Guided builds that reuse coding, SQL, and MCQ engines. Original Job Ready content.
        </p>
      </div>

      <div className="filter-chip-row is-wrapped" role="group" aria-label="Project category">
        <button
          type="button"
          className="filter-chip"
          aria-pressed={!category}
          onClick={() => setCategory('')}
        >
          All
        </button>
        {categories.map((key) => (
          <button
            key={key}
            type="button"
            className="filter-chip"
            aria-pressed={category === key}
            onClick={() => setCategory(key)}
          >
            {humanLabel(key)}
          </button>
        ))}
      </div>

      {isLoading ? (
        <p className="text-sm text-[var(--color-text-muted)]" role="status">Loading projects.</p>
      ) : isError ? (
        <p className="text-sm text-[var(--color-danger)]" role="alert">Could not load projects.</p>
      ) : visible.length === 0 ? (
        <p className="text-sm text-[var(--color-text-muted)]" role="status">No projects in this category.</p>
      ) : (
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {visible.map((project) => {
            const soon = project.availability === 'coming_soon'
            const open = !soon && Boolean(project.href || project.slug)
            const href = project.href || `/projects/${project.slug}`
            const body = (
              <Card className="h-full">
                <div className="mb-2 flex flex-wrap gap-2">
                  <h3 className="font-medium">{project.title}</h3>
                  <Badge>{humanLabel(project.difficulty)}</Badge>
                  <Badge variant={soon ? 'warning' : open ? 'success' : 'default'}>
                    {soon ? 'Coming soon' : open ? 'Available' : 'Locked'}
                  </Badge>
                </div>
                <p className="text-sm text-[var(--color-text-muted)]">{project.short_description}</p>
                <p className="mt-2 text-xs text-[var(--color-text-subtle)]">
                  {project.technology ?? humanLabel(project.category_key)}
                  {project.estimated_minutes ? ` · ${project.estimated_minutes} min` : ''}
                  {` · ${project.task_count} tasks`}
                  {project.progress_percent > 0 ? ` · ${project.progress_percent}%` : ''}
                </p>
                {soon ? (
                  <p className="mt-2 text-xs text-[var(--color-text-muted)]">This project is not open yet.</p>
                ) : null}
              </Card>
            )
            if (!open) {
              return <div key={project.id}>{body}</div>
            }
            return (
              <Link key={project.id} to={href}>
                {body}
              </Link>
            )
          })}
        </div>
      )}

      <ManualAssignmentSection />
    </div>
  )
}
