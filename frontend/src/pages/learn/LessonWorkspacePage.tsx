import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { Card } from '@/components/common/Card'
import {
  apiErrorMessage,
  EmptyState,
  ErrorState,
  LoadingState,
  PracticeProgress,
  PracticeStatusBadge,
  WorkspaceSplit,
} from '@/components/practice-workspace/PracticeWorkspace'
import { CodeEditor } from '@/features/dsa/CodeEditor'
import {
  completeLesson,
  fetchLesson,
  recordLessonAttempt,
  sendLessonFeedback,
  startLesson,
} from '@/services/learnService'

type WorkspaceTab = 'statement' | 'editor' | 'submissions' | 'solution' | 'hints' | 'help'

const LANG_MONACO: Record<string, string> = {
  python: 'python',
  java: 'java',
  cpp: 'cpp',
  cplusplus: 'cpp',
  javascript: 'javascript',
  js: 'javascript',
}

function starterLanguage(starter: Record<string, string>, courseLang?: string | null) {
  const keys = Object.keys(starter || {})
  if (courseLang && starter[courseLang]) return courseLang
  if (courseLang && LANG_MONACO[courseLang] && keys.includes(courseLang)) return courseLang
  if (keys.length === 1) return keys[0]
  return keys.includes('python') ? 'python' : keys[0] ?? 'python'
}

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
  const [languageKey, setLanguageKey] = useState('python')
  const [outlineOpen, setOutlineOpen] = useState(false)
  const [mobileTab, setMobileTab] = useState<'problem' | 'code' | 'output'>('problem')
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
    const lang = starterLanguage(data.starter_code ?? {}, data.primary_language_key)
    setLanguageKey(lang)
    const starter =
      data.starter_code?.[lang] ??
      data.starter_code?.python ??
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
        language: languageKey,
        is_correct: false,
        note: 'Practice attempt saved (execution unavailable)',
      }),
    onSuccess: () => {
      setLocalAttempts((prev) => [
        {
          at: new Date().toISOString(),
          note: 'Practice attempt saved',
          codeSnippet: code.slice(0, 120),
        },
        ...prev,
      ])
      setMessage('Practice attempt saved. This does not mark the solution as passed.')
      setTab('submissions')
    },
    onError: (err) => setMessage(apiErrorMessage(err, 'Could not save attempt.')),
  })

  const feedbackMutation = useMutation({
    mutationFn: (payload: { vote?: string; report_issue?: boolean; note?: string }) =>
      sendLessonFeedback(data!.id, payload),
    onSuccess: () => setMessage('Thanks for the feedback.'),
    onError: (err) => setMessage(apiErrorMessage(err, 'Could not send feedback.')),
  })

  const tabs = useMemo(() => {
    const base: WorkspaceTab[] = ['statement']
    if (data?.lesson_type === 'interactive_code' || data?.lesson_type === 'practice') {
      base.push('editor', 'submissions')
    }
    base.push('solution', 'hints', 'help')
    return base
  }, [data?.lesson_type])

  if (isLoading) return <LoadingState label="Loading lesson" />

  if (error || !data) {
    return (
      <Card>
        <ErrorState message="Lesson unavailable or locked. Complete previous lessons first." />
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
            <CodeEditor
              value={code}
              language={LANG_MONACO[languageKey] ?? 'python'}
              onChange={setCode}
              height="360px"
            />
          </div>
          <p className="text-xs text-[var(--color-text-muted)]">
            Execution is currently unavailable. Saving an attempt stores your code and language without pretending it passed.
          </p>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="secondary"
              onClick={() => attemptMutation.mutate()}
              disabled={attemptMutation.isPending}
            >
              {attemptMutation.isPending ? 'Saving...' : 'Save Practice Attempt'}
            </Button>
            {data.coding_problem_id && (
              <Link to={`/practice/dsa/${data.coding_problem_id}`}>
                <Button variant="ghost">Open Graded Challenge</Button>
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
            <EmptyState title="No attempts yet" description="Save a practice attempt from the editor." />
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
          <p className="text-sm text-[var(--color-text-muted)]">
            {data.course_title ?? courseSlug}
            {data.module_title ? ` · ${data.module_title}` : ''}
            {data.lesson_index && data.lesson_total ? ` · Lesson ${data.lesson_index} of ${data.lesson_total}` : ''}
          </p>
          <div className="mt-2 max-w-sm">
            <PracticeProgress percent={data.course_percent ?? 0} label={`${data.course_percent ?? 0}%`} />
          </div>
          <div className="mt-1 flex flex-wrap gap-2">
            <Badge>{data.lesson_type}</Badge>
            <PracticeStatusBadge status={data.status} />
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="ghost" className="lg:hidden" onClick={() => setOutlineOpen(true)}>
            Course outline
          </Button>
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

      {outlineOpen && (
        <div className="fixed inset-0 z-40 bg-black/40 p-4 lg:hidden" role="dialog" aria-label="Course outline">
          <div className="max-h-[80vh] overflow-auto rounded-md bg-[var(--color-surface)] p-4">
            <Button variant="ghost" size="sm" onClick={() => setOutlineOpen(false)}>
              Close
            </Button>
            {data.progress_blocks.map((item) => (
              <Link
                key={item.id}
                to={`/learn/courses/${courseSlug}/${item.module_slug}/${item.slug}`}
                className="mt-2 block text-sm"
                onClick={() => setOutlineOpen(false)}
              >
                {item.title}
              </Link>
            ))}
          </div>
        </div>
      )}

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
                {item.status === 'completed' ? '✓ ' : item.status === 'locked' ? '🔒 ' : active ? '● ' : '○ '}
                {item.title}
              </Link>
            )
          })}
        </aside>

        {data.lesson_type === 'interactive_code' || data.lesson_type === 'practice' ? (
          <div className="min-h-[32rem]">
            <WorkspaceSplit
              storageKey="learn-split"
              left={
                <Card className="h-full overflow-auto" padding="md">
                  <div className="mb-3 flex gap-1 overflow-x-auto">
                    {tabs.filter((t) => t !== 'editor').map((t) => (
                      <button key={t} type="button" className="px-2 py-1 text-xs" onClick={() => setTab(t)}>
                        {TAB_LABELS[t]}
                      </button>
                    ))}
                  </div>
                  {tab === 'editor' ? <StatementBlocks blocks={data.statement_json?.blocks} /> : panel}
                </Card>
              }
              right={
                <Card className="h-full overflow-hidden p-0">
                  <CodeEditor
                    value={code}
                    language={LANG_MONACO[languageKey] ?? 'python'}
                    onChange={setCode}
                    height="100%"
                  />
                </Card>
              }
              bottom={
                <Card padding="md">
                  <Button onClick={() => attemptMutation.mutate()} disabled={attemptMutation.isPending}>
                    {attemptMutation.isPending ? 'Saving...' : 'Save Practice Attempt'}
                  </Button>
                </Card>
              }
              mobileTab={mobileTab}
              onMobileTab={setMobileTab}
            />
          </div>
        ) : (
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
        )}
      </div>
    </div>
  )
}
