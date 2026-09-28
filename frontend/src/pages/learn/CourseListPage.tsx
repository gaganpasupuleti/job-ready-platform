import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { LearnSubnav } from '@/components/learn/LearnSubnav'
import { humanLabel } from '@/lib/studentLabels'
import { fetchCourses } from '@/services/learnService'

export function CourseListPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['courses'],
    queryFn: fetchCourses,
  })

  return (
    <div className="module-page learn-page">
      <LearnSubnav />
      <header className="module-heading">
        <div>
          <Link to="/practice" className="back-link">
            ← Practice Hub
          </Link>
          <p className="eyebrow">Learn</p>
          <h1>Interactive Courses</h1>
          <p>
            Guided lessons with concepts, interactive code, checkpoints, and hints — no AI tutor.
          </p>
        </div>
      </header>

      {isLoading ? (
        <p className="text-sm text-[var(--color-text-muted)]">Loading courses...</p>
      ) : isError ? (
        <p className="text-sm text-[var(--color-danger)]" role="alert">
          Unable to load courses.
        </p>
      ) : (data ?? []).length === 0 ? (
        <p className="text-sm text-[var(--color-text-muted)]">No courses available yet.</p>
      ) : (
        <div className="course-grid">
          {(data ?? []).map((course) => (
            <Link
              key={course.id}
              to={`/learn/courses/${course.slug}`}
              className="course-tile"
            >
              <div className="flex flex-wrap gap-1.5">
                <strong>{course.title}</strong>
                <Badge>{humanLabel(course.level)}</Badge>
                {course.is_featured && <Badge variant="success">Featured</Badge>}
              </div>
              <p>{course.summary}</p>
              <span>
                {course.lesson_count} lessons
                {course.progress_percent > 0 ? ` · ${course.progress_percent}% lesson progress` : ''}
              </span>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
