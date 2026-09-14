import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { PracticeTrackNav } from '@/components/practice/PracticeTrackNav'
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
    <div className="module-page space-y-4">
      <PracticeTrackNav />
      <div>
        <h1 className="text-base font-semibold text-[var(--color-text)] sm:text-lg">Coding Practice</h1>
        <p className="mt-0.5 text-sm text-[var(--color-text-muted)]">
          Language-focused practice using the same coding engine as DSA. Pick a language to filter
          problems with starter templates.
        </p>
      </div>

      {progress && <CodingProgressSummary progress={progress} />}

      <div className="flex flex-wrap gap-1.5" role="group" aria-label="Language filter">
        {SUPPORTED_LANGUAGES.map((lang) => (
          <button
            key={lang.id}
            type="button"
            onClick={() => setLanguageId(lang.id)}
            aria-pressed={languageId === lang.id}
            className={`h-7 rounded-[var(--radius-control)] border px-2.5 text-xs ${
              languageId === lang.id
                ? 'border-[var(--color-accent)] bg-[var(--color-accent-muted)] text-[var(--color-accent)]'
                : 'border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text-muted)] hover:text-[var(--color-text)]'
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
        Freeform Python (not graded):{' '}
        <Link to="/practice/python" className="text-[var(--color-accent)] hover:underline">
          Python Playground
        </Link>
        . Assessed problems open in the shared workspace at{' '}
        <Link to="/practice/dsa" className="text-[var(--color-accent)] hover:underline">
          DSA Practice
        </Link>
        .
      </p>
    </div>
  )
}
