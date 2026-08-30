import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { Card } from '@/components/common/Card'
import { CodeEditor } from '@/features/dsa/CodeEditor'
import {
  completeLesson,
  fetchLesson,
  recordLessonAttempt,
  sendLessonFeedback,
  startLesson,
} from '@/services/learnService'

type WorkspaceTab = 'statement' | 'editor' | 'submissions' | 'solution' | 'hints' | 'help'

const TAB_LABELS: Record<WorkspaceTab, string> = {
  statement: 'Statement',
  editor: 'Code',
  submissions: 'Submissions',
  solution: 'Solution',
  hints: 'Hints',
  help: 'Help',
}

function StatementBlocks({
  blocks,
}: {
  blocks?: Array<{ type: string; value?: string; language?: string; title?: string; items?: string[]; tone?: string }>
}) {
  if (!blocks?.length) return <p className="text-sm text-[var(--color-text-muted)]">No statement content.</p>
  return (
    <div className="space-y-4 text-sm text-[var(--color-text)]">
      {blocks.map((block, idx) => {
        if (block.type === 'code') {
          return (
            <pre
              key={idx}
              className="overflow-x-auto rounded-md bg-[var(--color-surface-muted)] p-3 font-mono text-xs"
            >
              {block.value}
            </pre>
          )
        }
        if (block.type === 'list') {
          return (
            <div key={idx}>
              {block.title && <p className="mb-1 font-medium">{block.title}</p>}
              <ul className="list-disc space-y-1 pl-5 text-[var(--color-text-muted)]">
                {(block.items ?? []).map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          )
        }
        if (block.type === 'callout') {
          return (
            <div
              key={idx}
              className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface-muted)] p-3 text-[var(--color-text-muted)]"
            >
              {block.value}
            </div>
          )
        }
        return (
          <p key={idx} className="whitespace-pre-wrap text-[var(--color-text-muted)]">
            {block.value}
          </p>
        )
      })}
    </div>
  )
}

