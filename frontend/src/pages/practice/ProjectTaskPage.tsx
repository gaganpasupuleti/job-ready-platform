import { useMemo } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
import {
  EmptyState,
  ErrorState,
  HintPanel,
  LoadingState,
  PracticeHeader,
  PracticeProgress,
  PracticeStatusBadge,
  SuccessState,
  apiErrorMessage,
} from '@/components/practice-workspace/PracticeWorkspace'
import {
  completeProjectTask,
  fetchProjectTask,
  updateProjectTaskChecklist,
} from '@/services/learnService'

function asText(value: unknown) {
  return typeof value === 'string' ? value : value ? JSON.stringify(value, null, 2) : ''
}

function checklistItems(raw: unknown[]) {
  return raw.map((entry, index) => {
    if (typeof entry === 'string') return { id: String(index), label: entry, required: true }
    const row = entry as { id?: string; label?: string; text?: string; required?: boolean }
    return {
      id: String(row.id ?? index),
      label: row.label || row.text || `Item ${index + 1}`,
      required: row.required !== false,
    }
  })
}

export function ProjectTaskPage() {
  const { slug = '', taskId = '' } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { data, isLoading, error } = useQuery({
    queryKey: ['project-task', slug, taskId],
    queryFn: () => fetchProjectTask(slug, taskId),
    enabled: Boolean(slug && taskId),
  })

  const complete = useMutation({
    mutationFn: () => completeProjectTask(data!.project_id, data!.task.id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['project-task', slug, taskId] })
      void queryClient.invalidateQueries({ queryKey: ['project', slug] })
    },
  })

  const checklistMut = useMutation({
    mutationFn: (checked: Record<string, boolean>) =>
      updateProjectTaskChecklist(data!.project_id, data!.task.id, checked),
    onSuccess: (body: { completed?: boolean }) => {
      void queryClient.invalidateQueries({ queryKey: ['project-task', slug, taskId] })
      void queryClient.invalidateQueries({ queryKey: ['project', slug] })
      if (body.completed && data?.next_task_id) {
        navigate(`/projects/${slug}/tasks/${data.next_task_id}`)
      }
    },
  })

  const items = useMemo(() => checklistItems(data?.task.checklist_json ?? []), [data])
  const body = (data?.task.body_json ?? {}) as Record<string, unknown>
  const type = data?.task.task_type ?? 'concept'
  const linked =
    Boolean(data?.task.coding_problem_id) ||
    Boolean(data?.task.sql_problem_id) ||
    Boolean(data?.task.topic_id) ||
    Boolean(data?.task.scenario_slug)
  const engineHref = data?.task.engine_href
    ? `${data.task.engine_href}${data.task.engine_href.includes('?') ? '&' : '?'}fromProject=${slug}`
    : null

  if (isLoading) return <LoadingState label="Loading project task" />
  if (error || !data) return <ErrorState message={apiErrorMessage(error, 'Task not found.')} />

  const task = data.task
  const state = task.checklist_state ?? {}

  if (data.project_completed && data.project_percent >= 100) {
    return (
      <div className="space-y-4">
        <PracticeHeader backTo={`/projects/${slug}`} backLabel="Project" title={data.project_title} />
        <SuccessState title="PROJECT COMPLETED ✓">
          <p>Skills practiced: {data.skills.join(', ') || '—'}</p>
          <p>Estimated effort: {data.estimated_minutes ?? '—'} minutes</p>
          {data.completed_at && <p>Completed {new Date(data.completed_at).toLocaleString()}</p>}
          <div className="mt-3 flex gap-2">
            <Link to={`/projects/${slug}`}>
              <Button variant="secondary">Review Project</Button>
            </Link>
            <Link to="/practice/projects">
              <Button variant="primary">Start Another Project</Button>
            </Link>
          </div>
        </SuccessState>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <PracticeHeader backTo={`/projects/${slug}`} backLabel={data.project_title} title={task.title}>
        <div className="mt-2 flex flex-wrap gap-2">
          <Badge>{type}</Badge>
          <PracticeStatusBadge status={task.status} />
          {task.estimated_minutes && <Badge>{task.estimated_minutes} min</Badge>}
        </div>
        <div className="mt-2 max-w-xs">
          <PracticeProgress percent={data.project_percent} label={`Project ${data.project_percent}%`} />
        </div>
      </PracticeHeader>
      <div className="flex gap-2">
        {data.prev_task_id && (
          <Link to={`/projects/${slug}/tasks/${data.prev_task_id}`}>
            <Button variant="ghost" size="sm">Previous</Button>
          </Link>
        )}
        {data.next_task_id && (
          <Link to={`/projects/${slug}/tasks/${data.next_task_id}`}>
            <Button variant="ghost" size="sm">Next</Button>
          </Link>
        )}
      </div>

      {task.summary && <p className="text-sm text-[var(--color-text-muted)]">{task.summary}</p>}

      {type === 'concept' && (
        <Card>
          <CardHeader title="Objective" />
          <p className="whitespace-pre-wrap text-sm">{asText(body.objective || body.explanation || task.summary)}</p>
          {Array.isArray(body.examples) && (
            <ul className="mt-3 list-disc pl-5 text-sm">
              {(body.examples as string[]).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          )}
        </Card>
      )}

      {(type === 'coding' || type === 'sql' || type === 'mcq' || type === 'scenario') && (
        <Card>
          {linked && engineHref ? (
            <>
              <p className="text-sm">This task is graded in the linked practice engine. Completing that challenge completes the task automatically.</p>
              <Link to={engineHref} className="mt-3 inline-block">
                <Button variant="primary">
                  {type === 'coding' && 'Open coding workspace'}
                  {type === 'sql' && 'Open SQL workspace'}
                  {type === 'mcq' && 'Open MCQ practice'}
                  {type === 'scenario' && 'Open scenario'}
                </Button>
              </Link>
            </>
          ) : (
            <EmptyState
              title="Workspace disabled"
              description="No linked challenge is configured. Follow the implementation brief below without fake execution."
            />
          )}
        </Card>
      )}

      {(type === 'implementation' || type === 'review' || type === 'checklist' || type === 'concept') && (
        <Card>
          {asText(body.requirements) && (
            <div className="mb-3">
              <h3 className="text-sm font-medium">Requirements</h3>
              <p className="whitespace-pre-wrap text-sm text-[var(--color-text-muted)]">{asText(body.requirements)}</p>
            </div>
          )}
          {asText(body.acceptance) && (
            <div className="mb-3">
              <h3 className="text-sm font-medium">Acceptance criteria</h3>
              <p className="whitespace-pre-wrap text-sm">{asText(body.acceptance)}</p>
            </div>
          )}
          {Array.isArray(body.hints) && (
            <HintPanel
              hints={body.hints as string[]}
              revealed={1}
              onReveal={() => undefined}
            />
          )}
          {items.length > 0 && (
            <ul className="space-y-2">
              {items.map((item) => (
                <li key={item.id}>
                  <label className="flex items-start gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={Boolean(state[item.id])}
                      onChange={(e) => checklistMut.mutate({ [item.id]: e.target.checked })}
                    />
                    <span>{item.label}</span>
                  </label>
                </li>
              ))}
            </ul>
          )}
          {type === 'implementation' && task.status !== 'completed' && (
            <Button className="mt-3" onClick={() => complete.mutate()} disabled={complete.isPending}>
              Submit for self-review
            </Button>
          )}
          {type === 'concept' && task.status !== 'completed' && !linked && (
            <Button className="mt-3" onClick={() => complete.mutate()} disabled={complete.isPending}>
              Mark Complete
            </Button>
          )}
        </Card>
      )}
    </div>
  )
}
