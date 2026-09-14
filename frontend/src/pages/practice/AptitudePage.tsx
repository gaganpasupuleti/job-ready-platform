import { PracticeTrackNav } from '@/components/practice/PracticeTrackNav'
import { PracticeCatalog } from '@/features/practice/PracticeCatalog'

export function AptitudePage() {
  return (
    <div className="module-page">
      <PracticeTrackNav />
      <PracticeCatalog
        title="Aptitude & Reasoning"
        description="Quantitative aptitude, logical reasoning, verbal ability, and data interpretation."
        formatLabel="Multiple choice"
        domainSlug="placement"
        categorySlug="aptitude"
      />
    </div>
  )
}
