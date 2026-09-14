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
    </div>
  )
}
