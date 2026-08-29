import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { SUPPORTED_LANGUAGES } from '@/constants/languages'
import {
  CodingProblemList,
  CodingProgressSummary,
} from '@/features/dsa/CodingProblemList'
import { fetchCodingProblems, fetchCodingProgress } from '@/services/codingService'

export function CodingPage() {
  const [languageId, setLanguageId] = useState<number>(71)

  const { data: progress } = useQuery({
    queryKey: ['coding-progress'],
    queryFn: fetchCodingProgress,
  })

  const { data: problems, isLoading } = useQuery({
    queryKey: ['coding-problems-by-lang', languageId],
    queryFn: () => fetchCodingProblems({ language_id: languageId }),
  })

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-[var(--color-text)]">Coding Practice</h2>
        <p className="text-sm text-[var(--color-text-muted)]">
          Language-focused practice using the same coding engine as DSA. Pick a language to filter
          problems with starter templates.
        </p>
      </div>

      {progress && <CodingProgressSummary progress={progress} />}

      <div className="flex flex-wrap gap-2">
        {SUPPORTED_LANGUAGES.map((lang) => (
          <button
            key={lang.id}
            type="button"
            onClick={() => setLanguageId(lang.id)}
            className={`rounded-md border px-3 py-1.5 text-sm ${
              languageId === lang.id
                ? 'border-[var(--color-accent)] bg-[var(--color-accent-muted)] text-[var(--color-accent)]'
                : 'border-[var(--color-border)] bg-[var(--color-surface)]'
            }`}
          >
            {lang.shortLabel}
          </button>
        ))}
      </div>

      <CodingProblemList
        problems={problems?.items ?? []}
        total={problems?.total ?? 0}
        isLoading={isLoading}
        problemLinkPrefix="/practice/dsa"
      />

      <p className="text-xs text-[var(--color-text-muted)]">
        Problems open in the shared workspace at{' '}
        <Link to="/practice/dsa" className="text-[var(--color-accent)] hover:underline">
          DSA Practice
        </Link>
        .
      </p>
    </div>
  )
}
