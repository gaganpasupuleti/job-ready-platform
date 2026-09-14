import { PracticeTrackNav } from '@/components/practice/PracticeTrackNav'
import { PracticeCatalog } from '@/features/practice/PracticeCatalog'

export function McqPage() {
  return (
    <div className="module-page">
      <PracticeTrackNav />
      <PracticeCatalog
        title="Technical MCQs"
        description="Core computer science, programming, cloud, AI, and cybersecurity fundamentals."
        domainSlug="technical"
      />
    </div>
  )
}
