import { Link, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
import { completeProjectTask, fetchProject, startProject } from '@/services/learnService'

export function ProjectDetailPage() {
  const { slug = '' } = useParams()
  const queryClient = useQueryClient()
  const { data, isLoading } = useQuery({
    queryKey: ['project', slug],
    queryFn: () => fetchProject(slug),
    enabled: Boolean(slug),
  })

  const start = useMutation({
    mutationFn: () => startProject(data!.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['project', slug] }),
  })

  const complete = useMutation({
    mutationFn: (taskId: string) => completeProjectTask(data!.id, taskId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['project', slug] })
      void queryClient.invalidateQueries({ queryKey: ['practice-hub'] })
      void queryClient.invalidateQueries({ queryKey: ['continue-learning'] })
    },
  })

  if (isLoading || !data) {
    return <p className="text-sm text-[var(--color-text-muted)]">Loading project...</p>
  }

  const currentHref = data.current_task_href

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <Link to="/practice/projects" className="text-xs text-[var(--color-accent)] hover:underline">
            ← Projects
          </Link>
          <h2 className="mt-1 text-lg font-semibold text-[var(--color-text)]">{data.title}</h2>
          <p className="text-sm text-[var(--color-text-muted)]">{data.short_description}</p>
          <div className="mt-2 flex flex-wrap gap-2">
            <Badge>{data.difficulty}</Badge>
            <Badge>{data.category_key}</Badge>
            {data.technology && <Badge>{data.technology}</Badge>}
            {data.estimated_minutes != null && <Badge>{data.estimated_minutes} min</Badge>}
            <Badge variant={data.availability === 'available' ? 'success' : 'warning'}>
              {data.availability}
            </Badge>
            <Badge>{data.progress_percent}%</Badge>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          {data.status === 'not_started' ? (
            <Button variant="primary" onClick={() => start.mutate()} disabled={start.isPending}>
              Start project
            </Button>
          ) : (
            <Button variant="primary" onClick={() => start.mutate()} disabled={start.isPending}>
              Continue project
            </Button>
          )}
          {currentHref && (
            <Link to={currentHref}>
              <Button variant="secondary">Open current task</Button>
            </Link>
          )}
        </div>
      </div>

      {data.description && (
        <Card>
          <CardHeader title="Overview" />
          <p className="whitespace-pre-wrap text-sm text-[var(--color-text-muted)]">{data.description}</p>
          {data.final_objective && (
            <p className="mt-3 text-sm">
              <span className="font-medium">Final objective: </span>
              {data.final_objective}
            </p>
          )}
        </Card>
      )}

      {(data.skills.length > 0 || data.prerequisites.length > 0) && (
        <div className="grid gap-3 md:grid-cols-2">
          <Card>
            <CardHeader title="Skills" />
            <ul className="list-disc pl-5 text-sm text-[var(--color-text-muted)]">
              {data.skills.map((s) => (
                <li key={s}>{s}</li>
              ))}
            </ul>
          </Card>
          <Card>
            <CardHeader title="Prerequisites" />
            <ul className="list-disc pl-5 text-sm text-[var(--color-text-muted)]">
              {data.prerequisites.map((s) => (
                <li key={s}>{s}</li>
              ))}
            </ul>
          </Card>
        </div>
      )}

      <Card>
        <CardHeader
          title="Progress"
          description={`${data.completed_task_count}/${data.task_count} tasks · ${data.status}`}
        />
        <div className="h-2 overflow-hidden rounded-full bg-[var(--color-surface-muted)]">
          <div
            className="h-full bg-[var(--color-accent)]"
            style={{ width: `${data.progress_percent}%` }}
          />
        </div>
      </Card>

      {data.modules.map((mod) => (
        <Card key={mod.id}>
          <CardHeader title={mod.title} />
          <ul className="space-y-2 text-sm">
            {mod.tasks.map((task) => (
              <li key={task.id} className="border-t border-[var(--color-border)] py-3">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <p className="font-medium">{task.title}</p>
                    <p className="text-xs text-[var(--color-text-subtle)]">
                      {task.task_type} · {task.status}
                    </p>
                    {task.summary && (
                      <p className="mt-1 text-[var(--color-text-muted)]">{task.summary}</p>
                    )}
                    {task.checklist_json?.length > 0 && (
                      <ul className="mt-2 list-disc pl-5 text-[var(--color-text-muted)]">
                        {task.checklist_json.map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {task.href && (
                      <Link to={task.href} className="text-[var(--color-accent)] hover:underline">
                        Open engine
                      </Link>
                    )}
                    {task.status !== 'completed' && (
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => complete.mutate(task.id)}
                        disabled={complete.isPending}
                      >
                        Mark complete
                      </Button>
                    )}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </Card>
      ))}
    </div>
  )
}
