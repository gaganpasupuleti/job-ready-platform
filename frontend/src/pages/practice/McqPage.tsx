import { Link } from 'react-router-dom'

import { PracticeTrackNav } from '@/components/practice/PracticeTrackNav'
import { PracticeCatalog } from '@/features/practice/PracticeCatalog'

export function McqPage() {
  return (
    <div className="module-page">
      <PracticeTrackNav />
      <PracticeCatalog
        title="Technical MCQs"
        description="Choose a subject, then a topic. These are multiple-choice assessments, separate from aptitude."
        formatLabel="Multiple choice"
        domainSlug="technical"
      />
      <nav className="space-y-2 px-4 pb-4 text-sm" aria-label="Published family quizzes">
        <p className="text-xs font-medium text-[var(--color-text-muted)]">Published packs</p>
        <div className="flex flex-wrap gap-3">
        <Link to="/learn/quizzes/pack-data-analyst" className="text-[var(--color-accent)] hover:underline">Data Analyst</Link>
        <Link to="/learn/quizzes/pack-data-engineer" className="text-[var(--color-accent)] hover:underline">Data Engineer</Link>
        <Link to="/learn/quizzes/pack-python-dev" className="text-[var(--color-accent)] hover:underline">Python</Link>
        <Link to="/learn/quizzes/pack-java-backend" className="text-[var(--color-accent)] hover:underline">Java</Link>
        <Link to="/learn/quizzes/pack-frontend-react" className="text-[var(--color-accent)] hover:underline">React</Link>
        <Link to="/learn/quizzes/pack-fullstack-web" className="text-[var(--color-accent)] hover:underline">Full stack</Link>
        </div>
      </nav>
    </div>
  )
}
