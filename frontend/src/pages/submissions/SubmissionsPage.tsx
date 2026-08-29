import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Card, CardHeader } from '@/components/common/Card'
import { SUPPORTED_LANGUAGES } from '@/constants/languages'
import { fetchSubmissions } from '@/services/codingService'
import type { SubmissionStatus } from '@/types/coding'

export function SubmissionsPage() {
  const [status, setStatus] = useState('')
  const [languageId, setLanguageId] = useState('')
  const [difficulty, setDifficulty] = useState('')
  const [search, setSearch] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['all-submissions', status, languageId, difficulty, search],
    queryFn: () =>
      fetchSubmissions({
        status: (status as SubmissionStatus) || undefined,
        language_id: languageId ? Number(languageId) : undefined,
        difficulty: difficulty || undefined,
        search: search || undefined,
        limit: 50,
      }),
  })

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-[var(--color-text)]">Submission History</h2>
        <p className="text-sm text-[var(--color-text-muted)]">
          Review your coding runs and submits across all problems.
        </p>
      </div>

      <Card padding="md">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <input
            type="search"
            placeholder="Search by problem title"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm"
          />
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm"
          >
            <option value="">All statuses</option>
            <option value="accepted">Accepted</option>
            <option value="wrong_answer">Wrong Answer</option>
            <option value="compilation_error">Compilation Error</option>
            <option value="runtime_error">Runtime Error</option>
            <option value="time_limit_exceeded">Time Limit Exceeded</option>
          </select>
          <select
            value={languageId}
            onChange={(e) => setLanguageId(e.target.value)}
            className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm"
          >
            <option value="">All languages</option>
            {SUPPORTED_LANGUAGES.map((lang) => (
              <option key={lang.id} value={lang.id}>
                {lang.name}
              </option>
            ))}
          </select>
          <select
            value={difficulty}
            onChange={(e) => setDifficulty(e.target.value)}
            className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm"
          >
            <option value="">All difficulties</option>
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </select>
        </div>
      </Card>

      <Card>
        <CardHeader title={`Submissions (${data?.total ?? 0})`} />
        {isLoading ? (
          <p className="text-sm text-[var(--color-text-muted)]">Loading...</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs text-[var(--color-text-subtle)]">
                <tr>
                  <th className="pb-2">Status</th>
                  <th className="pb-2">Problem</th>
                  <th className="pb-2">Difficulty</th>
                  <th className="pb-2">Language</th>
                  <th className="pb-2">Tests</th>
                  <th className="pb-2">Runtime</th>
                  <th className="pb-2">Submitted</th>
                </tr>
              </thead>
              <tbody>
                {data?.items.map((sub) => (
                  <tr key={sub.id} className="border-t border-[var(--color-border)]">
                    <td className="py-3 pr-3 capitalize">
                      <Link to={`/submissions/${sub.id}`} className="text-[var(--color-accent)]">
                        {sub.status.replace(/_/g, ' ')}
                      </Link>
                    </td>
                    <td className="py-3 pr-3">{sub.problem_title}</td>
                    <td className="py-3 pr-3 capitalize">{sub.problem_difficulty ?? '—'}</td>
                    <td className="py-3 pr-3">{sub.language_name}</td>
                    <td className="py-3 pr-3">
                      {sub.passed_tests}/{sub.total_tests}
                    </td>
                    <td className="py-3 pr-3">
                      {sub.execution_time_ms != null
                        ? `${sub.execution_time_ms.toFixed(0)} ms`
                        : '—'}
                    </td>
                    <td className="py-3 text-xs text-[var(--color-text-muted)]">
                      {new Date(sub.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}
