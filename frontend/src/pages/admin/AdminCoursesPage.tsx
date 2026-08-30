import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
import { fetchAdminCourses, patchAdminCourse } from '@/services/learnService'

export function AdminCoursesPage() {
  const queryClient = useQueryClient()
  const { data, isLoading } = useQuery({
    queryKey: ['admin-courses'],
    queryFn: fetchAdminCourses,
  })

  const publish = useMutation({
    mutationFn: ({ id, is_published }: { id: string; is_published: boolean }) =>
      patchAdminCourse(id, { is_published }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-courses'] }),
  })

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold">Courses</h2>
        <p className="text-sm text-[var(--color-text-muted)]">
          Publish/unpublish courses. Lesson bodies are seeded; expand CRUD as needed.
        </p>
      </div>
      <Card>
        <CardHeader title="All courses" />
        {isLoading ? (
          <p className="text-sm text-[var(--color-text-muted)]">Loading...</p>
        ) : (
          <ul className="divide-y divide-[var(--color-border)] text-sm">
            {(data ?? []).map((course) => (
              <li key={String(course.id)} className="flex flex-wrap items-center justify-between gap-2 py-3">
                <div>
                  <p className="font-medium">{String(course.title)}</p>
                  <p className="text-xs text-[var(--color-text-muted)]">
                    {String(course.slug)} · {String(course.level)}
                  </p>
                  <Link
                    to={`/learn/courses/${String(course.slug)}`}
                    className="text-xs text-[var(--color-accent)] hover:underline"
                  >
                    Preview student view
                  </Link>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={course.is_published ? 'success' : 'warning'}>
                    {course.is_published ? 'Published' : 'Draft'}
                  </Badge>
                  <Button
                    variant="secondary"
                    onClick={() =>
                      publish.mutate({
                        id: String(course.id),
                        is_published: !course.is_published,
                      })
                    }
                  >
                    Toggle publish
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  )
}
