import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { apiClient } from '@/api/client'
import { apiEndpoints } from '@/api/config'
import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'

export function AdminProjectsPage() {
  const queryClient = useQueryClient()
  const { data, isLoading } = useQuery({
    queryKey: ['admin-projects'],
    queryFn: async () => {
      const res = await apiClient.get<Array<Record<string, unknown>>>(apiEndpoints.admin.projects)
      return res.data
    },
  })
  const [title, setTitle] = useState('')
  const [slug, setSlug] = useState('')
  const [category, setCategory] = useState('python')

  const create = useMutation({
    mutationFn: async () => {
      await apiClient.post(apiEndpoints.admin.projects, {
        slug,
        title,
        category_key: category,
        short_description: title,
        is_published: false,
        availability: 'available',
      })
    },
    onSuccess: () => {
      setTitle('')
      setSlug('')
      void queryClient.invalidateQueries({ queryKey: ['admin-projects'] })
    },
  })

  const toggle = useMutation({
    mutationFn: ({ id, is_published }: { id: string; is_published: boolean }) =>
      apiClient.patch(apiEndpoints.admin.project(id), { is_published }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-projects'] }),
  })

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold">Projects</h2>
        <p className="text-sm text-[var(--color-text-muted)]">
          Create shells, publish, and link tasks via API. Edit detail after create.
        </p>
      </div>
      <Card>
        <CardHeader title="New project" />
        <form
          className="flex flex-wrap gap-2"
          onSubmit={(e) => {
            e.preventDefault()
            create.mutate()
          }}
        >
          <input
            className="rounded-md border border-[var(--color-border)] px-2 py-1 text-sm"
            placeholder="Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
          />
          <input
            className="rounded-md border border-[var(--color-border)] px-2 py-1 text-sm"
            placeholder="slug"
            value={slug}
            onChange={(e) => setSlug(e.target.value)}
            required
          />
          <input
            className="rounded-md border border-[var(--color-border)] px-2 py-1 text-sm"
            placeholder="category"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          />
          <Button variant="primary" type="submit" disabled={create.isPending}>
            Create
          </Button>
        </form>
      </Card>
      <Card>
        <CardHeader title="All projects" />
        {isLoading ? (
          <p className="text-sm text-[var(--color-text-muted)]">Loading...</p>
        ) : (
          <ul className="divide-y divide-[var(--color-border)] text-sm">
            {(data ?? []).map((project) => (
              <li key={String(project.id)} className="flex flex-wrap items-center justify-between gap-2 py-3">
                <div>
                  <p className="font-medium">{String(project.title)}</p>
                  <p className="text-xs text-[var(--color-text-muted)]">
                    {String(project.slug)} · {String(project.category_key)}
                  </p>
                  <Link
                    to={`/projects/${String(project.slug)}`}
                    className="text-xs text-[var(--color-accent)] hover:underline"
                  >
                    Student view
                  </Link>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={project.is_published ? 'success' : 'warning'}>
                    {project.is_published ? 'Published' : 'Draft'}
                  </Badge>
                  <Button
                    variant="secondary"
                    onClick={() =>
                      toggle.mutate({
                        id: String(project.id),
                        is_published: !project.is_published,
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
