import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
import { fetchAdminPracticePaths, patchAdminPath } from '@/services/learnService'

export function AdminPracticePathsPage() {
  const queryClient = useQueryClient()
  const { data, isLoading } = useQuery({
    queryKey: ['admin-practice-paths'],
    queryFn: fetchAdminPracticePaths,
  })

  const toggle = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      patchAdminPath(id, { is_active }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-practice-paths'] }),
  })

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold">Practice Paths</h2>
        <p className="text-sm text-[var(--color-text-muted)]">
          Minimal admin: list and toggle active. Full authoring can expand later.
        </p>
      </div>
      <Card>
        <CardHeader title="All paths" />
        {isLoading ? (
          <p className="text-sm text-[var(--color-text-muted)]">Loading...</p>
        ) : (
          <ul className="divide-y divide-[var(--color-border)] text-sm">
            {(data ?? []).map((path) => (
              <li key={String(path.id)} className="flex flex-wrap items-center justify-between gap-2 py-3">
                <div>
                  <p className="font-medium">{String(path.title)}</p>
                  <p className="text-xs text-[var(--color-text-muted)]">
                    {String(path.slug)} · {String(path.path_type)} · {String(path.availability)}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={path.is_active ? 'success' : 'warning'}>
                    {path.is_active ? 'Active' : 'Inactive'}
                  </Badge>
                  <Button
                    variant="secondary"
                    onClick={() =>
                      toggle.mutate({ id: String(path.id), is_active: !path.is_active })
                    }
                  >
                    Toggle active
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
