import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
import { fetchCourse } from '@/services/learnService'

export function CourseDetailPage() {
  const { slug = '' } = useParams()
  const { data, isLoading } = useQuery({
    queryKey: ['course', slug],
    queryFn: () => fetchCourse(slug),
    enabled: Boolean(slug),
  })

  if (isLoading || !data) {
    return <p className="text-sm text-[var(--color-text-muted)]">Loading course...</p>
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <Link to="/learn" className="text-xs text-[var(--color-accent)] hover:underline">
            ← Courses
          </Link>
          <h2 className="mt-1 text-lg font-semibold text-[var(--color-text)]">{data.title}</h2>
          <p className="text-sm text-[var(--color-text-muted)]">{data.summary}</p>
          <div className="mt-2 flex flex-wrap gap-2">
            <Badge>{data.level}</Badge>
            <Badge>{data.progress_percent}% complete</Badge>
            <Badge>{data.status}</Badge>
          </div>
        </div>
        {data.continue_href && (
          <Link to={data.continue_href}>
            <Button variant="primary">Continue</Button>
          </Link>
        )}
      </div>

      {data.modules.map((mod) => (
        <Card key={mod.id}>
          <CardHeader
            title={mod.title}
            description={`${mod.completed_count}/${mod.lesson_count} lessons · ${mod.summary ?? ''}`}
          />
          <ul className="divide-y divide-[var(--color-border)]">
            {mod.lessons.map((lesson) => {
              const locked = lesson.status === 'locked'
              const href = `/learn/courses/${data.slug}/${mod.slug}/${lesson.slug}`
              return (
                <li key={lesson.id} className="flex items-center justify-between gap-2 py-2 text-sm">
                  <div>
                    <p className={locked ? 'text-[var(--color-text-muted)]' : 'text-[var(--color-text)]'}>
                      {lesson.title}
                    </p>
                    <p className="text-xs text-[var(--color-text-subtle)]">
                      {lesson.lesson_type} · {lesson.status}
                    </p>
                  </div>
                  {locked ? (
                    <span className="text-xs text-[var(--color-text-muted)]">Locked</span>
                  ) : (
                    <Link to={href} className="text-[var(--color-accent)] hover:underline">
                      Open
                    </Link>
                  )}
                </li>
              )
            })}
          </ul>
        </Card>
      ))}
    </div>
  )
}
