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
      <nav className="flex flex-wrap gap-3 px-4 pb-4 text-sm" aria-label="Published CRT packs">
        <Link to="/learn/quizzes/pack-crt-shared" className="text-[var(--color-accent)] hover:underline">
          CRT pack, week 1
        </Link>
        <Link to="/learn/quizzes/pack-crt-2026-09-14" className="text-[var(--color-accent)] hover:underline">
          CRT pack, 14 Sep
        </Link>
      </nav>
    </div>
  )
}
