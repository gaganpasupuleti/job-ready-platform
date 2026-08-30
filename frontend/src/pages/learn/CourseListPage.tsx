import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Card } from '@/components/common/Card'
import { fetchCourses } from '@/services/learnService'

export function CourseListPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['courses'],
    queryFn: fetchCourses,
  })

  return (
    <div className="space-y-6">
      <div>
        <Link to="/practice" className="text-xs text-[var(--color-accent)] hover:underline">
          ← Practice Hub
        </Link>
        <h2 className="mt-1 text-lg font-semibold text-[var(--color-text)]">Interactive Courses</h2>
        <p className="text-sm text-[var(--color-text-muted)]">
          Guided lessons with concepts, interactive code, checkpoints, and hints — no AI tutor.
        </p>
      </div>

      {isLoading ? (
        <p className="text-sm text-[var(--color-text-muted)]">Loading courses...</p>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {(data ?? []).map((course) => (
            <Link key={course.id} to={`/learn/courses/${course.slug}`}>
              <Card className="h-full transition hover:border-[var(--color-accent)]">
                <div className="mb-2 flex flex-wrap gap-2">
                  <h3 className="font-medium text-[var(--color-text)]">{course.title}</h3>
                  <Badge>{course.level}</Badge>
                  {course.is_featured && <Badge variant="success">Featured</Badge>}
                </div>
                <p className="text-sm text-[var(--color-text-muted)]">{course.summary}</p>
                <p className="mt-3 text-xs text-[var(--color-text-subtle)]">
                  {course.lesson_count} lessons
                  {course.progress_percent > 0 ? ` · ${course.progress_percent}% complete` : ''}
                </p>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
