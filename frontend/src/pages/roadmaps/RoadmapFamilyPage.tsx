import { Link, useParams } from 'react-router-dom'

import { OfficialRoadmapView } from '@/features/roadmap-official/OfficialRoadmapView'

export function RoadmapFamilyPage() {
  const { familySlug = '' } = useParams()

  if (!familySlug) {
    return (
      <div className="module-page">
        <p role="alert">Missing roadmap id.</p>
        <Link to="/roadmaps">Back to roadmaps</Link>
      </div>
    )
  }

  return <OfficialRoadmapView slug={familySlug} />
}
