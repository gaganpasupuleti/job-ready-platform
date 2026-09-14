import { PracticeTrackNav } from '@/components/practice/PracticeTrackNav'
import { PracticeCatalog } from '@/features/practice/PracticeCatalog'

export function AptitudePage() {
  return (
    <div className="module-page">
      <PracticeTrackNav />
      <PracticeCatalog
        title="Aptitude / CRT Practice"
        description="Quantitative aptitude, logical reasoning, verbal ability, and data interpretation."
        domainSlug="placement"
        categorySlug="aptitude"
      />
    </div>
  )
}
