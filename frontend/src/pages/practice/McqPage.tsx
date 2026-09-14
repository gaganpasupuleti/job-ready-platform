import { Link } from 'react-router-dom'

import { PracticeCatalog } from '@/features/practice/PracticeCatalog'

export function McqPage() {
  return (
    <>
      <PracticeCatalog
        title="Technical MCQs"
        description="Core computer science, programming, cloud, AI, and cybersecurity fundamentals."
        domainSlug="technical"
      />
      <nav className="flex flex-wrap gap-3 px-4 pb-4 text-sm" aria-label="Published family quizzes">
        <Link to="/learn/quizzes/pack-data-analyst" className="text-[var(--color-accent)]">Data Analyst quiz</Link>
        <Link to="/learn/quizzes/pack-data-engineer" className="text-[var(--color-accent)]">Data Engineer quiz</Link>
        <Link to="/learn/quizzes/pack-python-dev" className="text-[var(--color-accent)]">Python quiz</Link>
      </nav>
    </>
  )
}
