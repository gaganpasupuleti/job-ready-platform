import { Link } from 'react-router-dom'

import { PracticeTrackNav } from '@/components/practice/PracticeTrackNav'
import { PracticeCatalog } from '@/features/practice/PracticeCatalog'

export function AptitudePage() {
  return (
    <div className="module-page">
      <PracticeTrackNav />
      <PracticeCatalog
        title="Aptitude & Reasoning"
        description="Quantitative aptitude, logical reasoning, verbal ability, and data interpretation. CRT is shared practice, not a job family."
        formatLabel="Multiple choice"
        domainSlug="placement"
        categorySlug="aptitude"
      />
      <nav className="space-y-2 px-4 pb-4 text-sm" aria-label="Published CRT packs">
        <p className="text-xs font-medium text-[var(--color-text-muted)]">Published packs</p>
        <div className="flex flex-wrap gap-3">
        <Link to="/learn/quizzes/pack-crt-shared" className="text-[var(--color-accent)] hover:underline">
          CRT pack, week 1
        </Link>
        <Link to="/learn/quizzes/pack-crt-2026-09-14" className="text-[var(--color-accent)] hover:underline">
          CRT pack, 14 Sep
        </Link>
        </div>
      </nav>
    </div>
  )
}
