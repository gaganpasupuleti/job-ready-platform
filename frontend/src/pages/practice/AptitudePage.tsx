import { Link } from 'react-router-dom'

import { PracticeCatalog } from '@/features/practice/PracticeCatalog'

export function AptitudePage() {
  return (
    <>
      <PracticeCatalog
        title="Aptitude / CRT Practice"
        description="Quantitative aptitude, logical reasoning, verbal ability, and data interpretation. CRT is shared practice, not a job family."
        domainSlug="placement"
        categorySlug="aptitude"
      />
      <p className="px-4 pb-4 text-sm">
        <Link to="/learn/quizzes/pack-crt-shared" className="text-[var(--color-accent)]">
          Open the published CRT pack
        </Link>
      </p>
    </>
  )
}
