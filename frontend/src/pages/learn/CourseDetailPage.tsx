import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { fetchCourse } from '@/services/learnService'

export function CourseDetailPage() {
  const { slug = '' } = useParams()
  const { data, isLoading, isError } = useQuery({
    queryKey: ['course', slug],
    queryFn: () => fetchCourse(slug),
    enabled: Boolean(slug),
  })

  if (isLoading) {
    return <p className="text-sm text-[var(--color-text-muted)]">Loading course...</p>
  }
  if (isError || !data) {
    return (
      <p className="text-sm text-[var(--color-danger)]" role="alert">
        Unable to load this course.
      </p>
    )
  }

  return (
    <div className="module-page learn-page">
      <header className="module-heading curriculum-summary">
        <div>
          <Link to="/learn" className="back-link">
            ← Courses
          </Link>
          <p className="eyebrow">Course</p>
          <h1>{data.title}</h1>
          <p>{data.summary}</p>
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
      </header>

      <div className="module-stack">
        {data.modules.map((mod, index) => (
          <section key={mod.id} className="module-row">
            <div className="module-meta">
              <span className={`module-number ${mod.completed_count >= mod.lesson_count ? 'done' : ''}`}>
                {String(index + 1).padStart(2, '0')}
              </span>
              <div>
                <h2>{mod.title}</h2>
                <p>
                  {mod.completed_count}/{mod.lesson_count} lessons
                  {mod.summary ? ` · ${mod.summary}` : ''}
                </p>
              </div>
            </div>
            <ul className="lesson-list">
              {mod.lessons.map((lesson) => {
                const locked = lesson.status === 'locked'
                const href = `/learn/courses/${data.slug}/${mod.slug}/${lesson.slug}`
                return (
                  <li key={lesson.id}>
                    <div>
                      <p className={locked ? 'is-muted' : ''}>{lesson.title}</p>
                      <span>
                        {lesson.lesson_type} · {lesson.status}
                      </span>
                    </div>
                    {locked ? (
                      <span className="is-muted">Locked</span>
                    ) : (
                      <Link to={href}>Open</Link>
                    )}
                  </li>
                )
              })}
            </ul>
          </section>
        ))}
      </div>
    </div>
  )
}