export function LessonWorkspacePage() {
  const { courseSlug = '', moduleSlug = '', lessonSlug = '' } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [tab, setTab] = useState<WorkspaceTab>('statement')
  const [code, setCode] = useState('')
  const [hintIndex, setHintIndex] = useState(0)
  const [localAttempts, setLocalAttempts] = useState<
    Array<{ at: string; note: string; codeSnippet: string }>
  >([])
  const [feedbackNote, setFeedbackNote] = useState('')
  const [message, setMessage] = useState<string | null>(null)

  const { data, isLoading, error } = useQuery({
    queryKey: ['lesson', courseSlug, moduleSlug, lessonSlug],
    queryFn: () => fetchLesson(courseSlug, moduleSlug, lessonSlug),
    enabled: Boolean(courseSlug && moduleSlug && lessonSlug),
  })

  useEffect(() => {
    if (!data) return
    const starter =
      data.starter_code?.python ??
      data.starter_code?.javascript ??
      Object.values(data.starter_code ?? {})[0] ??
      ''
    setCode(starter)
    setHintIndex(0)
    setLocalAttempts([])
    setTab('statement')
    void startLesson(data.id).catch(() => undefined)
  }, [data?.id])

  const completeMutation = useMutation({
    mutationFn: () => completeLesson(data!.id),
    onSuccess: async (res) => {
      setMessage('Lesson marked complete.')
      await queryClient.invalidateQueries({ queryKey: ['lesson', courseSlug, moduleSlug, lessonSlug] })
      await queryClient.invalidateQueries({ queryKey: ['course', courseSlug] })
      await queryClient.invalidateQueries({ queryKey: ['practice-hub'] })
      if (res.next_href) navigate(res.next_href)
    },
    onError: () => setMessage('Could not complete lesson. Finish required steps first.'),
  })

  const attemptMutation = useMutation({
    mutationFn: () =>
      recordLessonAttempt(data!.id, {
        code,
        language: 'python',
        is_correct: false,
        note: 'Local practice attempt (Judge0 optional)',
      }),
    onSuccess: () => {
      setLocalAttempts((prev) => [
        {
          at: new Date().toISOString(),
          note: 'Practice run recorded',
          codeSnippet: code.slice(0, 120),
        },
        ...prev,
      ])
      setMessage('Attempt recorded. Use Mark Complete when you are ready (Judge0 not required for this course).')
      setTab('submissions')
    },
  })

  const feedbackMutation = useMutation({
    mutationFn: (payload: { vote?: string; report_issue?: boolean; note?: string }) =>
      sendLessonFeedback(data!.id, payload),
    onSuccess: () => setMessage('Thanks for the feedback.'),
  })

  const tabs = useMemo(() => {
    const base: WorkspaceTab[] = ['statement']
    if (data?.lesson_type === 'interactive_code' || data?.lesson_type === 'practice') {
      base.push('editor', 'submissions')
    }
    base.push('solution', 'hints', 'help')
    return base
  }, [data?.lesson_type])

  if (isLoading) {
    return <p className="text-sm text-[var(--color-text-muted)]">Loading lesson...</p>
  }

  if (error || !data) {
    return (
      <Card>
        <p className="text-sm text-[var(--color-text-muted)]">
          Lesson unavailable or locked. Complete previous lessons first.
        </p>
        <Link to={`/learn/courses/${courseSlug}`} className="mt-2 inline-block text-sm text-[var(--color-accent)]">
          Back to course
        </Link>
      </Card>
    )
  }

  const visibleHints = data.hints.slice(0, Math.max(hintIndex, 0))

  const panel = (
    <>
      {tab === 'statement' && (
        <div className="space-y-4">
          <StatementBlocks blocks={data.statement_json?.blocks} />
          {data.steps.length > 0 && (
            <div className="space-y-3">
              <h4 className="text-sm font-medium">Steps</h4>
              {data.steps.map((step) => (
                <div key={step.id} className="rounded-md border border-[var(--color-border)] p-3 text-sm">
                  <p className="font-medium">{step.title}</p>
                  <p className="mt-1 whitespace-pre-wrap text-[var(--color-text-muted)]">{step.body_md}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {tab === 'editor' && (
        <div className="space-y-3">
          <div className="h-[360px] overflow-hidden rounded-md border border-[var(--color-border)]">
            <CodeEditor value={code} language="python" onChange={setCode} height="360px" />
          </div>
          <p className="text-xs text-[var(--color-text-muted)]">
            Interactive practice uses Monaco here. Full Judge0 grading is available on linked DSA problems when
            configured; this lesson can be completed without execution.
          </p>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="secondary"
              onClick={() => attemptMutation.mutate()}
              disabled={attemptMutation.isPending}
            >
              Record attempt
            </Button>
            {data.coding_problem_slug && (
              <Link to={`/practice/dsa/${data.coding_problem_slug}`}>
                <Button variant="ghost">Open linked DSA problem</Button>
              </Link>
            )}
          </div>
        </div>
      )}

      {tab === 'submissions' && (
        <div className="space-y-2 text-sm">
          <p className="text-[var(--color-text-muted)]">
            Attempts: {data.attempts + localAttempts.length} (server + this session)
          </p>
          {localAttempts.length === 0 ? (
            <p className="text-[var(--color-text-muted)]">No local attempts yet.</p>
          ) : (
            localAttempts.map((a, i) => (
              <div key={i} className="rounded-md border border-[var(--color-border)] p-3">
                <p className="text-xs text-[var(--color-text-subtle)]">{new Date(a.at).toLocaleString()}</p>
                <p>{a.note}</p>
                <pre className="mt-1 overflow-x-auto text-xs text-[var(--color-text-muted)]">{a.codeSnippet}</pre>
              </div>
            ))
          )}
        </div>
      )}

      {tab === 'solution' && (
        <div className="space-y-2 text-sm">
          {data.solution_unlocked && data.solution_json ? (
            <>
              <p className="whitespace-pre-wrap text-[var(--color-text-muted)]">
                {data.solution_json.explanation}
              </p>
              {(data.solution_json.code ||
                data.solution_json.python ||
                data.solution_json.javascript) && (
                <pre className="overflow-x-auto rounded-md bg-[var(--color-surface-muted)] p-3 font-mono text-xs">
                  {data.solution_json.code ||
                    data.solution_json.python ||
                    data.solution_json.javascript}
                </pre>
              )}
            </>
          ) : (
            <p className="text-[var(--color-text-muted)]">
              Solution unlocks after you complete this lesson (policy: after completion). No AI-generated answers.
            </p>
          )}
        </div>
      )}

      {tab === 'hints' && (
        <div className="space-y-3 text-sm">
          {visibleHints.map((hint) => (
            <div key={hint.id} className="rounded-md border border-[var(--color-border)] p-3">
              {hint.hint_text}
            </div>
          ))}
          {hintIndex < data.hints.length ? (
            <Button variant="secondary" onClick={() => setHintIndex((n) => n + 1)}>
              Reveal next hint ({hintIndex + 1}/{data.hints.length})
            </Button>
          ) : data.hints.length === 0 ? (
            <p className="text-[var(--color-text-muted)]">No hints for this lesson.</p>
          ) : (
            <p className="text-xs text-[var(--color-text-muted)]">All hints revealed.</p>
          )}
        </div>
      )}

      {tab === 'help' && (
        <div className="space-y-4 text-sm">
          <p className="text-[var(--color-text-muted)]">
            Help is curated FAQ and resources — not an AI chatbot.
          </p>
          {data.doubts.map((d) => (
            <div key={d.id} className="rounded-md border border-[var(--color-border)] p-3">
              <p className="font-medium">{d.question}</p>
              <p className="mt-1 text-[var(--color-text-muted)]">{d.answer}</p>
            </div>
          ))}
          {data.resources.map((r) => (
            <a
              key={r.id}
              href={r.url}
              target="_blank"
              rel="noreferrer"
              className="block text-[var(--color-accent)] hover:underline"
            >
              {r.title}
            </a>
          ))}
          <div className="space-y-2 border-t border-[var(--color-border)] pt-3">
            <p className="font-medium">Was this lesson helpful?</p>
            <div className="flex flex-wrap gap-2">
              <Button
                variant="secondary"
                onClick={() => feedbackMutation.mutate({ vote: 'helpful' })}
              >
                Yes
              </Button>
              <Button
                variant="ghost"
                onClick={() => feedbackMutation.mutate({ vote: 'not_helpful' })}
              >
                Needs work
              </Button>
              <Button
                variant="ghost"
                onClick={() => feedbackMutation.mutate({ report_issue: true, note: feedbackNote || 'Issue reported' })}
              >
                Report issue
              </Button>
            </div>
            <textarea
              className="w-full rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] p-2 text-sm"
              rows={2}
              placeholder="Optional note"
              value={feedbackNote}
              onChange={(e) => setFeedbackNote(e.target.value)}
            />
          </div>
        </div>
      )}
    </>
  )

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <Link
            to={`/learn/courses/${courseSlug}`}
            className="text-xs text-[var(--color-accent)] hover:underline"
          >
            ← {courseSlug}
          </Link>
          <h2 className="mt-1 text-lg font-semibold text-[var(--color-text)]">{data.title}</h2>
          <div className="mt-1 flex flex-wrap gap-2">
            <Badge>{data.lesson_type}</Badge>
            <Badge>{data.status}</Badge>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          {data.prev_href && (
            <Link to={data.prev_href}>
              <Button variant="ghost">Previous</Button>
            </Link>
          )}
          {data.can_mark_complete && data.status !== 'completed' && (
            <Button
              variant="primary"
              onClick={() => completeMutation.mutate()}
              disabled={completeMutation.isPending}
            >
              Mark complete
            </Button>
          )}
          {data.next_href && (
            <Link to={data.next_href}>
              <Button variant="secondary">Next</Button>
            </Link>
          )}
        </div>
      </div>

      {message && <p className="text-sm text-[var(--color-accent)]">{message}</p>}

      <div className="grid gap-4 lg:grid-cols-[220px_1fr]">
        <aside className="hidden space-y-1 lg:block">
          <p className="mb-2 text-xs font-medium uppercase text-[var(--color-text-subtle)]">Progress</p>
          {data.progress_blocks.map((item) => {
            const href = `/learn/courses/${courseSlug}/${item.module_slug}/${item.slug}`
            const active = item.slug === lessonSlug && item.module_slug === moduleSlug
            return (
              <Link
                key={item.id}
                to={item.status === 'locked' ? '#' : href}
                className={`block rounded-md px-2 py-1.5 text-xs ${
                  active
                    ? 'bg-[var(--color-accent-muted)] text-[var(--color-accent)]'
                    : item.status === 'locked'
                      ? 'pointer-events-none text-[var(--color-text-subtle)]'
                      : 'text-[var(--color-text-muted)] hover:bg-[var(--color-surface-muted)]'
                }`}
                onClick={(e) => item.status === 'locked' && e.preventDefault()}
              >
                {item.title}
              </Link>
            )
          })}
        </aside>

        <Card className="min-h-[420px]">
          <div className="mb-4 flex gap-1 overflow-x-auto border-b border-[var(--color-border)] pb-2">
            {tabs.map((t) => (
              <button
                key={t}
                type="button"
                className={`whitespace-nowrap rounded-md px-3 py-1.5 text-xs ${
                  tab === t
                    ? 'bg-[var(--color-accent-muted)] text-[var(--color-accent)]'
                    : 'text-[var(--color-text-muted)]'
                }`}
                onClick={() => setTab(t)}
              >
                {TAB_LABELS[t]}
              </button>
            ))}
          </div>
          {panel}
        </Card>
      </div>
    </div>
  )
}
