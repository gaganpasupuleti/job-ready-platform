import type { FormEvent } from 'react'
import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'

import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
import { PracticeHeader } from '@/components/practice-workspace/PracticeWorkspace'
import { createInterviewSession } from '@/services/interviewService'
import type {
  ExperienceLevel,
  InterviewQuestionType,
  InterviewSessionMode,
  InterviewSessionSource,
} from '@/types/interview'

export function InterviewSessionNewPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const questionIdsParam = searchParams.get('question_ids')

  const [mode, setMode] = useState<InterviewSessionMode>('study')
  const [sourceType, setSourceType] = useState<InterviewSessionSource>(
    questionIdsParam ? 'custom_filter' : 'custom_filter',
  )
  const [packSlug, setPackSlug] = useState('')
  const [questionCount, setQuestionCount] = useState(10)
  const [role, setRole] = useState('')
  const [skill, setSkill] = useState('')
  const [company, setCompany] = useState('')
  const [difficulty, setDifficulty] = useState('')
  const [experienceLevel, setExperienceLevel] = useState('')
  const [questionType, setQuestionType] = useState('')

  const startMutation = useMutation({
    mutationFn: createInterviewSession,
    onSuccess: (detail) => navigate(`/interviews/sessions/${detail.session.id}`),
  })

  const onSubmit = (e: FormEvent) => {
    e.preventDefault()
    const questionIds = questionIdsParam
      ? questionIdsParam.split(',').map((id) => id.trim()).filter(Boolean)
      : undefined

    startMutation.mutate({
      mode,
      source_type: packSlug ? 'pack' : sourceType,
      pack_slug: packSlug || undefined,
      question_count: questionCount,
      role: role || undefined,
      skill: skill || undefined,
      company: company || undefined,
      difficulty: difficulty || undefined,
      experience_level: (experienceLevel || undefined) as ExperienceLevel | undefined,
      question_type: (questionType || undefined) as InterviewQuestionType | undefined,
      question_ids: questionIds,
    })
  }

  const inputClass =
    'mt-1 w-full rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)]'

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <PracticeHeader backTo="/interviews" backLabel="Interview hub" title="New interview session">
        <p className="text-sm text-[var(--color-text-muted)]">
          Filter questions or start from a pack. Self-review only — no LLM scoring.
        </p>
      </PracticeHeader>

      <Card>
        <CardHeader title="Session setup" />
        <form className="space-y-4" onSubmit={onSubmit}>
          <fieldset className="space-y-2">
            <legend className="text-sm font-medium text-[var(--color-text)]">Mode</legend>
            <div className="flex flex-wrap gap-3">
              {(
                [
                  ['study', 'Study'],
                  ['mock', 'Mock'],
                  ['rapid_review', 'Rapid review'],
                ] as const
              ).map(([value, label]) => (
                <label
                  key={value}
                  htmlFor={`mode-${value}`}
                  className="flex items-center gap-2 text-sm text-[var(--color-text)]"
                >
                  <input
                    id={`mode-${value}`}
                    type="radio"
                    name="session-mode"
                    checked={mode === value}
                    onChange={() => setMode(value)}
                  />
                  {label}
                </label>
              ))}
            </div>
          </fieldset>

          <label className="block text-xs text-[var(--color-text-muted)]" htmlFor="pack-slug">
            Pack slug (optional)
            <input
              id="pack-slug"
              value={packSlug}
              onChange={(e) => {
                setPackSlug(e.target.value)
                setSourceType(e.target.value ? 'pack' : 'custom_filter')
              }}
              className={inputClass}
              placeholder="leave empty for custom filters"
            />
          </label>

          <label className="block text-xs text-[var(--color-text-muted)]" htmlFor="question-count">
            Question count
            <input
              id="question-count"
              type="number"
              min={1}
              max={50}
              value={questionCount}
              onChange={(e) => setQuestionCount(Number(e.target.value) || 10)}
              className={inputClass}
            />
          </label>

          <div className="grid gap-3 sm:grid-cols-2">
            <label className="block text-xs text-[var(--color-text-muted)]" htmlFor="new-role">
              Role
              <input id="new-role" value={role} onChange={(e) => setRole(e.target.value)} className={inputClass} />
            </label>
            <label className="block text-xs text-[var(--color-text-muted)]" htmlFor="new-skill">
              Skill
              <input id="new-skill" value={skill} onChange={(e) => setSkill(e.target.value)} className={inputClass} />
            </label>
            <label className="block text-xs text-[var(--color-text-muted)]" htmlFor="new-company">
              Company
              <input
                id="new-company"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                className={inputClass}
              />
            </label>
            <label className="block text-xs text-[var(--color-text-muted)]" htmlFor="new-difficulty">
              Difficulty
              <select
                id="new-difficulty"
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value)}
                className={inputClass}
              >
                <option value="">Any</option>
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </select>
            </label>
            <label className="block text-xs text-[var(--color-text-muted)]" htmlFor="new-exp">
              Experience level
              <select
                id="new-exp"
                value={experienceLevel}
                onChange={(e) => setExperienceLevel(e.target.value)}
                className={inputClass}
              >
                <option value="">Any</option>
                <option value="fresher">Fresher</option>
                <option value="junior">Junior</option>
                <option value="intermediate">Intermediate</option>
                <option value="senior">Senior</option>
              </select>
            </label>
            <label className="block text-xs text-[var(--color-text-muted)]" htmlFor="new-type">
              Question type
              <select
                id="new-type"
                value={questionType}
                onChange={(e) => setQuestionType(e.target.value)}
                className={inputClass}
              >
                <option value="">Any</option>
                <option value="technical">Technical</option>
                <option value="hr">HR</option>
                <option value="behavioral">Behavioral</option>
                <option value="scenario">Scenario</option>
                <option value="conceptual">Conceptual</option>
              </select>
            </label>
          </div>

          {questionIdsParam && (
            <p className="text-xs text-[var(--color-text-muted)]">
              Starting with selected question id(s): {questionIdsParam}
            </p>
          )}

          {startMutation.isError && (
            <p className="text-sm text-red-700 dark:text-red-300">Could not create session.</p>
          )}

          <Button type="submit" variant="primary" disabled={startMutation.isPending}>
            {startMutation.isPending ? 'Starting…' : 'Start session'}
          </Button>
        </form>
      </Card>
    </div>
  )
}
