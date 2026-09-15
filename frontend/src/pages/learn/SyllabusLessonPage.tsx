import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { Button } from '@/components/common/Button'
import { LearnSubnav } from '@/components/learn/LearnSubnav'
import { SafeMarkdown } from '@/components/learn/SafeMarkdown'
import {
  checkSyllabusPractice,
  fetchSyllabusLesson,
  markMaterialRead,
} from '@/services/studioService'

export function SyllabusLessonPage() {
  const { key = '' } = useParams()
  const queryClient = useQueryClient()
  const { data, isLoading, isError } = useQuery({
    queryKey: ['studio-syllabus-lesson', key],
    queryFn: () => fetchSyllabusLesson(key),
    enabled: Boolean(key),
  })
  const [answers, setAnswers] = useState<Record<string, string[]>>({})
  const [revealed, setRevealed] = useState<Record<string, Awaited<ReturnType<typeof checkSyllabusPractice>>>>({})

  const readMutation = useMutation({
    mutationFn: () => markMaterialRead(data!.material_key!),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['studio-syllabus-lesson', key] }),
  })

  const practiceMutation = useMutation({
    mutationFn: ({ questionKey, selected }: { questionKey: string; selected: string[] }) =>
      checkSyllabusPractice(key, questionKey, selected),
    onSuccess: (result, variables) => {
      setRevealed((current) => ({ ...current, [variables.questionKey]: result }))
    },
  })

  return (
    <div className="module-page learn-page">
      <LearnSubnav />
      {isLoading ? (
        <p>Loading lesson...</p>
      ) : isError || !data ? (
        <p role="alert">Unable to load this lesson.</p>
      ) : data.status !== 'published' || !data.material ? (
        <div className="rounded-[5px] border border-[var(--color-border)] p-4">
          <h1>{data.title}</h1>
          <p role="status" className="mt-2 text-sm">
            Coming soon. This topic is on the syllabus, but the article is not published yet.
          </p>
          <Link to="/learn/syllabus" className="mt-3 inline-block text-sm text-[var(--color-accent)]">
            Back to syllabus
          </Link>
        </div>
      ) : (
        <>
          <header className="module-heading">
            <div>
              <p className="eyebrow">
                {data.track_title} · {data.unit_title} · lesson {data.syllabus_position} of{' '}
                {data.syllabus_total}
                {data.minutes ? ` · ${data.minutes} min` : ''}
              </p>
              <h1>{data.title}</h1>
              <p>{data.material.summary}</p>
            </div>
          </header>
          <section className="mt-4">
            <h2 className="text-sm font-semibold">Prerequisites</h2>
            {data.prerequisites.length === 0 ? (
              <p className="text-sm text-[var(--color-text-muted)]">None.</p>
            ) : (
              <ul className="list-disc pl-5 text-sm">
                {data.prerequisites.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            )}
          </section>
          <section className="mt-4">
            <h2 className="text-sm font-semibold">Learning objectives</h2>
            <ul className="list-disc pl-5 text-sm">
              {data.material.objectives.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>
          <div className="mt-4 min-w-0 rounded-[5px] border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
            <SafeMarkdown source={data.material.body_md} />
          </div>
          {data.material.examples.length > 0 && (
            <section className="mt-4">
              <h2 className="text-sm font-semibold">Examples</h2>
              {data.material.examples.map((item) => (
                <pre key={item} className="mt-2 overflow-x-auto rounded bg-[var(--color-surface-muted)] p-3 text-xs">
                  {item}
                </pre>
              ))}
            </section>
          )}
          <section className="mt-4">
            <h2 className="text-sm font-semibold">Recap</h2>
            <SafeMarkdown source={data.material.summary_md || data.material.summary} />
          </section>
          {data.video && (
            <p className="mt-3 text-sm">
              Optional video ({data.video.channel}):{' '}
              <a href={data.video.url} className="text-[var(--color-accent)]" rel="noreferrer" target="_blank">
                {data.video.topic}
              </a>
            </p>
          )}
          <section className="mt-6">
            <h2 className="text-sm font-semibold">Related practice</h2>
            <p className="text-xs text-[var(--color-text-muted)]">
              Explanations appear after you answer. This is reading practice, not assessed competence.
            </p>
            <div className="mt-3 space-y-4">
              {data.practice.map((question) => {
                const selected = answers[question.key] ?? []
                const result = revealed[question.key]
                return (
                  <div key={question.key} className="rounded-[5px] border border-[var(--color-border)] p-3">
                    <p className="text-sm font-medium">{question.stem}</p>
                    <ul className="mt-2 space-y-1">
                      {question.options.map((option) => (
                        <li key={option.key}>
                          <label className="flex items-start gap-2 text-sm">
                            <input
                              type="radio"
                              name={question.key}
                              checked={selected[0] === option.key}
                              onChange={() =>
                                setAnswers((current) => ({ ...current, [question.key]: [option.key] }))
                              }
                            />
                            <span>{option.text}</span>
                          </label>
                        </li>
                      ))}
                    </ul>
                    <Button
                      className="mt-2"
                      variant="secondary"
                      disabled={!selected.length || practiceMutation.isPending}
                      onClick={() =>
                        practiceMutation.mutate({ questionKey: question.key, selected })
                      }
                    >
                      Check answer
                    </Button>
                    {result && (
                      <div className="mt-2 text-sm">
                        <p role="status">{result.correct ? 'Correct' : 'Not quite'}</p>
                        <p className="mt-1">{result.explanation}</p>
                        <p className="mt-1 text-xs text-[var(--color-text-muted)]">{result.note}</p>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </section>
          <div className="mt-4 flex flex-wrap gap-2">
            <Button
              variant="secondary"
              onClick={() => readMutation.mutate()}
              disabled={!data.material_key || readMutation.isPending}
            >
              Mark as read
            </Button>
          </div>
          <p className="mt-2 text-xs text-[var(--color-text-muted)]">
            Mark as read tracks reading progress only, not assessed competence.
          </p>
          <nav className="mt-6 flex flex-wrap justify-between gap-3 text-sm" aria-label="Lesson">
            {data.previous ? (
              <Link to={data.previous.href} className="text-[var(--color-accent)] hover:underline">
                Previous: {data.previous.title}
              </Link>
            ) : (
              <span />
            )}
            {data.next ? (
              <Link to={data.next.href} className="text-[var(--color-accent)] hover:underline">
                Next: {data.next.title}
              </Link>
            ) : (
              <span />
            )}
          </nav>
        </>
      )}
    </div>
  )
}
