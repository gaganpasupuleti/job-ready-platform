import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { Card } from '@/components/common/Card'
import {
  ErrorState,
  LoadingState,
  PracticeHeader,
} from '@/components/practice-workspace/PracticeWorkspace'
import { fetchInterviewQuestion, fetchInterviewQuestions } from '@/services/interviewService'

export function InterviewQuestionsPage() {
  const [role, setRole] = useState('')
  const [skill, setSkill] = useState('')
  const [difficulty, setDifficulty] = useState('')
  const [questionType, setQuestionType] = useState('')
  const [openSlug, setOpenSlug] = useState<string | null>(null)

  const filters = useMemo(
    () => ({
      role: role || undefined,
      skill: skill || undefined,
      difficulty: difficulty || undefined,
      question_type: questionType || undefined,
    }),
    [role, skill, difficulty, questionType],
  )

  const { data, isLoading, error } = useQuery({
    queryKey: ['interview-questions', filters],
    queryFn: () => fetchInterviewQuestions(filters),
  })

  const { data: detail, isLoading: detailLoading } = useQuery({
    queryKey: ['interview-question', openSlug],
    queryFn: () => fetchInterviewQuestion(openSlug!),
    enabled: Boolean(openSlug),
  })

  return (
    <div className="space-y-6">
      <PracticeHeader backTo="/interviews" backLabel="Interview hub" title="Interview questions">
        <p className="text-sm text-[var(--color-text-muted)]">
          Browse approved Q&amp;A. For timed practice, start a study or mock session instead.
        </p>
      </PracticeHeader>

      <Card padding="md">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <label className="block text-xs text-[var(--color-text-muted)]" htmlFor="filter-role">
            Role
            <input
              id="filter-role"
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="mt-1 w-full rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)]"
              placeholder="e.g. backend"
            />
          </label>
          <label className="block text-xs text-[var(--color-text-muted)]" htmlFor="filter-skill">
            Skill
            <input
              id="filter-skill"
              value={skill}
              onChange={(e) => setSkill(e.target.value)}
              className="mt-1 w-full rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)]"
              placeholder="e.g. sql"
            />
          </label>
          <label className="block text-xs text-[var(--color-text-muted)]" htmlFor="filter-difficulty">
            Difficulty
            <select
              id="filter-difficulty"
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value)}
              className="mt-1 w-full rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)]"
            >
              <option value="">Any</option>
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>
          </label>
          <label className="block text-xs text-[var(--color-text-muted)]" htmlFor="filter-type">
            Type
            <select
              id="filter-type"
              value={questionType}
              onChange={(e) => setQuestionType(e.target.value)}
              className="mt-1 w-full rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)]"
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
        <div className="mt-3">
          <Link to="/interviews/session/new">
            <Button variant="primary" size="sm">
              Start filtered session
            </Button>
          </Link>
        </div>
      </Card>

      {isLoading && <LoadingState label="Loading questions" />}
      {error && <ErrorState message="Unable to load interview questions." />}

      {!isLoading && !error && (
        <div className="space-y-3">
          {(data?.items ?? []).map((item) => (
            <Card key={item.id} padding="md">
              <button
                type="button"
                className="w-full text-left"
                onClick={() => setOpenSlug(item.slug === openSlug ? null : item.slug)}
                aria-expanded={openSlug === item.slug}
              >
                <p className="font-medium text-[var(--color-text)]">{item.question_text}</p>
                <div className="mt-2 flex flex-wrap gap-1">
                  <Badge>{item.difficulty}</Badge>
                  <Badge>{item.experience_level}</Badge>
                  <Badge>{item.question_type}</Badge>
                  {item.skills.map((s) => (
                    <Badge key={s}>{s}</Badge>
                  ))}
                </div>
              </button>
              {openSlug === item.slug && (
                <div className="mt-4 space-y-3 border-t border-[var(--color-border)] pt-3 text-sm">
                  {detailLoading && (
                    <p className="text-[var(--color-text-muted)]">Loading details…</p>
                  )}
                  {detail && (
                    <>
                      <div>
                        <p className="text-xs font-medium text-[var(--color-text-muted)]">
                          Expected answer (browse only)
                        </p>
                        <p className="mt-1 whitespace-pre-wrap text-[var(--color-text)]">
                          {detail.expected_answer}
                        </p>
                      </div>
                      {detail.key_points.length > 0 && (
                        <ul className="list-disc pl-5 text-[var(--color-text-muted)]">
                          {detail.key_points.map((p) => (
                            <li key={p.id}>{p.point_text}</li>
                          ))}
                        </ul>
                      )}
                      <Link
                        to={`/interviews/session/new?question_ids=${item.id}`}
                        className="inline-block text-[var(--color-accent)] hover:underline"
                      >
                        Practice this in a session
                      </Link>
                    </>
                  )}
                </div>
              )}
            </Card>
          ))}
          {!data?.items.length && (
            <p className="text-sm text-[var(--color-text-muted)]">
              No approved interview questions match these filters.
            </p>
          )}
        </div>
      )}
    </div>
  )
}
