import { Navigate } from 'react-router-dom'

/** Legacy dev URL — student roadmaps live at `/roadmaps/:familySlug`. */
export function RoadmapPreviewPage() {
  return <Navigate to="/roadmaps/data-engineer" replace />
}
