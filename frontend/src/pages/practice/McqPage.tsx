import { Link } from 'react-router-dom'

import { PracticeTrackNav } from '@/components/practice/PracticeTrackNav'
import { PracticeCatalog } from '@/features/practice/PracticeCatalog'

export function McqPage() {
  return (
    <div className="module-page">
      <PracticeTrackNav />
      <PracticeCatalog
        title="Subject quizzes"
        description="Choose a subject, then a topic. Multiple choice is the question format, not a separate track."
        formatLabel="Multiple choice"
        domainSlug="technical"
      />
      <nav className="flex flex-wrap gap-3 px-4 pb-4 text-sm" aria-label="Published family quizzes">
        <Link to="/learn/quizzes/pack-data-analyst" className="text-[var(--color-accent)] hover:underline">Data Analyst</Link>
        <Link to="/learn/quizzes/pack-data-engineer" className="text-[var(--color-accent)] hover:underline">Data Engineer</Link>
        <Link to="/learn/quizzes/pack-python-dev" className="text-[var(--color-accent)] hover:underline">Python</Link>
        <Link to="/learn/quizzes/pack-java-backend" className="text-[var(--color-accent)] hover:underline">Java</Link>
        <Link to="/learn/quizzes/pack-frontend-react" className="text-[var(--color-accent)] hover:underline">React</Link>
        <Link to="/learn/quizzes/pack-fullstack-web" className="text-[var(--color-accent)] hover:underline">Full stack</Link>
      </nav>
    </div>
  )
}
